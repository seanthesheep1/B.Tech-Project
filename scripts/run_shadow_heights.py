"""Measure obstruction heights from their shadows in the Esri scene.

    make heights

Replaces the six assumed values in ``config.OBSTRUCTION_HEIGHTS_M``, which
between them carry about 85% of the modelled shading loss, with numbers taken
off the imagery the roofs were traced against. The method and its one trick -
recovering the capture time from the shadows' own bearing rather than assuming
it - are set out in ``src/btp_solar/shadows.py``.

Output: ``data/obstruction_heights.csv``, one row per obstruction, plus a
summary by type that the register can adopt.
"""

from __future__ import annotations

import csv
import json
import math
import sqlite3
import statistics
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from btp_solar import basemap, config, shadows  # noqa: E402
from run_fr3_shading import rings_of  # noqa: E402

OBSTRUCTIONS = ROOT / "data" / "obstructions.gpkg"
ROOFS = ROOT / "data" / "roofs.gpkg"
PROVENANCE = ROOT / "data" / "imagery_provenance.json"
OUT = ROOT / "data" / "obstruction_heights.csv"

RADIUS_M = 26.0  # mosaic half-width around each obstruction


def load_roof_rings() -> dict[str, list]:
    """Each candidate roof as a lon/lat ring, for masking the imagery."""
    to_lonlat, _ = basemap.utm_transformers()
    out = {}
    with sqlite3.connect(ROOFS) as conn:
        for bid, geom in conn.execute("select building_id, geom from roofs"):
            out[bid] = [to_lonlat.transform(x, y) for x, y in rings_of(geom)[0]]
    return out


def roof_mask(mosaic, ring_lonlat):
    """Boolean array, true where a pixel lies on this roof."""
    from PIL import Image, ImageDraw

    canvas = Image.new("L", mosaic.image.size, 0)
    pixels = [mosaic.lonlat_to_pixel(lo, la) for lo, la in ring_lonlat]
    ImageDraw.Draw(canvas).polygon(pixels, fill=1)
    return np.asarray(canvas, dtype=bool)


def load() -> list[dict]:
    to_lonlat, _ = basemap.utm_transformers()
    rows = []
    with sqlite3.connect(OBSTRUCTIONS) as conn:
        for fid, bid, kind, geom in conn.execute(
            "select fid, building_id, obstruction_type, geometry from obstructions "
            "order by fid"
        ):
            ring = rings_of(geom)[0]
            lonlat = [to_lonlat.transform(x, y) for x, y in ring]
            rows.append(
                {
                    "fid": fid,
                    "building_id": bid,
                    "type": kind,
                    "lonlat": lonlat,
                    "lon": sum(p[0] for p in lonlat) / len(lonlat),
                    "lat": sum(p[1] for p in lonlat) / len(lonlat),
                }
            )
    return rows


def main() -> int:
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    date_iso = provenance["acquisition_date"]
    print(f"Esri World Imagery, captured {date_iso}, "
          f"{provenance['resolution_m']} m nominal, {provenance['sensor']}")
    print(f"zoom {basemap.DEFAULT_ZOOM}, "
          f"{basemap.metres_per_pixel(config.SITE_LAT, basemap.DEFAULT_ZOOM):.3f} m/pixel\n")

    rows = load()
    roof_rings = load_roof_rings()
    allowed = shadows.northward_bearings()
    print(f"{len(rows)} obstructions on {len(roof_rings)} roofs")
    print("samples are confined to the roof deck: off the roof is tree canopy,")
    print("which is darker than any shadow and would win every time")
    print(f"and to the {len(allowed)} bearings a shadow can physically take today\n")

    # --- pass one: which way do the shadows point? ------------------------
    print("Pass 1 - shadow bearing of each obstruction")
    print(f"{'fid':>4} {'bld':>4} {'type':>12} {'roof':>6} {'lobe':>6} "
          f"{'contrast':>9} {'bearing':>8}  vote")
    for row in rows:
        mosaic = basemap.mosaic_around(row["lon"], row["lat"], RADIUS_M)
        grey = np.asarray(mosaic.image.convert("L"), dtype=float)
        mpp = mosaic.metres_per_pixel(row["lat"])
        centre = mosaic.lonlat_to_pixel(row["lon"], row["lat"])
        pixels = [mosaic.lonlat_to_pixel(lo, la) for lo, la in row["lonlat"]]
        radius = max(math.hypot(px - centre[0], py - centre[1]) for px, py in pixels)
        mask = roof_mask(mosaic, roof_rings[row["building_id"]])

        bearing, lobe, roof = shadows.darkest_lobe_bearing(
            grey, centre, pixels, mpp, roof_mask=mask, allowed=allowed
        )
        contrast = roof - lobe
        votes = (
            math.isfinite(bearing)
            and math.isfinite(contrast)
            and contrast >= shadows.MIN_SHADOW_CONTRAST
            and row["type"] not in shadows.NON_CASTERS
        )
        row.update(
            mosaic=mosaic, grey=grey, mpp=mpp, centre=centre, pixels=pixels,
            radius=radius, bearing=bearing, roof=roof, contrast=contrast,
            votes=votes, mask=mask,
        )
        shown = f"{bearing:7.0f}d" if math.isfinite(bearing) else f"{'-':>8}"
        c_shown = f"{contrast:9.1f}" if math.isfinite(contrast) else f"{'-':>9}"
        print(f"{row['fid']:>4} {row['building_id']:>4} {row['type']:>12} "
              f"{roof:6.0f} {lobe:6.0f} {c_shown} {shown}  "
              f"{'yes' if votes else 'no'}")

    voters = [r for r in rows if r["votes"]]
    if len(voters) < 5:
        print("\nToo few obstructions cast a readable shadow. Stopping.")
        return 1

    sun = shadows.solve_scene_sun(
        date_iso,
        [r["bearing"] for r in voters],
        [r["contrast"] for r in voters],
    )
    ist = shadows.solar_time_to_ist(sun.solar_time_hours)

    print(f"\nPass 2 - the sun that made them, from {sun.votes} voting shadows")
    print(f"  shadow bearing   {sun.shadow_bearing_deg:.1f} deg")
    print(f"  concentration    {sun.concentration:.2f} "
          f"({'usable' if sun.trustworthy else 'TOO SCATTERED'})")
    print(f"  sun azimuth      {sun.sun_azimuth_deg:.1f} deg")
    print(f"  hour angle       {sun.hour_angle_deg:.2f} deg")
    print(f"  sun elevation    {sun.elevation_deg:.2f} deg")
    print(f"  implied capture  {int(ist)}:{round((ist % 1) * 60):02d} IST")
    if not sun.trustworthy:
        print("\nThe bearings disagree too much to carry a time. Stopping.")
        return 1

    # --- pass three: how long is each shadow? -----------------------------
    print(f"\nPass 3 - shadow length along {sun.shadow_bearing_deg:.0f} deg, "
          f"and the height it implies")
    print(f"{'fid':>4} {'bld':>4} {'type':>12} {'shadow m':>9} {'height m':>9}")
    for row in rows:
        if row["type"] in shadows.NON_CASTERS:
            row["height"] = 0.0
            row["shadow"] = 0.0
            print(f"{row['fid']:>4} {row['building_id']:>4} {row['type']:>12} "
                  f"{'-':>9} {'0.00':>9}  (a hole, not an object)")
            continue
        reach = shadows.extent_along(
            row["pixels"], row["centre"], sun.shadow_bearing_deg
        )
        run = shadows.shadow_run(
            row["grey"], row["centre"], reach, sun.shadow_bearing_deg,
            row["mpp"], row["roof"],
            max(row["contrast"], shadows.MIN_SHADOW_CONTRAST)
            if math.isfinite(row["contrast"]) else shadows.MIN_SHADOW_CONTRAST,
            roof_mask=row["mask"],
        )
        row["shadow"] = run
        row["height"] = shadows.height_from_shadow(run, sun.elevation_deg) if run > 0 else 0.0
        print(f"{row['fid']:>4} {row['building_id']:>4} {row['type']:>12} "
              f"{run:9.2f} {row['height']:9.2f}")

    # --- summary by type --------------------------------------------------
    print("\nBy type, against what the model has been assuming")
    print(f"{'type':>12} {'n':>3} {'measured':>9} {'spread':>14} {'assumed':>8} {'shift':>8}")
    summary = {}
    for kind in sorted({r["type"] for r in rows}):
        heights = [r["height"] for r in rows if r["type"] == kind and r["height"] > 0]
        assumed = config.OBSTRUCTION_HEIGHTS_M.get(kind, float("nan"))
        if not heights:
            print(f"{kind:>12} {0:>3} {'-':>9} {'-':>14} {assumed:8.1f} "
                  f"{'no shadow':>8}")
            continue
        median = statistics.median(heights)
        summary[kind] = median
        spread = f"{min(heights):.1f} to {max(heights):.1f}"
        print(f"{kind:>12} {len(heights):>3} {median:9.2f} {spread:>14} "
              f"{assumed:8.1f} {median - assumed:+8.2f}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "fid", "building_id", "obstruction_type", "shadow_m", "height_m",
            "contrast", "bearing_deg", "voted", "scene_date", "sun_elevation_deg",
            "sun_azimuth_deg", "concentration", "source",
        ])
        for row in rows:
            writer.writerow([
                row["fid"], row["building_id"], row["type"],
                f"{row.get('shadow', 0.0):.3f}", f"{row.get('height', 0.0):.3f}",
                f"{row['contrast']:.1f}", f"{row['bearing']:.0f}",
                "yes" if row["votes"] else "no", date_iso,
                f"{sun.elevation_deg:.3f}", f"{sun.sun_azimuth_deg:.3f}",
                f"{sun.concentration:.3f}", "esri_world_imagery_shadow",
            ])
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

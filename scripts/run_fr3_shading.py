"""FR-3: how much of the year's sunlight the surroundings take away.

    uv run python scripts/run_fr3_shading.py

Builds a horizon profile for every sampled point on every candidate roof -
the highest obstruction in each degree of azimuth - from three kinds of
shade caster:

    neighbouring buildings   OSM outlines, heights from tags where given
    the roof's own parapet   a wall around the roof edge
    objects on the roof      the 21 polygons digitised in Part 4

Then it walks the real sun positions of the NASA series and reports, per roof,
the fraction of plane-of-array irradiance lost to shade over the year.

Inter-row shading is **not** counted here: the array is spaced by the ground
coverage ratio derived in Part 4 precisely so rows do not shade each other in
the design window, so counting it again would penalise the same geometry twice.
"""

from __future__ import annotations

import csv
import sqlite3
import struct
import sys

sys.path.insert(0, "src")

import numpy as np

from btp_solar import config, fr1_data, fr3_shading, fr4_generation, register

NASA = config.DATA / "nasa_power_28.545_77.192_20140101_20231231.json"
ROOFS = config.DATA / "roofs.gpkg"
OBSTRUCTIONS = config.DATA / "obstructions.gpkg"
FACTORS = config.DATA / "shading_factors.csv"
HORIZONS = config.DATA / "roof_horizons.npz"
FIGURE = config.REPORTS / "figures" / "shading_by_month.png"


def rings_of(blob: bytes):
    envelope = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(blob[3] >> 1) & 0x07]
    wkb = blob[8 + envelope:]
    order = "<" if wkb[0] == 1 else ">"
    pos = 5
    out = []
    count = struct.unpack(order + "I", wkb[pos:pos + 4])[0]
    pos += 4
    for _ in range(count):
        n = struct.unpack(order + "I", wkb[pos:pos + 4])[0]
        pos += 4
        pts = []
        for _ in range(n):
            x, y = struct.unpack(order + "dd", wkb[pos:pos + 16])
            pos += 16
            pts.append((x, y))
        out.append(pts)
    return out


def load_roofs() -> dict[str, dict]:
    """Our ten digitised roofs: outline, holes and height."""
    rows = {r["building_id"]: r for r in register.load()}
    roofs = {}
    with sqlite3.connect(ROOFS) as conn:
        for bid, geom in conn.execute("select building_id, geom from roofs"):
            rings = rings_of(geom)
            roofs[bid] = {
                "outer": rings[0],
                "holes": rings[1:],
                "height_m": float(rows[bid]["height_m"]),
                "osm_id": rows[bid]["osm_id"].strip(),
            }
    return roofs


def load_obstructions() -> dict[str, list[tuple[str, list]]]:
    out: dict[str, list[tuple[str, list]]] = {}
    if not OBSTRUCTIONS.exists():
        return out
    with sqlite3.connect(OBSTRUCTIONS) as conn:
        for bid, kind, geom in conn.execute(
            "select building_id, obstruction_type, geometry from obstructions"
        ):
            out.setdefault(bid, []).append((kind, rings_of(geom)[0]))
    return out


def neighbour_casters(
    exclude: set[str], default_height: float | None = None
) -> tuple[list[fr3_shading.Caster], dict[str, int]]:
    """Every other building near the campus, as a prism with a top height."""
    import json

    from pyproj import Transformer

    path = fr1_data.fetch_campus_footprints()
    document = json.loads(path.read_text(encoding="utf-8"))
    to_utm = Transformer.from_crs(config.CRS_GEOGRAPHIC, config.CRS_WORKING, always_xy=True)

    casters: list[fr3_shading.Caster] = []
    sources: dict[str, int] = {}
    for element in document["elements"]:
        if str(element.get("id")) in exclude:
            continue
        geometry = element.get("geometry")
        if not geometry:
            members = element.get("members") or []
            geometry = next(
                (m.get("geometry") for m in members
                 if m.get("role") == "outer" and m.get("geometry")), None)
        if not geometry or len(geometry) < 3:
            continue
        height, source = fr1_data.osm_height_m(element.get("tags", {}))
        if source == "assumed" and default_height is not None:
            height = default_height
        sources[source] = sources.get(source, 0) + 1
        outline = [to_utm.transform(p["lon"], p["lat"]) for p in geometry]
        casters.append(fr3_shading.Caster(str(element.get("id")), height, outline))
    return casters, sources


def shading_for(roof, obstruction_rings, neighbours, poa_direct, poa_diffuse,
                azimuths, elevations, include=("neighbours", "parapet", "objects")):
    """Annual and monthly shading loss for one roof, from a chosen set of casters.

    ``include`` selects which kinds of shade caster take part, which is how the
    loss is attributed: run the model with one kind at a time and the campus
    learns where its shade actually comes from.
    """
    import numpy as np
    from shapely.geometry import Polygon

    polygon = Polygon(roof["outer"], roof["holes"])
    usable = polygon.buffer(-config.SETBACK_M)
    for kind, ring in obstruction_rings:
        usable = usable.difference(Polygon(ring))
    if usable.is_empty:
        usable = polygon.buffer(-config.SETBACK_M)

    points_xy = fr3_shading.sample_grid(usable)
    point_z = roof["height_m"] + config.ARRAY_MID_HEIGHT_M

    casters = []
    if "neighbours" in include:
        casters += neighbours
    if "parapet" in include:
        casters.append(fr3_shading.Caster(
            "parapet", roof["height_m"] + config.PARAPET_HEIGHT_M, roof["outer"]))
    if "objects" in include:
        for kind, ring in obstruction_rings:
            rise = config.OBSTRUCTION_HEIGHTS_M.get(kind, 0.0)
            if rise > 0:
                casters.append(fr3_shading.Caster(kind, roof["height_m"] + rise, ring))

    if not casters:
        return {"points": len(points_xy), "svf": 1.0, "annual": 0.0,
                "monthly": [0.0] * 12, "horizons": np.zeros((len(points_xy), config.HORIZON_BINS))}

    cloud = fr3_shading.caster_points(casters, near=polygon.bounds)
    horizons = np.array([
        fr3_shading.horizon_profile((x, y, point_z), cloud) for x, y in points_xy
    ])
    svf = float(np.mean([fr3_shading.sky_view_factor(h) for h in horizons]))
    beam = fr3_shading.sunlit_fraction_series(horizons, azimuths, elevations)

    unshaded = poa_direct + poa_diffuse
    shaded = poa_direct * beam + poa_diffuse * svf
    return {
        "points": len(points_xy),
        "svf": svf,
        "annual": float(1.0 - shaded.sum() / unshaded.sum()),
        "shaded": shaded,
        "unshaded": unshaded,
        "beam": beam,
        "horizons": horizons,
    }


def main() -> int:
    for path in (ROOFS, NASA):
        if not path.exists():
            print(f"missing {path.name}; earlier steps must run first")
            return 1


    roofs = load_roofs()
    obstructions = load_obstructions()
    print(f"Ten digitised roofs, {sum(len(v) for v in obstructions.values())} "
          f"objects on them.")

    casters, sources = neighbour_casters({r["osm_id"] for r in roofs.values()})
    print(f"Neighbouring buildings within the campus box: {len(casters)}")
    print(f"  heights from an OSM height tag   {sources.get('height_tag', 0)}")
    print(f"  heights from building:levels     {sources.get('levels', 0)}")
    print(f"  heights assumed at "
          f"{config.DEFAULT_NEIGHBOUR_HEIGHT_M:.1f} m        {sources.get('assumed', 0)}")

    # our own roofs shade each other, and are better digitised than OSM
    for bid, roof in roofs.items():
        casters.append(fr3_shading.Caster(bid, roof["height_m"], roof["outer"]))

    print("\nSun positions over the NASA series...")
    weather = fr4_generation.load_nasa_hourly(NASA)
    site_chain = fr4_generation.build_site_chain(weather)
    from pvlib import location

    site = location.Location(
        config.SITE_LAT, config.SITE_LON, config.SITE_TZ, config.SITE_ELEVATION_M
    )
    solpos = site.get_solarposition(weather.index)
    elevations = solpos["apparent_elevation"].to_numpy()
    azimuths = solpos["azimuth"].to_numpy()

    poa_direct = site_chain.poa_direct.to_numpy()
    poa_diffuse = site_chain.poa_diffuse.to_numpy()
    months = weather.index.month.to_numpy()

    header = (f"\n  {'id':<5}{'pts':>5}{'SVF':>7}{'annual':>9}{'worst':>8}{'  month':>8}")
    print(header)
    print("  " + "-" * (len(header) - 3))

    rows = register.load()
    by_id = {r["building_id"]: r for r in rows}
    factor_rows = []
    stored = {}
    results = {}

    for bid in sorted(roofs):
        result = shading_for(roofs[bid], obstructions.get(bid, []),
                             [c for c in casters if c.name != bid],
                             poa_direct, poa_diffuse, azimuths, elevations)
        results[bid] = result
        monthly = [float(1.0 - result["shaded"][months == m].sum()
                         / result["unshaded"][months == m].sum()) for m in range(1, 13)]
        worst = int(np.argmax(monthly)) + 1

        print(f"  {bid:<5}{result['points']:>5}{result['svf']:>7.3f}"
              f"{result['annual']:>8.1%}{max(monthly):>8.1%}{worst:>8}")

        by_id[bid].update({
            "annual_shading_loss": register._fmt(round(result["annual"], 4)),
            "worst_month_shading_loss": register._fmt(round(max(monthly), 4)),
            "sky_view_factor": register._fmt(round(result["svf"], 4)),
            "shading_method": "horizon_raytrace",
        })
        stored[bid] = result["horizons"]
        for m, loss in enumerate(monthly, start=1):
            factor_rows.append({
                "building_id": bid, "month": m,
                "shading_loss": round(loss, 4),
                "mean_beam_factor": round(float(result["beam"][months == m].mean()), 4),
                "sky_view_factor": round(result["svf"], 4),
            })

    # --- where does the shade actually come from? -------------------------
    print("\nWhere the shade comes from, campus mean annual loss")
    for label, include in (("neighbouring buildings", ("neighbours",)),
                           ("the roof's own parapet", ("parapet",)),
                           ("objects on the roof", ("objects",)),
                           ("all three together", ("neighbours", "parapet", "objects"))):
        losses = [shading_for(roofs[b], obstructions.get(b, []),
                              [c for c in casters if c.name != b],
                              poa_direct, poa_diffuse, azimuths, elevations,
                              include=include)["annual"] for b in sorted(roofs)]
        print(f"  {label:<26}{float(np.mean(losses)):>7.2%}")

    # --- how much rests on the assumed neighbour height? ------------------
    print(f"""
Sensitivity to the assumed neighbour height
  {sources.get('assumed', 0)} of {sources.get('assumed', 0) + sources.get('levels', 0) + sources.get('height_tag', 0)} """
          f"""neighbours carry no height in OpenStreetMap, so their
  height is assumed. Our roofs stand {min(r['height_m'] for r in roofs.values()):.1f} to """
          f"""{max(r['height_m'] for r in roofs.values()):.1f} m tall, and a
  neighbour shorter than a roof cannot shade it at all - so this assumption
  decides almost all of the neighbour contribution.""")
    print(f"\n  {'assumed height':<18}{'campus mean annual loss':>26}")
    for height in (7.0, 10.5, 14.0, 17.5, 21.0):
        swept, _ = neighbour_casters({r["osm_id"] for r in roofs.values()}, height)
        for bid, roof in roofs.items():
            swept.append(fr3_shading.Caster(bid, roof["height_m"], roof["outer"]))
        losses = [shading_for(roofs[b], obstructions.get(b, []),
                              [c for c in swept if c.name != b],
                              poa_direct, poa_diffuse, azimuths, elevations)["annual"]
                  for b in sorted(roofs)]
        mark = "  <- used" if abs(height - config.DEFAULT_NEIGHBOUR_HEIGHT_M) < 0.01 else ""
        print(f"  {height:>6.1f} m{float(np.mean(losses)):>25.2%}{mark}")

    register.save(rows)
    np.savez_compressed(HORIZONS, **stored)
    with FACTORS.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(factor_rows[0]))
        writer.writeheader()
        writer.writerows(factor_rows)
    print(f"\nWritten {FACTORS.name}, {HORIZONS.name}, and the register")

    try:
        _figure(factor_rows)
        print(f"Figure:  {FIGURE.relative_to(config.ROOT)}")
    except Exception as exc:  # noqa: BLE001 - a figure must not fail the run
        print(f"Figure skipped: {exc}")

    print("""
FR-3 acceptance
  [BLOCKED] shadow geometry validation: the criterion compares a modelled
  shadow against one measured in dated satellite imagery, and the acquisition
  date of the Esri scenes used in Part 4 was never recorded. The sun's position
  depends on the date, so without it there is nothing to compare against.
  acceptance.fr3_shadow_length is implemented and tested; it needs one dated
  image and one measured shadow to run.

  What can be said meanwhile: the geometry reproduces a hand derivation
  exactly (tests/test_shading.py), and the PVGIS horizon profile independently
  confirmed the far horizon is flat, so every shadow modelled here is local.""")
    return 0


def _figure(rows) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import calendar

    import matplotlib.pyplot as plt

    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    buildings = sorted({r["building_id"] for r in rows})
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    for bid in buildings:
        series = [r["shading_loss"] for r in rows if r["building_id"] == bid]
        ax.plot(range(1, 13), series, linewidth=1.1, color="#808080")
        ax.annotate(bid, (12, series[-1]), fontsize=7, color="#404040",
                    xytext=(3, -2), textcoords="offset points")
    mean = [np.mean([r["shading_loss"] for r in rows if r["month"] == m])
            for m in range(1, 13)]
    ax.plot(range(1, 13), mean, linewidth=2.2, color="#000000", label="mean of ten roofs")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels([calendar.month_abbr[m] for m in range(1, 13)])
    ax.set_ylabel("share of plane-of-array irradiance lost to shade")
    ax.set_title("FR-3 shading loss by month: neighbours, parapets and rooftop objects\n"
                 "deepest in December, when shadows are longest",
                 fontsize=9, loc="left")
    ax.legend(frameon=False, fontsize=8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURE, dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())

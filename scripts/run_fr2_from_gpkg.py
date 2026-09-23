"""FR-2: run the area chain from the digitised layers and write the register.

    uv run python scripts/run_fr2_from_gpkg.py

Reads the hand-digitised roofs and obstructions, runs the usable-area chain,
writes every intermediate value into data/building_register.csv, and reports
the FR-2 acceptance position.

The register is the audit trail, so each derived column is written there rather
than only printed: gross area, obstruction footprint, setback strip, net
available area, ground coverage ratio, module area and installable capacity.
"""

from __future__ import annotations

import collections
import math
import sqlite3
import struct
import sys
from pathlib import Path

sys.path.insert(0, "src")

from btp_solar import config, fr2_usable_area, register  # noqa: E402
from btp_solar.fr2_usable_area import RoofMeasurements  # noqa: E402
from btp_solar.solar_geometry import design_sun_position  # noqa: E402

ROOFS = config.DATA / "roofs.gpkg"
OBSTRUCTIONS = config.DATA / "obstructions.gpkg"


def rings(blob: bytes):
    envelope = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(blob[3] >> 1) & 0x07]
    wkb = blob[8 + envelope:]
    order = "<" if wkb[0] == 1 else ">"
    pos, out = 5, []
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


def area(ring) -> float:
    return abs(sum(ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
                   for i in range(len(ring) - 1))) / 2


def perimeter(ring) -> float:
    return sum(math.dist(ring[i], ring[i + 1]) for i in range(len(ring) - 1))


def main() -> int:
    if not ROOFS.exists():
        print(f"{ROOFS} not found.")
        return 1

    sun = design_sun_position(config.SITE_LAT, config.SHADING_CRITERION)
    print(f"Design sun: {sun.elevation_deg:.2f} deg elevation, "
          f"{sun.azimuth_from_south_deg:.2f} deg from south ({sun.label})")
    print(f"Tilt {config.MODULE_TILT_DEG} deg, setback {config.SETBACK_M} m, "
          f"packing {config.PACKING_FACTOR}\n")

    geometry: dict[str, list] = collections.defaultdict(list)
    for bid, blob in sqlite3.connect(ROOFS).execute("SELECT building_id, geom FROM roofs"):
        geometry[bid].append(rings(blob))

    obstruction_area: dict[str, float] = collections.defaultdict(float)
    obstruction_count: dict[str, int] = collections.defaultdict(int)
    if OBSTRUCTIONS.exists():
        for bid, blob in sqlite3.connect(OBSTRUCTIONS).execute(
                "SELECT building_id, geometry FROM obstructions"):
            obstruction_area[bid] += sum(area(r) for r in rings(blob))
            obstruction_count[bid] += 1

    header = (f"{'id':<5}{'gross':>8}{'obstr':>8}{'setback':>9}{'net':>8}"
              f"{'module':>8}{'kWp':>8}{'% roof':>8}")
    print(header)
    print("-" * len(header))

    rows = register.load()
    by_id = {r["building_id"]: r for r in rows}
    totals = collections.Counter()

    for bid in sorted(geometry):
        parts = geometry[bid]
        gross = sum(area(p[0]) - sum(area(h) for h in p[1:]) for p in parts)
        edge = sum(perimeter(r) for p in parts for r in p)
        obstructed = obstruction_area.get(bid, 0.0)

        result = fr2_usable_area.compute(
            RoofMeasurements(bid, gross, obstructed, edge))

        print(f"{bid:<5}{gross:>8.0f}{obstructed:>8.0f}{result.setback_area_m2:>9.0f}"
              f"{result.net_available_area_m2:>8.0f}{result.module_area_m2:>8.0f}"
              f"{result.installable_capacity_kwp:>8.1f}"
              f"{result.usable_fraction_of_roof:>7.1%}")

        totals["gross"] += gross
        totals["obstructed"] += obstructed
        totals["module"] += result.module_area_m2
        totals["kwp"] += result.installable_capacity_kwp

        if bid in by_id:
            by_id[bid].update({k: register._fmt(v) for k, v in result.as_row().items()})
            by_id[bid]["obstruction_count"] = str(obstruction_count.get(bid, 0))
            by_id[bid]["roof_perimeter_m"] = register._fmt(edge)

    print("-" * len(header))
    print(f"{'TOT':<5}{totals['gross']:>8.0f}{totals['obstructed']:>8.0f}"
          f"{'':>9}{'':>8}{totals['module']:>8.0f}{totals['kwp']:>8.1f}")

    register.save(rows)
    print(f"\nWritten to {config.REGISTER_CSV.relative_to(config.ROOT)}")

    # --- FR-2 acceptance -------------------------------------------------
    print("\nFR-2 acceptance")
    gcr = fr2_usable_area.compute(
        RoofMeasurements("x", 1000.0, 0.0, 130.0)).ground_coverage_ratio
    print(f"  usable area derived from a {config.SETBACK_M} m setback and a ground")
    print(f"  coverage ratio of {gcr:.3f}, computed from the winter sun rather than")
    print("  assumed as a percentage: PASS")
    missing = [b for b in geometry if b not in obstruction_area]
    if missing:
        print(f"  obstructions digitised on {len(geometry) - len(missing)}/{len(geometry)} "
              f"roofs; none found on {', '.join(sorted(missing))}")
    print("\n  The segmentation IoU criterion belongs to Part 5 and is not")
    print("  evaluated here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

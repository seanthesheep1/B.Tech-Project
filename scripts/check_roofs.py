"""Validate the digitised roof and obstruction layers, and report progress.

    uv run python scripts/check_roofs.py

Run this after every digitising session. Each check exists because the defect
it looks for actually occurred and was invisible on screen:

- a polygon in the wrong hemisphere, from an OSM way/relation id collision
- a self-intersecting outline, which makes the shoelace area meaningless
  rather than merely inaccurate
- duplicate vertices from a stray double-click
- a building present twice, because redrawing adds a feature rather than
  replacing one
- an obstruction naming a neighbouring block, which is undetectable by eye
  when two buildings run parallel

GeoPackage geometry is read directly from the WKB rather than through GDAL,
so this has no heavy dependencies and runs anywhere.
"""

from __future__ import annotations

import collections
import math
import struct
import sys
from pathlib import Path

sys.path.insert(0, "src")

from btp_solar import config, fr2_usable_area  # noqa: E402
from btp_solar.fr2_usable_area import RoofMeasurements  # noqa: E402

ROOFS = config.DATA / "roofs.gpkg"
OBSTRUCTIONS = config.DATA / "obstructions.gpkg"
EXPECTED = {f"B{i:02d}" for i in range(1, 11)}

# generous box around the campus; anything outside is a fetch or projection error
X_RANGE = (713_000.0, 716_000.0)
Y_RANGE = (3_158_000.0, 3_161_000.0)
DUPLICATE_VERTEX_TOL = 0.01  # metres
PLACEHOLDER_OBSTRUCTION_FRACTION = 0.08


def envelope_size(flags: int) -> int:
    return {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(flags >> 1) & 0x07]


def rings(blob: bytes) -> list[list[tuple[float, float]]]:
    """Ring coordinates from a GeoPackage polygon blob."""
    wkb = blob[8 + envelope_size(blob[3]):]
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


def area(ring: list[tuple[float, float]]) -> float:
    return abs(sum(ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
                   for i in range(len(ring) - 1))) / 2


def perimeter(ring: list[tuple[float, float]]) -> float:
    return sum(math.dist(ring[i], ring[i + 1]) for i in range(len(ring) - 1))


def net_area(rs: list[list[tuple[float, float]]]) -> float:
    """Outer ring less any holes - courtyards and gaps are not roof."""
    return area(rs[0]) - sum(area(r) for r in rs[1:])


def segments_cross(a, b, c, d) -> bool:
    def orient(p, q, r):
        v = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else 2)
    return orient(a, b, c) != orient(a, b, d) and orient(c, d, a) != orient(c, d, b)


def self_intersects(ring) -> bool:
    n = len(ring) - 1
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if segments_cross(ring[i], ring[i + 1], ring[j], ring[j + 1]):
                return True
    return False


def duplicate_vertices(ring) -> list[int]:
    return [i for i in range(len(ring) - 1)
            if math.dist(ring[i], ring[i + 1]) < DUPLICATE_VERTEX_TOL]


def centroid(ring):
    pts = ring[:-1]
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def point_in_ring(pt, ring) -> bool:
    x, y = pt
    inside = False
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def point_in_polygon(pt, rs) -> bool:
    return point_in_ring(pt, rs[0]) and not any(point_in_ring(pt, h) for h in rs[1:])


def load(path: Path, table: str, geom_column: str):
    import sqlite3
    con = sqlite3.connect(path)
    cols = [r[1] for r in con.execute(f'PRAGMA table_info("{table}")')]
    rows = [dict(zip(cols, r)) for r in con.execute(f'SELECT * FROM "{table}"')]
    con.close()
    for r in rows:
        r["_rings"] = rings(r[geom_column])
    return rows


def main() -> int:
    if not ROOFS.exists():
        print(f"{ROOFS} not found - nothing digitised yet.")
        return 1

    roofs = load(ROOFS, "roofs", "geom")
    obstructions = load(OBSTRUCTIONS, "obstructions", "geometry") if OBSTRUCTIONS.exists() else []
    problems = 0

    by_id = collections.defaultdict(list)
    for r in roofs:
        by_id[r["building_id"]].append(r)

    def report(label: str, offenders: list[str]) -> None:
        nonlocal problems
        if offenders:
            problems += len(offenders)
            print(f"  FAIL  {label}: {', '.join(offenders)}")
        else:
            print(f"  ok    {label}")

    print(f"{len(roofs)} roof features, {len(obstructions)} obstructions\n")

    report("every building present", sorted(EXPECTED - set(by_id)))
    report("no duplicate buildings", sorted(b for b, v in by_id.items() if len(v) > 1))
    report("all vertices on campus",
           sorted({r["building_id"] for r in roofs for ring in r["_rings"] for x, y in ring
                   if not (X_RANGE[0] <= x <= X_RANGE[1] and Y_RANGE[0] <= y <= Y_RANGE[1])}))
    report("no self-intersections",
           sorted({r["building_id"] for r in roofs
                   for ring in r["_rings"] if self_intersects(ring)}))
    report("no duplicate vertices",
           sorted({r["building_id"] for r in roofs
                   for ring in r["_rings"] if duplicate_vertices(ring)}))
    report("all rings closed",
           sorted({r["building_id"] for r in roofs
                   for ring in r["_rings"] if ring[0] != ring[-1]}))

    misplaced = []
    for o in obstructions:
        c = centroid(o["_rings"][0])
        owner = next((b for b, rs in by_id.items()
                      if any(point_in_polygon(c, r["_rings"]) for r in rs)), None)
        if owner != o["building_id"]:
            misplaced.append(f"fid {o['fid']} says {o['building_id']}, sits on {owner}")
    report("obstructions on the right roof", misplaced)

    obstruction_area = collections.defaultdict(float)
    for o in obstructions:
        obstruction_area[o["building_id"]] += sum(area(r) for r in o["_rings"])

    print(f"\n{'id':<5}{'building':<26}{'OSM':>8}{'digitised':>10}{'change':>8}"
          f"{'kWp':>8}  obstr")
    print("-" * 74)
    total_osm = total_now = total_kwp = 0.0
    for bid in sorted(by_id):
        rs = by_id[bid]
        a = sum(net_area(r["_rings"]) for r in rs)
        p = sum(perimeter(ring) for r in rs for ring in r["_rings"])
        measured = bid in obstruction_area
        obstruction = obstruction_area.get(bid, PLACEHOLDER_OBSTRUCTION_FRACTION * a)
        osm = next((r["osm_area_m2"] for r in rs if r["osm_area_m2"]), 0) or 0
        total_osm += osm
        total_now += a
        change = f"{(a - osm) / osm * 100:+.0f}%" if osm else "-"
        name = (rs[0]["building_name"] or "?")[:25]
        try:
            result = fr2_usable_area.compute(RoofMeasurements(bid, a, obstruction, p))
        except ValueError as exc:
            # A tangled outline gives a tiny area against a long perimeter, so the
            # setback eats everything. Report it rather than aborting the run.
            problems += 1
            print(f"{bid:<5}{name:<26}{osm:>8.0f}{a:>10.0f}{change:>8}{'--':>8}  "
                  f"UNUSABLE: {exc.args[0].split(': ', 1)[-1]}")
            continue
        total_kwp += result.installable_capacity_kwp
        print(f"{bid:<5}{name:<26}{osm:>8.0f}{a:>10.0f}"
              f"{change:>8}{result.installable_capacity_kwp:>8.1f}  "
              f"{'measured' if measured else 'PLACEHOLDER'}")
    print("-" * 74)
    drop = (total_now - total_osm) / total_osm * 100 if total_osm else 0
    print(f"{'TOTAL':<31}{total_osm:>8.0f}{total_now:>10.0f}{drop:>+7.0f}%{total_kwp:>8.1f} kWp")

    verified = sum(1 for rs in by_id.values() if rs[0]["verified"] == "yes")
    placeholders = sum(1 for b in by_id if b not in obstruction_area)
    print(f"\nverified {verified}/{len(EXPECTED)}   "
          f"{placeholders} roofs still on the {PLACEHOLDER_OBSTRUCTION_FRACTION:.0%} "
          f"obstruction placeholder")

    print(f"\n{problems} problem(s)" if problems else "\nno problems found")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())

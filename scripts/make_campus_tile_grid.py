"""Fix the satellite tile grid for the campus and record it.

    uv run python scripts/make_campus_tile_grid.py

This writes data/campus_tiles_manifest.csv, which states where every tile sits
before a single image is downloaded. The download step then only has to fetch
tiles named in the manifest, and every later step reads a tile's position from
it rather than recomputing one.

The extent covers the ten digitised candidate roofs plus the validation
buildings that carry existing PV, with a margin so that an array near a roof
edge is not cut in half by the grid.
"""

from __future__ import annotations

import json
import sqlite3
import struct
import sys

sys.path.insert(0, "src")

from btp_solar import config, imagery

MANIFEST = config.DATA / "campus_tiles_manifest.csv"
ROOFS = config.DATA / "roofs.gpkg"
FOOTPRINTS = config.DATA / "footprints_osm.json"

MARGIN_M = 150.0  # beyond the outermost roof, so edge arrays stay whole

# The validation buildings carry existing PV and are the point of the census,
# but their register rows hold a name and nothing else. These three were found
# in the OSM footprints already on disk; Blocks 1, 5 and 6 still need locating.
VALIDATION_OSM_NAMES = {
    "V01": "Bharti School of Telecom Technology and Management",
    "V05": "Karakoram",
    "V06": "Shivalik Hostel",
}


def rings_of(blob: bytes):
    """Polygon rings out of a GeoPackage blob, without a GDAL dependency."""
    if True:
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


def roof_bounds_utm() -> tuple[float, float, float, float]:
    """Bounding box of every digitised roof, in EPSG:32643."""
    xs: list[float] = []
    ys: list[float] = []
    with sqlite3.connect(ROOFS) as conn:
        for (geom,) in conn.execute("select geom from roofs"):
            for ring in rings_of(geom):
                xs += [p[0] for p in ring]
                ys += [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def validation_points() -> list[tuple[str, float, float]]:
    """Centroids of the validation buildings we can already locate."""
    if not FOOTPRINTS.exists():
        return []
    elements = json.loads(FOOTPRINTS.read_text(encoding="utf-8"))
    elements = elements.get("elements", elements)
    by_name = {}
    for element in elements:
        name = element.get("tags", {}).get("name")
        lat = element.get("lat") or (element.get("center") or {}).get("lat")
        lon = element.get("lon") or (element.get("center") or {}).get("lon")
        if name and lat and lon:
            by_name[name] = (float(lat), float(lon))

    found = []
    for building_id, name in VALIDATION_OSM_NAMES.items():
        if name in by_name:
            found.append((building_id, *by_name[name]))
    return found


def main() -> int:
    if not ROOFS.exists():
        print(f"missing {ROOFS.name}; Part 4 must be complete first")
        return 1

    from pyproj import Transformer

    to_wgs = Transformer.from_crs(config.CRS_WORKING, config.CRS_GEOGRAPHIC, always_xy=True)

    min_e, min_n, max_e, max_n = roof_bounds_utm()
    print("Digitised roofs, EPSG:32643")
    print(f"  easting  {min_e:.0f} to {max_e:.0f}  ({max_e - min_e:.0f} m)")
    print(f"  northing {min_n:.0f} to {max_n:.0f}  ({max_n - min_n:.0f} m)")

    min_lon, min_lat = to_wgs.transform(min_e - MARGIN_M, min_n - MARGIN_M)
    max_lon, max_lat = to_wgs.transform(max_e + MARGIN_M, max_n + MARGIN_M)

    extra = validation_points()
    for building_id, lat, lon in extra:
        min_lat, max_lat = min(min_lat, lat), max(max_lat, lat)
        min_lon, max_lon = min(min_lon, lon), max(max_lon, lon)
    if extra:
        margin_deg = MARGIN_M / 111_320.0
        min_lat -= margin_deg
        max_lat += margin_deg
        min_lon -= margin_deg
        max_lon += margin_deg
        print(f"\nValidation buildings located in the OSM footprints: "
              f"{', '.join(b for b, _, _ in extra)}")
    missing = sorted(set(VALIDATION_OSM_NAMES) - {b for b, _, _ in extra})
    still = sorted({"V01", "V02", "V03", "V04", "V05", "V06"} - {b for b, _, _ in extra})
    if still:
        print(f"  still to locate: {', '.join(still)} "
              f"- the census cannot check these until they have coordinates")
    if missing:
        print(f"  expected but not found: {', '.join(missing)}")

    tiles = imagery.tile_grid((min_lon, min_lat, max_lon, max_lat))
    sample = tiles[0]

    print("\nTile grid")
    print(f"  extent        {min_lon:.5f}, {min_lat:.5f} to {max_lon:.5f}, {max_lat:.5f}")
    print(f"  zoom          {sample.zoom}, {sample.size_px} px")
    print(f"  resolution    {sample.metres_per_pixel:.4f} m/pixel")
    print(f"  tile side     {sample.size_m:.1f} m")
    print(f"  tiles         {len(tiles)}")
    print(f"  ground cover  {len(tiles) * sample.size_m**2 / 1e6:.2f} km2")

    # The manifest is only valid if it actually covers what we digitised.
    # Checked here rather than trusted, as with the Part 4 roof checks.
    covered = {t.tile_id for t in tiles}
    uncovered, spans = 0, {}
    with sqlite3.connect(ROOFS) as conn:
        for building_id, geom in conn.execute("select building_id, geom from roofs"):
            hits = set()
            for ring in rings_of(geom):
                for easting, northing in ring:
                    lon, lat = to_wgs.transform(easting, northing)
                    here = [t.tile_id for t in tiles if t.contains(lat, lon)]
                    if here:
                        hits.add(here[0])
                    else:
                        uncovered += 1
            spans[building_id] = len(hits & covered)

    if uncovered:
        print(f"\n  FAIL: {uncovered} roof vertices fall outside the grid; "
              f"raise MARGIN_M and re-run")
        return 1

    multi = {b: n for b, n in spans.items() if n > 1}
    print(f"  roofs covered {len(spans)}/{len(spans)}, no vertex outside the grid")
    print(f"  roofs split across more than one tile: {len(multi)} "
          f"(up to {max(spans.values())})")
    print("  -> detections must be dissolved across tile edges before their area "
          "means anything")

    imagery.write_manifest(tiles, MANIFEST)
    print(f"\nWritten {MANIFEST.relative_to(config.ROOT)} - "
          f"the position of every tile, recorded before anything is downloaded.")
    print("\nNothing has been fetched. scripts/fetch_campus_tiles.py will read this")
    print("manifest and download only the tiles it names.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Satellite tile geometry: the bridge from detected pixels to campus metres.

A segmentation model returns masks in pixel coordinates inside a 640x640 tile.
Nothing in this project can use that until it becomes an area in square metres
attached to a named building. This module is that conversion, and it is kept
free of any network call or model import so that every step of it can be
tested.

**Why a manifest rather than a formula.** The obvious design is to recompute
the tile grid wherever a coordinate is needed, and recover a tile's position
from its index. The earlier `rooftop-solar-pv` code did exactly that in two
separate scripts, and they disagreed: one stepped longitude by
``tile / (111320 cos phi)`` and numbered only the tiles it kept, the other used
the latitude step for both axes and numbered every point in the grid. Same tile
id, different place - a median of 872 m apart over this campus, which is a
different building every time, and nothing about the output looks wrong.

So a tile's position is **recorded once, when it is created**, and every later
step reads it back. This is the register rule applied to imagery: a number
whose provenance is not written down at the time is a number that gets argued
about in November.
"""

from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from . import config

# Web Mercator ground resolution at the equator, metres per pixel at zoom 0.
EQUATOR_METRES_PER_PIXEL = 156543.03392


def metres_per_pixel(latitude: float, zoom: int) -> float:
    """Ground resolution of a Web Mercator tile at this latitude and zoom.

    At zoom 19 and the campus latitude this is 0.262 m, so a 640 pixel tile is
    168 m across - sub-metre imagery, which is what FR-1 asks for.
    """
    if not -85.0 <= latitude <= 85.0:
        raise ValueError(f"latitude {latitude} is outside the Web Mercator range")
    if zoom < 0:
        raise ValueError("zoom must not be negative")
    return EQUATOR_METRES_PER_PIXEL * math.cos(math.radians(latitude)) / (2**zoom)


@dataclass(frozen=True)
class TileSpec:
    """One satellite tile, with its position recorded rather than derived."""

    tile_id: int
    centre_lat: float
    centre_lon: float
    zoom: int
    size_px: int
    metres_per_pixel: float
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float

    @property
    def size_m(self) -> float:
        return self.size_px * self.metres_per_pixel

    def contains(self, lat: float, lon: float) -> bool:
        return self.min_lat <= lat <= self.max_lat and self.min_lon <= lon <= self.max_lon


def _degree_steps(latitude: float, tile_m: float) -> tuple[float, float]:
    """Degrees of longitude and latitude spanned by one tile.

    A degree of longitude shrinks with the cosine of the latitude while a
    degree of latitude does not, so the two steps are different. Using the
    latitude step for both - the mistake in the earlier code - stretches the
    grid east-west by 14 per cent at this latitude.
    """
    lat_step = tile_m / 111320.0
    lon_step = tile_m / (111320.0 * math.cos(math.radians(latitude)))
    return lon_step, lat_step


def tile_grid(
    bounds: tuple[float, float, float, float],
    zoom: int = 19,
    size_px: int = 640,
) -> list[TileSpec]:
    """Lay a non-overlapping grid of tiles over a lat/lon bounding box.

    ``bounds`` is (min_lon, min_lat, max_lon, max_lat). Tiles are numbered in
    row-major order from the south-west corner, and every tile generated is
    kept: there is no filtering step whose result a later script would have to
    reproduce.
    """
    min_lon, min_lat, max_lon, max_lat = bounds
    if min_lon >= max_lon or min_lat >= max_lat:
        raise ValueError(f"degenerate bounds {bounds}")

    centre_lat = (min_lat + max_lat) / 2.0
    mpp = metres_per_pixel(centre_lat, zoom)
    tile_m = size_px * mpp
    lon_step, lat_step = _degree_steps(centre_lat, tile_m)

    tiles: list[TileSpec] = []
    lat = min_lat + lat_step / 2.0
    tile_id = 0
    while lat - lat_step / 2.0 < max_lat:
        lon = min_lon + lon_step / 2.0
        while lon - lon_step / 2.0 < max_lon:
            tiles.append(
                TileSpec(
                    tile_id=tile_id,
                    centre_lat=lat,
                    centre_lon=lon,
                    zoom=zoom,
                    size_px=size_px,
                    metres_per_pixel=mpp,
                    min_lat=lat - lat_step / 2.0,
                    min_lon=lon - lon_step / 2.0,
                    max_lat=lat + lat_step / 2.0,
                    max_lon=lon + lon_step / 2.0,
                )
            )
            tile_id += 1
            lon += lon_step
        lat += lat_step
    return tiles


FIELDS = [
    "tile_id", "centre_lat", "centre_lon", "zoom", "size_px",
    "metres_per_pixel", "min_lat", "min_lon", "max_lat", "max_lon",
]


def write_manifest(tiles: list[TileSpec], path: Path, fetched_date: str = "") -> None:
    """Record every tile's position. This file is the provenance, not the images."""
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=[*FIELDS, "fetched_date"])
        writer.writeheader()
        for tile in tiles:
            row = asdict(tile)
            row["fetched_date"] = fetched_date
            writer.writerow(row)


def read_manifest(path: Path) -> dict[int, TileSpec]:
    """Read tile positions back, keyed by id. Never recompute them instead."""
    out: dict[int, TileSpec] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            spec = TileSpec(
                tile_id=int(row["tile_id"]),
                centre_lat=float(row["centre_lat"]),
                centre_lon=float(row["centre_lon"]),
                zoom=int(row["zoom"]),
                size_px=int(row["size_px"]),
                metres_per_pixel=float(row["metres_per_pixel"]),
                min_lat=float(row["min_lat"]),
                min_lon=float(row["min_lon"]),
                max_lat=float(row["max_lat"]),
                max_lon=float(row["max_lon"]),
            )
            out[spec.tile_id] = spec
    return out


def pixel_to_lonlat(tile: TileSpec, x: float, y: float) -> tuple[float, float]:
    """Convert a pixel inside a tile to longitude and latitude.

    Pixel (0, 0) is the top-left corner of the image and y increases
    *southward*, which is the opposite of latitude.
    """
    dx_m = (x - tile.size_px / 2.0) * tile.metres_per_pixel
    dy_m = (tile.size_px / 2.0 - y) * tile.metres_per_pixel
    lon_step, lat_step = _degree_steps(tile.centre_lat, 1.0)
    return tile.centre_lon + dx_m * lon_step, tile.centre_lat + dy_m * lat_step


def polygon_to_utm(tile: TileSpec, pixels: list[tuple[float, float]]):
    """A detection's pixel outline as a polygon in EPSG:32643, measured in metres.

    All area measurement in this project happens in UTM 43N and never in
    degrees, per the rule in data/README.md.
    """
    from pyproj import Transformer
    from shapely.geometry import Polygon

    if len(pixels) < 3:
        raise ValueError("a polygon needs at least three points")
    transformer = Transformer.from_crs(
        config.CRS_GEOGRAPHIC, config.CRS_WORKING, always_xy=True
    )
    lonlat = [pixel_to_lonlat(tile, x, y) for x, y in pixels]
    return Polygon([transformer.transform(lon, lat) for lon, lat in lonlat])


def capacity_from_block_area(
    block_area_m2: float,
    ground_coverage_ratio: float,
    power_density_w_per_m2: float = config.MODULE_POWER_DENSITY_W_PER_M2,
) -> float:
    """Installed capacity implied by the plan area of an array block, in kWp.

    The annotations this rests on outline a **whole array block including the
    gaps between rows** - 89 per cent of them are four-point boxes drawn around
    a field of modules, not around single panels. So the detected area is land
    area, and the ground coverage ratio is what converts it to module area:

        module area = block area x GCR
        kWp         = module area x power density / 1000

    Pass the ratio **measured on the real arrays**, not ``config``'s design
    value of 0.707. That figure is what this project would build; the existing
    campus arrays were laid out by somebody else and may be packed differently.
    Using our own design value here would smuggle an assumption into a check
    whose whole purpose is to be independent.
    """
    if not 0.0 < ground_coverage_ratio <= 1.0:
        raise ValueError(f"ground coverage ratio {ground_coverage_ratio} is not a fraction")
    if block_area_m2 < 0:
        raise ValueError("area must not be negative")
    return block_area_m2 * ground_coverage_ratio * power_density_w_per_m2 / 1000.0

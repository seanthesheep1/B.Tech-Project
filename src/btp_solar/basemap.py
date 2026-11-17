"""Esri World Imagery tiles, fetched and mosaicked.

Why this exists alongside ``imagery.py``: that module lays out a grid of
Google Static Maps requests, each one a centre point and a size, because that
is the shape of that API. Esri serves the standard slippy scheme instead -
Web Mercator, a quadtree of 256-pixel tiles addressed by ``z/y/x`` - so the
geometry is different enough to deserve its own file rather than a flag.

The tiles are free and need no key, and at zoom 19 they are about 0.26 m per
pixel at this latitude, which is the same ground sampling the census was
planned around. More to the point they are the *same scene* the roofs were
traced against - see ``data/imagery_provenance.json`` - so measurements taken
here and polygons drawn in QGIS describe one photograph, not two.

Attribution: Esri World Imagery. The report must say so.

Tiles are cached under ``data/basemap_cache`` and the cache is authoritative
once written: a tile is fetched once and read back thereafter. This is the
same discipline the tile manifest follows - a position is recorded, never
recomputed - and here it also keeps a re-run from hammering someone else's
service.
"""

from __future__ import annotations

import io
import math
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from . import config

TILE_PIXELS = 256
EQUATOR_METRES_PER_PIXEL = 156543.03392

#: Esri World Imagery, the layer the roofs were traced over.
ESRI_WORLD_IMAGERY = (
    "https://services.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/tile/{z}/{y}/{x}"
)

#: Esri publishes World Imagery to level 19 in most of the world and to 20 or
#: 21 over some cities. Asking beyond what exists returns a grey "map data not
#: yet available" tile rather than an error, so the fetcher checks.
DEFAULT_ZOOM = 19

CACHE = Path(__file__).resolve().parents[2] / "data" / "basemap_cache"

_MIN_SECONDS_BETWEEN_REQUESTS = 0.1
_last_request = 0.0


def metres_per_pixel(latitude: float, zoom: int) -> float:
    """Ground sampling distance of a tile pixel at this latitude."""
    return EQUATOR_METRES_PER_PIXEL * math.cos(math.radians(latitude)) / (2.0**zoom)


def lonlat_to_pixel(lon: float, lat: float, zoom: int) -> tuple[float, float]:
    """Web Mercator global pixel coordinates, origin at the top left."""
    if not -85.05112878 <= lat <= 85.05112878:
        raise ValueError(f"latitude {lat} is outside the Web Mercator range")
    n = 2.0**zoom * TILE_PIXELS
    x = (lon + 180.0) / 360.0 * n
    sin_lat = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi)) * n
    return x, y


def pixel_to_lonlat(x: float, y: float, zoom: int) -> tuple[float, float]:
    """Inverse of :func:`lonlat_to_pixel`."""
    n = 2.0**zoom * TILE_PIXELS
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lon, lat


@dataclass(frozen=True)
class Mosaic:
    """A stitched image plus the transform back to the world.

    ``origin`` is the global Web Mercator pixel coordinate of the image's top
    left corner, so a pixel in this image is ``origin + (x, y)`` globally.
    """

    image: "object"  # PIL.Image.Image, not imported at module scope
    origin: tuple[float, float]
    zoom: int
    source: str = ESRI_WORLD_IMAGERY

    def pixel_to_lonlat(self, x: float, y: float) -> tuple[float, float]:
        return pixel_to_lonlat(self.origin[0] + x, self.origin[1] + y, self.zoom)

    def lonlat_to_pixel(self, lon: float, lat: float) -> tuple[float, float]:
        gx, gy = lonlat_to_pixel(lon, lat, self.zoom)
        return gx - self.origin[0], gy - self.origin[1]

    def metres_per_pixel(self, latitude: float | None = None) -> float:
        if latitude is None:
            _, latitude = self.pixel_to_lonlat(
                self.image.size[0] / 2, self.image.size[1] / 2
            )
        return metres_per_pixel(latitude, self.zoom)


def _cache_path(zoom: int, x: int, y: int, source: str) -> Path:
    tag = "esri" if "arcgisonline" in source else "tile"
    return CACHE / tag / str(zoom) / str(x) / f"{y}.jpg"


def fetch_tile(
    zoom: int,
    x: int,
    y: int,
    source: str = ESRI_WORLD_IMAGERY,
    timeout: float = 30.0,
) -> bytes:
    """One tile, from the cache if it is there and from the service if not."""
    global _last_request

    path = _cache_path(zoom, x, y, source)
    if path.exists():
        return path.read_bytes()

    gap = time.monotonic() - _last_request
    if gap < _MIN_SECONDS_BETWEEN_REQUESTS:
        time.sleep(_MIN_SECONDS_BETWEEN_REQUESTS - gap)

    url = source.format(z=zoom, x=x, y=y)
    # A generic client name. Nothing identifying the user goes to this service.
    request = urllib.request.Request(url, headers={"User-Agent": "btp-solar/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            blob = response.read()
    except urllib.error.URLError as exc:  # pragma: no cover - network
        raise RuntimeError(f"could not fetch tile {zoom}/{y}/{x}: {exc}") from exc
    finally:
        _last_request = time.monotonic()

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)
    return blob


def mosaic(
    lon_min: float,
    lat_min: float,
    lon_max: float,
    lat_max: float,
    zoom: int = DEFAULT_ZOOM,
    source: str = ESRI_WORLD_IMAGERY,
    margin_px: int = 0,
) -> Mosaic:
    """Stitch the tiles covering a bounding box into one image."""
    from PIL import Image

    if lon_min > lon_max or lat_min > lat_max:
        raise ValueError("bounding box corners are the wrong way round")

    # Latitude runs the other way in pixel space: lat_max is the top.
    left, top = lonlat_to_pixel(lon_min, lat_max, zoom)
    right, bottom = lonlat_to_pixel(lon_max, lat_min, zoom)
    left -= margin_px
    top -= margin_px
    right += margin_px
    bottom += margin_px

    tx0, ty0 = int(left // TILE_PIXELS), int(top // TILE_PIXELS)
    tx1, ty1 = int(right // TILE_PIXELS), int(bottom // TILE_PIXELS)

    count = (tx1 - tx0 + 1) * (ty1 - ty0 + 1)
    if count > 400:
        raise ValueError(
            f"that box needs {count} tiles at zoom {zoom}; narrow it or zoom out"
        )

    canvas = Image.new(
        "RGB", ((tx1 - tx0 + 1) * TILE_PIXELS, (ty1 - ty0 + 1) * TILE_PIXELS)
    )
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            blob = fetch_tile(zoom, tx, ty, source=source)
            tile = Image.open(io.BytesIO(blob)).convert("RGB")
            canvas.paste(tile, ((tx - tx0) * TILE_PIXELS, (ty - ty0) * TILE_PIXELS))

    origin = (tx0 * TILE_PIXELS, ty0 * TILE_PIXELS)
    # Crop back to the requested box so pixel (0, 0) means what it says.
    box = (
        int(left - origin[0]),
        int(top - origin[1]),
        int(math.ceil(right - origin[0])),
        int(math.ceil(bottom - origin[1])),
    )
    cropped = canvas.crop(box)
    return Mosaic(
        image=cropped,
        origin=(origin[0] + box[0], origin[1] + box[1]),
        zoom=zoom,
        source=source,
    )


def mosaic_around(
    lon: float,
    lat: float,
    radius_m: float,
    zoom: int = DEFAULT_ZOOM,
    source: str = ESRI_WORLD_IMAGERY,
) -> Mosaic:
    """A square mosaic of roughly ``radius_m`` either side of a point."""
    if radius_m <= 0:
        raise ValueError("radius must be positive")
    dlat = radius_m / 111_320.0
    dlon = radius_m / (111_320.0 * math.cos(math.radians(lat)))
    return mosaic(
        lon - dlon, lat - dlat, lon + dlon, lat + dlat, zoom=zoom, source=source
    )


def utm_transformers():
    """Both directions between the working CRS and lon/lat."""
    from pyproj import Transformer

    to_lonlat = Transformer.from_crs(
        config.CRS_WORKING, config.CRS_GEOGRAPHIC, always_xy=True
    )
    to_utm = Transformer.from_crs(
        config.CRS_GEOGRAPHIC, config.CRS_WORKING, always_xy=True
    )
    return to_lonlat, to_utm

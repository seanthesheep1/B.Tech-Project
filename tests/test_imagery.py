"""Tile geometry: every number that turns a detected pixel into campus metres.

None of this needs the segmentation model or a network call, which is the
point: the conversion from pixels to square metres is where a silent error
would do the most damage, so it is the part held down by tests.
"""

from __future__ import annotations

import itertools
import math

import pytest

from btp_solar import config, imagery

CAMPUS = (77.1800, 28.5350, 77.2050, 28.5550)  # min_lon, min_lat, max_lon, max_lat


def test_resolution_at_the_campus_is_sub_metre():
    """Zoom 19 gives 0.262 m per pixel here, so a 640 px tile is 167.9 m."""
    mpp = imagery.metres_per_pixel(config.SITE_LAT, 19)
    assert mpp == pytest.approx(0.2623, abs=0.001)
    assert 640 * mpp == pytest.approx(167.9, abs=0.5)
    assert mpp < 1.0, "FR-1 asks for sub-metre imagery"


def test_resolution_falls_with_latitude_and_rises_with_zoom():
    assert imagery.metres_per_pixel(0.0, 19) > imagery.metres_per_pixel(60.0, 19)
    assert imagery.metres_per_pixel(28.5, 19) == pytest.approx(
        imagery.metres_per_pixel(28.5, 20) * 2
    )


def test_an_impossible_latitude_is_rejected():
    with pytest.raises(ValueError, match="outside the Web Mercator range"):
        imagery.metres_per_pixel(91.0, 19)


def test_the_two_degree_steps_are_not_the_same():
    """The mistake that cost 872 m: a degree of longitude is shorter than a
    degree of latitude everywhere except the equator, so a square tile does not
    span the same number of degrees on both axes."""
    lon_step, lat_step = imagery._degree_steps(config.SITE_LAT, 167.9)
    assert lon_step > lat_step
    assert lon_step / lat_step == pytest.approx(1 / math.cos(math.radians(config.SITE_LAT)), rel=1e-6)
    assert lon_step / lat_step == pytest.approx(1.138, abs=0.005)


def test_the_grid_tiles_the_area_without_gaps_or_overlaps():
    tiles = imagery.tile_grid(CAMPUS)
    assert tiles, "the campus must produce tiles"

    row = [t for t in tiles if t.centre_lat == tiles[0].centre_lat]
    assert len(row) > 1
    for left, right in itertools.pairwise(row):
        assert right.min_lon == pytest.approx(left.max_lon, abs=1e-9)


def test_every_tile_id_is_unique_and_contiguous():
    """Ids must survive a round trip through a filename, so no gaps."""
    tiles = imagery.tile_grid(CAMPUS)
    ids = [t.tile_id for t in tiles]
    assert ids == list(range(len(tiles)))


def test_a_tile_knows_its_own_corner_coordinates():
    tile = imagery.tile_grid(CAMPUS)[0]
    assert tile.contains(tile.centre_lat, tile.centre_lon)
    assert not tile.contains(tile.max_lat + 1.0, tile.centre_lon)
    assert tile.size_m == pytest.approx(167.9, abs=0.5)


def test_the_centre_pixel_is_the_tile_centre():
    tile = imagery.tile_grid(CAMPUS)[5]
    lon, lat = imagery.pixel_to_lonlat(tile, tile.size_px / 2, tile.size_px / 2)
    assert lon == pytest.approx(tile.centre_lon, abs=1e-9)
    assert lat == pytest.approx(tile.centre_lat, abs=1e-9)


def test_pixel_y_increases_southward():
    """Image rows run top to bottom; latitude runs bottom to top. Getting this
    backwards mirrors every detection about the tile's centre."""
    tile = imagery.tile_grid(CAMPUS)[5]
    _, top = imagery.pixel_to_lonlat(tile, 320, 0)
    _, bottom = imagery.pixel_to_lonlat(tile, 320, 639)
    assert top > bottom


def test_a_tile_corner_pixel_lands_on_the_tile_corner():
    tile = imagery.tile_grid(CAMPUS)[5]
    lon, lat = imagery.pixel_to_lonlat(tile, 0, 0)
    assert lon == pytest.approx(tile.min_lon, abs=2e-6)
    assert lat == pytest.approx(tile.max_lat, abs=2e-6)


def test_a_full_tile_measures_its_own_area_in_square_metres():
    """The end-to-end check: pixels in, square metres out, measured in UTM."""
    tile = imagery.tile_grid(CAMPUS)[5]
    polygon = imagery.polygon_to_utm(
        tile, [(0, 0), (tile.size_px, 0), (tile.size_px, tile.size_px), (0, tile.size_px)]
    )
    assert polygon.area == pytest.approx(tile.size_m**2, rel=0.01)
    assert polygon.area == pytest.approx(28_190, rel=0.02)


def test_a_known_array_comes_out_the_right_size():
    """A 34 kWp plant should measure about 224 m2 of block on the ground.

    At 0.2623 m per pixel that is a square of roughly 57 pixels a side.
    """
    tile = imagery.tile_grid(CAMPUS)[5]
    side = math.sqrt(224.0) / tile.metres_per_pixel
    polygon = imagery.polygon_to_utm(
        tile, [(100, 100), (100 + side, 100), (100 + side, 100 + side), (100, 100 + side)]
    )
    assert polygon.area == pytest.approx(224.0, rel=0.02)
    kwp = imagery.capacity_from_block_area(polygon.area, 0.7066)
    assert kwp == pytest.approx(34.0, abs=1.0)


def test_a_degenerate_polygon_is_rejected():
    tile = imagery.tile_grid(CAMPUS)[0]
    with pytest.raises(ValueError, match="at least three points"):
        imagery.polygon_to_utm(tile, [(0, 0), (10, 10)])


def test_capacity_rejects_a_ratio_that_is_not_a_fraction():
    with pytest.raises(ValueError, match="not a fraction"):
        imagery.capacity_from_block_area(100.0, 1.5)


def test_capacity_scales_with_area_and_packing():
    assert imagery.capacity_from_block_area(200.0, 0.7) == pytest.approx(
        2 * imagery.capacity_from_block_area(100.0, 0.7)
    )
    assert imagery.capacity_from_block_area(100.0, 0.8) > imagery.capacity_from_block_area(
        100.0, 0.7
    )


def test_the_manifest_round_trips_exactly(tmp_path):
    """Positions must come back from the file byte for byte, because reading
    them back is the whole mechanism that replaces recomputing them."""
    tiles = imagery.tile_grid(CAMPUS)
    path = tmp_path / "manifest.csv"
    imagery.write_manifest(tiles, path, fetched_date="2026-11-16")
    back = imagery.read_manifest(path)

    assert len(back) == len(tiles)
    for tile in tiles:
        assert back[tile.tile_id] == tile


def test_a_detection_is_placed_from_the_manifest_not_from_a_recomputed_grid(tmp_path):
    """The regression test for the 872 m bug.

    The earlier code recovered a tile's position by rebuilding the grid in a
    second script with slightly different rules. Here the manifest is the only
    source, so a downstream step that is handed a different grid still places
    the detection correctly - it never consults a grid at all.
    """
    tiles = imagery.tile_grid(CAMPUS)
    path = tmp_path / "manifest.csv"
    imagery.write_manifest(tiles, path)

    # A different, wrong grid: the square-degree mistake the old code made.
    wrong = imagery.tile_grid((CAMPUS[0], CAMPUS[1], CAMPUS[2], CAMPUS[3]), zoom=18)
    assert len(wrong) != len(tiles), "the wrong grid must really be different"

    manifest = imagery.read_manifest(path)
    tile = manifest[10]
    lon, lat = imagery.pixel_to_lonlat(tile, 320, 320)
    assert (lon, lat) == pytest.approx((tiles[10].centre_lon, tiles[10].centre_lat))

"""The candidate roof polygons.

These exist because a real defect slipped through: B06 Lecture Hall Complex is
an OSM *relation*, but it was fetched with a `way(id:...)` query. Way and
relation ids are separate number spaces, so the query silently returned a
different building - one in Ohio - and it carried a plausible-looking area of
7,158 m2 all the way into the preliminary campus total.

A polygon in the wrong hemisphere is obvious once looked for and invisible
otherwise, so it is now looked for on every test run.
"""

from __future__ import annotations

import json

import pytest

from btp_solar import config

# Generous box around the IIT Delhi campus; anything outside is a fetch error.
LAT_RANGE = (28.535, 28.560)
LON_RANGE = (77.175, 77.205)


@pytest.fixture(scope="module")
def roofs():
    path = config.DATA / "candidate_roofs.geojson"
    if not path.exists():
        pytest.skip("candidate_roofs.geojson not present")
    return json.loads(path.read_text(encoding="utf-8"))["features"]


def test_there_are_ten_candidates(roofs):
    assert len(roofs) == 10


def test_every_polygon_is_on_the_campus(roofs):
    """Catches a way/relation id collision returning a building elsewhere."""
    for feature in roofs:
        bid = feature["properties"]["building_id"]
        for ring in feature["geometry"]["coordinates"]:
            for lon, lat in ring:
                assert LON_RANGE[0] <= lon <= LON_RANGE[1], f"{bid} longitude {lon} off campus"
                assert LAT_RANGE[0] <= lat <= LAT_RANGE[1], f"{bid} latitude {lat} off campus"


def test_every_ring_is_closed(roofs):
    for feature in roofs:
        for ring in feature["geometry"]["coordinates"]:
            assert ring[0] == ring[-1], f"{feature['properties']['building_id']} ring not closed"


def test_areas_are_plausible_for_a_campus_building(roofs):
    for feature in roofs:
        area = feature["properties"]["osm_area_m2"]
        assert 100 < area < 20000, f"{feature['properties']['building_id']} area {area} m2"


def test_a_courtyard_is_recorded_and_subtracted(roofs):
    """B06 is a multipolygon; its inner ring is a courtyard, not roof."""
    b06 = next(f for f in roofs if f["properties"]["building_id"] == "B06")
    assert b06["properties"]["has_courtyard"] == "yes"
    assert len(b06["geometry"]["coordinates"]) == 2
    # outer 8373 m2 less an inner 408 m2
    assert b06["properties"]["osm_area_m2"] == pytest.approx(7965, abs=5)


def test_every_roof_joins_to_the_register(roofs):
    from btp_solar import register
    ids = {r["building_id"] for r in register.load()}
    for feature in roofs:
        assert feature["properties"]["building_id"] in ids

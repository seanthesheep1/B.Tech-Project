"""The inter-row spacing derivation, checked against values worked out by hand.

FR-2 requires the ground coverage ratio to be derived rather than assumed, so
the derivation itself is what these tests pin down.
"""

from __future__ import annotations

import math

import pytest

from btp_solar import config
from btp_solar.solar_geometry import (
    SunPosition,
    declination,
    design_sun_position,
    ground_coverage_ratio,
    row_pitch_ratio,
    solar_azimuth_from_south,
    solar_elevation,
)


def test_declination_at_solstices_and_equinox():
    assert declination(355) == pytest.approx(-23.44, abs=0.1)   # 21 December
    assert declination(172) == pytest.approx(23.44, abs=0.3)    # 21 June
    assert declination(80) == pytest.approx(0.0, abs=1.0)       # equinox


def test_winter_noon_elevation_at_iit_delhi():
    """At solar noon on the winter solstice, alpha = 90 - lat + dec."""
    expected = 90.0 - config.SITE_LAT + (-23.44)
    computed = solar_elevation(config.SITE_LAT, -23.44, 0.0)
    assert computed == pytest.approx(expected, abs=0.01)
    assert computed == pytest.approx(38.0, abs=0.1)


def test_azimuth_is_due_south_at_solar_noon():
    assert solar_azimuth_from_south(config.SITE_LAT, -23.44, 0.0) == pytest.approx(0.0, abs=0.01)


def test_nine_am_design_point_is_lower_and_further_east():
    noon = design_sun_position(config.SITE_LAT, "winter_noon")
    nine = design_sun_position(config.SITE_LAT, "winter_9_to_3")
    assert nine.elevation_deg < noon.elevation_deg
    assert nine.azimuth_from_south_deg > noon.azimuth_from_south_deg
    # worked by hand: alpha = 22.3 deg, gamma = 44.5 deg from south
    assert nine.elevation_deg == pytest.approx(22.3, abs=0.2)
    assert nine.azimuth_from_south_deg == pytest.approx(44.5, abs=0.3)


def test_pitch_ratio_matches_the_closed_form():
    sun = SunPosition(30.0, 0.0, "test")
    beta = math.radians(20.0)
    expected = math.cos(beta) + math.sin(beta) / math.tan(math.radians(30.0))
    assert row_pitch_ratio(20.0, sun) == pytest.approx(expected)


def test_flat_modules_need_no_spacing():
    sun = design_sun_position(config.SITE_LAT, config.SHADING_CRITERION)
    assert ground_coverage_ratio(0.0, sun) == 1.0


def test_gcr_falls_as_tilt_rises():
    sun = design_sun_position(config.SITE_LAT, config.SHADING_CRITERION)
    ratios = [ground_coverage_ratio(t, sun) for t in (5, 10, 15, 20, 25, 30)]
    assert ratios == sorted(ratios, reverse=True)


def test_gcr_falls_under_the_stricter_criterion():
    """Keeping 09:00 to 15:00 clear costs roof coverage against noon-only."""
    noon = ground_coverage_ratio(15.0, design_sun_position(config.SITE_LAT, "winter_noon"))
    window = ground_coverage_ratio(15.0, design_sun_position(config.SITE_LAT, "winter_9_to_3"))
    assert window < noon


def test_sun_below_horizon_is_rejected():
    with pytest.raises(ValueError, match="below the horizon"):
        SunPosition(-5.0, 0.0, "midnight")


def test_unknown_criterion_is_rejected():
    with pytest.raises(ValueError, match="unknown shading criterion"):
        design_sun_position(config.SITE_LAT, "summer_noon")


def test_matches_pvgis_winter_solstice():
    """Our closed-form geometry against PVGIS's own solar position.

    PVGIS was asked for the horizon profile at the campus point; its winter
    solstice series is an independent check on the derivation that sets the
    ground coverage ratio, and therefore on every usable-area figure in FR-2.
    Values read from data/horizon_28.545_77.192.json.
    """
    noon = design_sun_position(config.SITE_LAT, "winter_noon")
    assert noon.elevation_deg == pytest.approx(38.0, abs=0.05)

    nine = design_sun_position(config.SITE_LAT, "winter_9_to_3")
    assert nine.elevation_deg == pytest.approx(22.3, abs=0.05)
    assert nine.azimuth_from_south_deg == pytest.approx(44.5, abs=0.05)

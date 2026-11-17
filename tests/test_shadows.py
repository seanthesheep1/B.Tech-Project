"""The shadow geometry, and the tile arithmetic underneath it.

None of this touches the network. The image-measurement half of
``shadows.py`` is exercised against small synthetic arrays rather than against
Esri, so the tests say whether the arithmetic is right, not whether a service
is up.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from btp_solar import basemap, config, shadows
from btp_solar.solar_geometry import declination, solar_elevation

OCTOBER_23 = 296  # day of year of the Esri capture


# --- tile arithmetic -----------------------------------------------------


@pytest.mark.parametrize(
    "lon,lat",
    [(77.192, 28.545), (0.0, 0.0), (-122.4, 37.8), (139.7, 35.7), (18.4, -33.9)],
)
def test_pixel_round_trip(lon, lat):
    for zoom in (12, 17, 19):
        x, y = basemap.lonlat_to_pixel(lon, lat, zoom)
        back_lon, back_lat = basemap.pixel_to_lonlat(x, y, zoom)
        assert back_lon == pytest.approx(lon, abs=1e-9)
        assert back_lat == pytest.approx(lat, abs=1e-9)


def test_latitude_outside_mercator_is_refused():
    with pytest.raises(ValueError, match="Web Mercator"):
        basemap.lonlat_to_pixel(0.0, 89.0, 19)


def test_zoom_19_is_the_resolution_the_census_was_planned_around():
    assert basemap.metres_per_pixel(config.SITE_LAT, 19) == pytest.approx(0.262, abs=0.002)


def test_resolution_halves_with_each_zoom_level():
    a = basemap.metres_per_pixel(config.SITE_LAT, 18)
    b = basemap.metres_per_pixel(config.SITE_LAT, 19)
    assert a / b == pytest.approx(2.0)


def test_pixels_increase_eastward_and_southward():
    """y runs down in image space; getting this backwards flips every shadow."""
    x0, y0 = basemap.lonlat_to_pixel(77.0, 28.6, 19)
    x1, _ = basemap.lonlat_to_pixel(77.1, 28.6, 19)
    _, y1 = basemap.lonlat_to_pixel(77.0, 28.5, 19)
    assert x1 > x0
    assert y1 > y0


# --- solar geometry ------------------------------------------------------


@pytest.mark.parametrize("hour_angle", [-75, -60, -45, -30, -15, 15, 30, 45, 60])
def test_azimuth_and_hour_angle_invert_each_other(hour_angle):
    dec = declination(OCTOBER_23)
    azimuth = shadows.compass_azimuth(config.SITE_LAT, dec, hour_angle)
    recovered = shadows.hour_angle_for_azimuth(
        azimuth, config.SITE_LAT, dec, morning=hour_angle < 0
    )
    assert recovered == pytest.approx(hour_angle, abs=1e-3)


def test_morning_sun_is_east_and_afternoon_sun_is_west():
    dec = declination(OCTOBER_23)
    assert shadows.compass_azimuth(config.SITE_LAT, dec, -45.0) < 180.0
    assert shadows.compass_azimuth(config.SITE_LAT, dec, 45.0) > 180.0


def test_an_unreachable_azimuth_is_refused_rather_than_fudged():
    dec = declination(OCTOBER_23)
    with pytest.raises(ValueError, match="not reached"):
        shadows.hour_angle_for_azimuth(5.0, config.SITE_LAT, dec, morning=True)


def test_shadows_at_this_latitude_all_point_north_in_october():
    """The constraint the whole method leans on, asserted rather than assumed."""
    allowed = set(shadows.northward_bearings(config.SITE_LAT, declination(OCTOBER_23)))
    assert 0 in allowed and 350 in allowed and 20 in allowed
    assert 180 not in allowed and 150 not in allowed and 210 not in allowed


def test_height_from_shadow_inverts_shadow_length():
    from btp_solar.fr3_shading import shadow_length

    for height in (1.0, 3.0, 7.5, 24.5):
        for elevation in (20.0, 35.0, 49.0):
            assert shadows.height_from_shadow(
                shadow_length(height, elevation), elevation
            ) == pytest.approx(height)


def test_height_from_shadow_refuses_a_sun_below_the_horizon():
    with pytest.raises(ValueError, match="between 0 and 90"):
        shadows.height_from_shadow(3.0, 0.0)


def test_the_sun_never_clears_fifty_degrees_here_in_late_october():
    """Why a 3 m object must cast at least 2.5 m, which is what made the
    absence of any shadow in the Esri scene conclusive rather than suggestive."""
    noon = solar_elevation(config.SITE_LAT, declination(OCTOBER_23), 0.0)
    assert noon < 50.0
    assert 3.0 / math.tan(math.radians(noon)) > 2.5


# --- circular statistics -------------------------------------------------


def test_circular_mean_crosses_north_without_landing_on_south():
    mean, concentration = shadows.circular_mean([350.0, 10.0])
    assert mean == pytest.approx(0.0, abs=1e-6) or mean == pytest.approx(360.0, abs=1e-6)
    assert concentration > 0.98


def test_opposed_bearings_report_no_concentration():
    _, concentration = shadows.circular_mean([0.0, 180.0])
    assert concentration == pytest.approx(0.0, abs=1e-9)


def test_weights_pull_the_mean_toward_the_stronger_shadow():
    mean, _ = shadows.circular_mean([0.0, 90.0], [9.0, 1.0])
    assert 0.0 < mean < 20.0


def test_empty_and_mismatched_inputs_are_refused():
    with pytest.raises(ValueError):
        shadows.circular_mean([])
    with pytest.raises(ValueError):
        shadows.circular_mean([10.0, 20.0], [1.0])


# --- scene solving -------------------------------------------------------


def test_scene_sun_recovers_a_sun_position_from_the_shadows_it_would_cast():
    dec = declination(OCTOBER_23)
    truth = -30.0
    azimuth = shadows.compass_azimuth(config.SITE_LAT, dec, truth)
    bearing = (azimuth + 180.0) % 360.0
    sun = shadows.solve_scene_sun("2025-10-23", [bearing - 2, bearing, bearing + 2])
    assert sun.hour_angle_deg == pytest.approx(truth, abs=0.5)
    assert sun.elevation_deg == pytest.approx(
        solar_elevation(config.SITE_LAT, dec, truth), abs=0.5
    )
    assert sun.trustworthy
    assert sun.morning is True


def test_scene_sun_picks_the_afternoon_branch_from_the_bearings_alone():
    dec = declination(OCTOBER_23)
    azimuth = shadows.compass_azimuth(config.SITE_LAT, dec, 30.0)
    sun = shadows.solve_scene_sun("2025-10-23", [(azimuth + 180.0) % 360.0])
    assert sun.morning is False
    assert sun.hour_angle_deg == pytest.approx(30.0, abs=0.5)


def test_scattered_bearings_report_as_untrustworthy():
    """Bearings spread round the compass carry no time, and say so.

    Note that 350, 20 and 60 would *not* be scattered: they agree to within a
    season's worth of sun. Genuine scatter has to span the circle, which is
    exactly what the unconstrained search produced on the real roofs.
    """
    sun = shadows.solve_scene_sun("2025-10-23", [10.0, 100.0, 190.0, 280.0])
    assert sun.concentration < shadows.MIN_BEARING_CONCENTRATION
    assert not sun.trustworthy


def test_solar_time_converts_to_ist_against_the_825_meridian():
    # Delhi sits west of the IST meridian, so clock time runs ahead of sun time.
    assert shadows.solar_time_to_ist(12.0) > 12.0
    assert shadows.solar_time_to_ist(12.0) == pytest.approx(
        12.0 + (82.5 - config.SITE_LON) / 15.0
    )


# --- image measurement ---------------------------------------------------


def _scene(bearing_deg: float, shadow_px: int = 12, size: int = 81):
    """A bright field, a dark square, and a shadow running off it."""
    grey = np.full((size, size), 240.0)
    centre = size // 2
    half = 4
    grey[centre - half:centre + half + 1, centre - half:centre + half + 1] = 90.0
    dx, dy = shadows._direction(bearing_deg)
    for step in range(1, shadow_px + 1):
        for across in range(-half, half + 1):
            x = centre + dx * (half + step) - dy * across
            y = centre + dy * (half + step) + dx * across
            if 0 <= int(y) < size and 0 <= int(x) < size:
                grey[int(y), int(x)] = 95.0
    outline = [
        (centre - half, centre - half), (centre + half, centre - half),
        (centre + half, centre + half), (centre - half, centre + half),
    ]
    return grey, (float(centre), float(centre)), outline


@pytest.mark.parametrize("bearing", [0.0, 45.0, 315.0, 90.0])
def test_darkest_lobe_finds_the_shadow_it_was_given(bearing):
    grey, centre, outline = _scene(bearing)
    found, lobe, roof = shadows.darkest_lobe_bearing(grey, centre, outline, 0.262)
    assert abs(((found - bearing + 180) % 360) - 180) <= 10
    assert roof == pytest.approx(240.0, abs=1.0)
    assert roof - lobe > shadows.MIN_SHADOW_CONTRAST


def test_extent_along_tracks_an_elongated_outline():
    """A single radius would start the search inside the object along the long
    axis and well clear of it along the short one - the bug that scattered the
    first run's bearings."""
    outline = [(0.0, -2.0), (30.0, -2.0), (30.0, 2.0), (0.0, 2.0)]
    centre = (15.0, 0.0)
    assert shadows.extent_along(outline, centre, 90.0) == pytest.approx(15.0)
    assert shadows.extent_along(outline, centre, 0.0) == pytest.approx(2.0)


def test_shadow_run_measures_the_length_laid_down():
    bearing, shadow_px = 0.0, 12
    grey, centre, outline = _scene(bearing, shadow_px=shadow_px)
    mpp = 0.262
    reach = shadows.extent_along(outline, centre, bearing)
    run = shadows.shadow_run(grey, centre, reach, bearing, mpp, 240.0, 145.0)
    assert run == pytest.approx(shadow_px * mpp, rel=0.25)


def test_shadow_run_stops_at_the_edge_of_the_roof():
    grey, centre, outline = _scene(0.0, shadow_px=12)
    mask = np.zeros_like(grey, dtype=bool)
    mask[:, :] = True
    mask[: int(centre[1]) - 4, :] = False  # roof ends at the object's own edge
    reach = shadows.extent_along(outline, centre, 0.0)
    run = shadows.shadow_run(
        grey, centre, reach, 0.0, 0.262, 240.0, 145.0, roof_mask=mask
    )
    assert run == 0.0


def test_a_direction_with_too_little_roof_to_sample_casts_no_vote():
    grey, centre, outline = _scene(0.0)
    mask = np.zeros_like(grey, dtype=bool)
    found, _, _ = shadows.darkest_lobe_bearing(
        grey, centre, outline, 0.262, roof_mask=mask
    )
    assert math.isnan(found)

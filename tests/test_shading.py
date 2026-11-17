"""FR-3 shading geometry, checked against derivations done by hand.

Every case here has an answer that can be worked out on paper, which is the
point: the shading model replaces a GUI plugin whose output could not be
tested, so the replacement has to earn that by being checkable.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from btp_solar import config, fr3_shading

# An observer standing at the origin: the box the sampling density is set from.
HERE = (-1.0, -1.0, 1.0, 1.0)


def wall(distance: float, height: float, bearing: str = "north") -> fr3_shading.Caster:
    """A long wall at a given distance from the origin, on one side."""
    spans = {
        "north": [(-60, distance), (60, distance), (60, distance + 2), (-60, distance + 2)],
        "south": [(-60, -distance), (60, -distance), (60, -distance - 2), (-60, -distance - 2)],
        "east": [(distance, -60), (distance, 60), (distance + 2, 60), (distance + 2, -60)],
    }
    return fr3_shading.Caster(bearing, height, spans[bearing])


# --- the geometry --------------------------------------------------------

def test_a_wall_subtends_the_angle_trigonometry_says_it_does():
    """A 10 m wall 10 m away stands at 45 degrees. No model needed to know that."""
    cloud = fr3_shading.caster_points([wall(10.0, 10.0)], near=HERE)
    horizon = fr3_shading.horizon_profile((0.0, 0.0, 0.0), cloud)
    assert horizon[0] == pytest.approx(45.0, abs=0.5)

    cloud = fr3_shading.caster_points([wall(20.0, 10.0)], near=HERE)
    horizon = fr3_shading.horizon_profile((0.0, 0.0, 0.0), cloud)
    assert horizon[0] == pytest.approx(math.degrees(math.atan2(10, 20)), abs=0.5)


def test_azimuth_is_measured_clockwise_from_north_like_pvlib():
    """If this convention slips, every shadow lands on the wrong side."""
    north = fr3_shading.horizon_profile(
        (0.0, 0.0, 0.0), fr3_shading.caster_points([wall(10.0, 10.0, "north")], near=HERE))
    assert north[0] > 40.0 and north[180] == 0.0

    south = fr3_shading.horizon_profile(
        (0.0, 0.0, 0.0), fr3_shading.caster_points([wall(10.0, 10.0, "south")], near=HERE))
    assert south[180] > 40.0 and south[0] == 0.0

    east = fr3_shading.horizon_profile(
        (0.0, 0.0, 0.0), fr3_shading.caster_points([wall(10.0, 10.0, "east")], near=HERE))
    assert east[90] > 40.0 and east[270] == 0.0


def test_something_shorter_than_the_observer_casts_nothing_on_it():
    """A roof is not shaded by a building whose top is below it."""
    cloud = fr3_shading.caster_points([wall(10.0, 5.0)], near=HERE)
    horizon = fr3_shading.horizon_profile((0.0, 0.0, 8.0), cloud)
    assert horizon.max() == 0.0


def test_an_open_site_has_a_flat_horizon_and_a_full_sky():
    horizon = fr3_shading.horizon_profile((0.0, 0.0, 0.0), np.zeros((0, 3)))
    assert horizon.max() == 0.0
    assert fr3_shading.sky_view_factor(horizon) == pytest.approx(1.0)


def test_the_sky_view_factor_falls_as_walls_close_in():
    heights = [0.0, 5.0, 10.0, 20.0]
    factors = []
    for h in heights:
        casters = [wall(10.0, h, b) for b in ("north", "south", "east")] if h else []
        cloud = fr3_shading.caster_points(casters, near=HERE) if casters else np.zeros((0, 3))
        factors.append(fr3_shading.sky_view_factor(
            fr3_shading.horizon_profile((0.0, 0.0, 0.0), cloud)))
    assert factors == sorted(factors, reverse=True)
    assert factors[0] == pytest.approx(1.0)
    assert factors[-1] < 0.8, "three close walls must take a visible bite out of the sky"


def test_one_long_wall_matches_an_independent_integration():
    """The sky view factor computed a second way, without the horizon code.

    For a wall of height h whose nearest point is d away, the azimuth phi
    measured from the perpendicular sees it at a distance d/cos(phi), so its
    elevation is atan(h*cos(phi)/d). Integrating cos^2 of that over the half
    of the sky containing the wall, and 1 over the rest, is the answer this
    module should arrive at by a different route.
    """
    d, h, half_length = 10.0, 10.0, 60.0
    total = 0.0
    for degree in range(360):
        # angle away from the wall's perpendicular, in (-180, 180]
        offset = math.radians(((degree + 180) % 360) - 180)
        along = d * math.tan(offset) if abs(offset) < math.pi / 2 else float("inf")
        if abs(offset) < math.pi / 2 and abs(along) <= half_length:
            elevation = math.atan2(h, math.hypot(along, d))
            total += math.cos(elevation) ** 2
        else:
            total += 1.0   # the wall ends; open sky beyond it
    expected = total / 360.0

    horizon = fr3_shading.horizon_profile(
        (0.0, 0.0, 0.0), fr3_shading.caster_points([wall(d, h)], near=HERE))
    assert fr3_shading.sky_view_factor(horizon) == pytest.approx(expected, abs=0.02)


def test_a_courtyard_of_known_proportions_matches_the_closed_form():
    """Four walls of height h at distance d: each azimuth sees atan(h/d) at the
    closest approach, so the sky view factor is bounded by cos^2 of that."""
    h, d = 10.0, 10.0
    casters = [wall(d, h, b) for b in ("north", "south", "east")]
    horizon = fr3_shading.horizon_profile(
        (0.0, 0.0, 0.0), fr3_shading.caster_points(casters))
    svf = fr3_shading.sky_view_factor(horizon)
    assert math.cos(math.radians(45.0)) ** 2 < svf < 1.0


# --- the sunlit test -----------------------------------------------------

def test_the_sun_must_clear_the_horizon_to_reach_the_point():
    cloud = fr3_shading.caster_points([wall(10.0, 10.0)], near=HERE)
    horizons = fr3_shading.horizon_profile((0.0, 0.0, 0.0), cloud)[None, :]
    assert fr3_shading.sunlit_fraction(horizons, 0.0, 44.0) == 0.0
    assert fr3_shading.sunlit_fraction(horizons, 0.0, 46.0) == 1.0


def test_a_sun_below_the_horizon_is_never_counted_as_sunlit():
    horizons = np.zeros((4, 360))
    assert fr3_shading.sunlit_fraction(horizons, 180.0, -5.0) == 0.0
    series = fr3_shading.sunlit_fraction_series(horizons, [180.0], [-5.0])
    assert series[0] == 0.0


def test_partial_shading_is_reported_as_a_fraction():
    """Half the sampled points behind a wall is a shading factor of 0.5, not 0
    and not 1. Roofs are rarely all-or-nothing in winter."""
    cloud = fr3_shading.caster_points([wall(5.0, 10.0)], near=HERE)
    near = fr3_shading.horizon_profile((0.0, 0.0, 0.0), cloud)
    far = fr3_shading.horizon_profile((0.0, -200.0, 0.0), cloud)
    horizons = np.array([near, near, far, far])
    assert fr3_shading.sunlit_fraction(horizons, 0.0, 30.0) == pytest.approx(0.5)


def test_the_series_and_the_single_hour_agree():
    cloud = fr3_shading.caster_points([wall(10.0, 10.0)], near=HERE)
    horizons = np.array([fr3_shading.horizon_profile((0.0, 0.0, 0.0), cloud)])
    azimuths = [0.0, 90.0, 180.0, 0.0]
    elevations = [44.0, 30.0, 30.0, 46.0]
    series = fr3_shading.sunlit_fraction_series(horizons, azimuths, elevations)
    for i, (az, el) in enumerate(zip(azimuths, elevations)):
        assert series[i] == pytest.approx(fr3_shading.sunlit_fraction(horizons, az, el))


# --- the supporting pieces ----------------------------------------------

def test_densify_fills_in_long_walls():
    """Corners alone leave the azimuths between them unshaded."""
    square = [(0, 0), (20, 0), (20, 20), (0, 20)]
    assert len(fr3_shading.densify(square, spacing=2.0)) > len(square) * 5
    assert len(fr3_shading.densify(square, spacing=100.0)) == 4


def test_densify_rejects_a_spacing_that_would_not_terminate():
    with pytest.raises(ValueError, match="spacing must be positive"):
        fr3_shading.densify([(0, 0), (1, 1), (2, 0)], spacing=0.0)


def test_the_sample_grid_stays_inside_the_polygon():
    from shapely.geometry import Point, Polygon

    polygon = Polygon([(0, 0), (40, 0), (40, 40), (0, 40)])
    points = fr3_shading.sample_grid(polygon, spacing=5.0)
    assert len(points) > 20
    assert all(polygon.contains(Point(x, y)) for x, y in points)


def test_a_roof_smaller_than_the_grid_still_gets_one_point():
    from shapely.geometry import Polygon

    tiny = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    assert len(fr3_shading.sample_grid(tiny, spacing=5.0)) == 1


def test_the_sample_grid_avoids_a_hole():
    from shapely.geometry import Point, Polygon

    donut = Polygon([(0, 0), (40, 0), (40, 40), (0, 40)],
                    [[(15, 15), (25, 15), (25, 25), (15, 25)]])
    points = fr3_shading.sample_grid(donut, spacing=2.0)
    assert not any(Point(x, y).within(Polygon([(15, 15), (25, 15), (25, 25), (15, 25)]))
                   for x, y in points)


# --- the analytic shadow path, which the acceptance check uses -----------

def test_shadow_length_matches_the_hand_derivation():
    assert fr3_shading.shadow_length(10.0, 45.0) == pytest.approx(10.0)
    assert fr3_shading.shadow_length(10.0, 30.0) == pytest.approx(10.0 / math.tan(math.radians(30)))


def test_a_sun_on_the_horizon_has_no_defined_shadow():
    with pytest.raises(ValueError, match="below the horizon"):
        fr3_shading.shadow_length(10.0, 0.0)


def test_obstruction_heights_are_declared_for_every_type_digitised():
    """A type drawn in Part 4 with no height here would silently cast nothing."""
    drawn = {"water_tank", "stair_room", "solar_panel", "other", "open_air"}
    assert drawn <= set(config.OBSTRUCTION_HEIGHTS_M)
    assert config.OBSTRUCTION_HEIGHTS_M["open_air"] == 0.0, "a hole casts no shadow"


# --- the sampling-density bug, pinned --------------------------------------

def test_a_wall_leaves_no_holes_in_the_horizon():
    """The regression test for a bug that quietly understated every shadow.

    An outline is reduced to points, and if consecutive points land more than
    one azimuth bin apart the horizon acquires gaps: bins reading open sky in
    the middle of a solid wall. The sun then shines through a building. It is
    invisible in the output - the shading loss simply comes out too small.
    """
    # The wall faces east, so the arc it covers runs from about 10 to 170
    # degrees without wrapping past north, and a plain min-to-max walk
    # describes it correctly.
    cloud = fr3_shading.caster_points([wall(10.0, 10.0, "east")], near=HERE)
    horizon = fr3_shading.horizon_profile((0.0, 0.0, 0.0), cloud)

    obstructed = np.nonzero(horizon)[0]
    assert len(obstructed) > 100, "a 120 m wall 10 m away should fill many azimuths"
    assert obstructed.min() > 5 and obstructed.max() < 355, "the arc must not wrap"

    holes = [b for b in range(obstructed.min(), obstructed.max() + 1) if horizon[b] == 0.0]
    assert not holes, f"{len(holes)} empty bins inside a solid wall: {holes[:10]}"


def test_spacing_shrinks_with_distance():
    """Close objects need finer sampling; distant ones do not."""
    assert fr3_shading.spacing_for(100.0) > fr3_shading.spacing_for(10.0)
    assert fr3_shading.spacing_for(0.1) >= 0.02, "must not demand unbounded points"

    # At any distance a sample point can actually be, two adjacent samples
    # stay inside one azimuth bin. The 1 m setback keeps points off the
    # parapet, so below about 1.2 m the guarantee is not needed.
    for distance in (1.5, 10.0, 50.0, 300.0):
        step_deg = math.degrees(fr3_shading.spacing_for(distance) / distance)
        assert step_deg <= 360.0 / config.HORIZON_BINS


def test_a_close_wall_is_sampled_more_finely_than_a_far_one():
    near_box = (-1.0, -1.0, 1.0, 1.0)
    close = len(fr3_shading.caster_points([wall(5.0, 10.0)], near=near_box))
    far = len(fr3_shading.caster_points([wall(200.0, 10.0)], near=near_box))
    assert close > far

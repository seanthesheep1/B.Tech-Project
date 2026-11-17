"""Obstruction heights measured from the shadows they cast.

``config.OBSTRUCTION_HEIGHTS_M`` has until now been six assumed numbers - 3.0 m
for a water tank, 3.0 for a stair room, 4.0 for a lift room - and roof clutter
is about 85% of the modelled shading loss. So those six numbers carry more of
FR-3 than anything else in the model, and not one of them was measured. Roof
access is not permitted, so the measurement has to come from the imagery.

The method, and the one trick in it
-----------------------------------
An object's height follows from the length of its shadow and the sun's
elevation: ``h = L * tan(alpha)``. The date is recorded - 2025-10-23, see
``data/imagery_provenance.json`` - which fixes the declination. What Esri does
not record is the *time*, and without the time there is no elevation.

The time does not have to be assumed. Every shadow in one scene points the same
way, and that direction is the sun's azimuth reflected. So:

1. take the direction of the darkest lobe around each obstruction,
2. keep the ones where the roof is bright enough for a shadow to show at all,
3. take the circular mean, which is the scene's shadow bearing,
4. solve for the hour angle that puts the sun at the opposite azimuth,
5. and read the elevation off that hour angle.

Bearing and length are independent measurements of the same shadow, so using
the bearing to fix the time leaves the length free to do the measuring. Nothing
is circular, and nothing rests on an orbital assumption about when WorldView-2
passes overhead.

The consensus step matters. A single obstruction's dark lobe can be a stain, a
patch of different roofing, or a neighbour's shadow. Twenty of them agreeing on
one bearing cannot be any of those things, and the concentration statistic says
how strongly they agree, so a weak scene reports as weak rather than as a
number.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import config
from .solar_geometry import declination, solar_azimuth_from_south, solar_elevation

#: Below this grey-level contrast against the surrounding roof, a dark lobe is
#: not taken as a shadow. Set from the spread seen on these roofs: genuine
#: shadows on a bright roof run 60 to 135 levels down, stains run under 20.
MIN_SHADOW_CONTRAST = 25.0

#: Below this circular concentration the bearings disagree too much to carry a
#: time. 1.0 is perfect agreement, 0.0 is random.
MIN_BEARING_CONCENTRATION = 0.55

#: Objects that cast nothing worth measuring, so they never vote on the bearing.
NON_CASTERS = frozenset({"open_air"})


def northward_bearings(
    latitude: float = config.SITE_LAT,
    declination_deg: float = -12.28,
    step_deg: int = 5,
    margin_deg: float = 10.0,
) -> list[int]:
    """Bearings a shadow can physically take on this day at this latitude.

    When the sun's declination is south of the latitude it never crosses the
    zenith's north side, so every shadow in the scene points somewhere north.
    The extremes are set by sunrise and sunset azimuth.

    This is a constraint from the sky, not a fit. Without it the darkest
    direction around an obstruction is as likely to be a stain, a neighbouring
    plant room or a parapet edge as a shadow, and the bearings scatter: on
    these roofs the unconstrained search returned a concentration of 0.21,
    which is noise, while the constrained one returns 0.82.
    """
    phi, dec = math.radians(latitude), math.radians(declination_deg)
    cos_gamma = -math.sin(dec) / math.cos(phi)
    if abs(cos_gamma) > 1.0:  # pragma: no cover - polar day or night
        raise ValueError("the sun does not rise and set normally here on this day")
    gamma = math.degrees(math.acos(max(-1.0, min(1.0, cos_gamma))))
    # Sun runs from azimuth 180-gamma at sunrise to 180+gamma at sunset, so
    # shadows run from (360-gamma) through north to gamma.
    limit = gamma + margin_deg
    return [a % 360 for a in range(-int(limit), int(limit) + 1, step_deg)]


def compass_azimuth(
    latitude: float, declination_deg: float, hour_angle_deg: float
) -> float:
    """Solar azimuth clockwise from true north.

    ``solar_azimuth_from_south`` returns an unsigned angle away from south;
    the hour angle says which side of south that is. Morning is east.
    """
    gamma = solar_azimuth_from_south(latitude, declination_deg, hour_angle_deg)
    return (180.0 - gamma) % 360.0 if hour_angle_deg < 0 else (180.0 + gamma) % 360.0


def hour_angle_for_azimuth(
    target_azimuth_deg: float,
    latitude: float,
    declination_deg: float,
    morning: bool = True,
) -> float:
    """The hour angle that puts the sun at this compass azimuth.

    Solved by bisection rather than inverted analytically: the azimuth
    expression is monotonic across a half day, and bisection cannot pick the
    wrong branch the way an arccos can.
    """
    target = target_azimuth_deg % 360.0
    lo, hi = (-89.9, -0.1) if morning else (0.1, 89.9)

    def error(h: float) -> float:
        diff = (compass_azimuth(latitude, declination_deg, h) - target + 180.0) % 360.0
        return diff - 180.0

    e_lo, e_hi = error(lo), error(hi)
    if e_lo * e_hi > 0:
        raise ValueError(
            f"azimuth {target_azimuth_deg:.1f} deg is not reached on the "
            f"{'morning' if morning else 'afternoon'} side of this day"
        )
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if error(lo) * error(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


def circular_mean(
    bearings_deg: list[float], weights: list[float] | None = None
) -> tuple[float, float]:
    """Mean direction and concentration of a set of bearings.

    Returns ``(mean_bearing, R)``. R near 1 means they agree; near 0 means they
    point every which way and the mean is meaningless. Averaging 350 and 10
    arithmetically gives 180, which is why this exists.
    """
    if not bearings_deg:
        raise ValueError("no bearings to average")
    if weights is None:
        weights = [1.0] * len(bearings_deg)
    if len(weights) != len(bearings_deg):
        raise ValueError("weights and bearings are different lengths")
    total = sum(weights)
    if total <= 0:
        raise ValueError("weights sum to zero")
    s = sum(w * math.sin(math.radians(b)) for b, w in zip(bearings_deg, weights))
    c = sum(w * math.cos(math.radians(b)) for b, w in zip(bearings_deg, weights))
    return math.degrees(math.atan2(s, c)) % 360.0, math.hypot(s, c) / total


def height_from_shadow(shadow_m: float, sun_elevation_deg: float) -> float:
    """Height of the object that cast this shadow on flat ground."""
    if shadow_m < 0:
        raise ValueError("shadow length cannot be negative")
    if not 0.0 < sun_elevation_deg < 90.0:
        raise ValueError(
            f"sun elevation {sun_elevation_deg} is not between 0 and 90 degrees"
        )
    return shadow_m * math.tan(math.radians(sun_elevation_deg))


@dataclass(frozen=True)
class SceneSun:
    """Where the sun stood when the scene was captured."""

    date: str
    day_of_year: int
    declination_deg: float
    shadow_bearing_deg: float
    concentration: float
    sun_azimuth_deg: float
    hour_angle_deg: float
    elevation_deg: float
    solar_time_hours: float
    votes: int
    morning: bool

    @property
    def trustworthy(self) -> bool:
        return self.concentration >= MIN_BEARING_CONCENTRATION


def solve_scene_sun(
    date_iso: str,
    bearings_deg: list[float],
    weights: list[float] | None = None,
    latitude: float = config.SITE_LAT,
    morning: bool | None = None,
) -> SceneSun:
    """Turn a set of shadow bearings into the sun position that made them."""
    import datetime

    day = datetime.date.fromisoformat(date_iso)
    doy = day.timetuple().tm_yday
    dec = declination(doy)

    bearing, concentration = circular_mean(bearings_deg, weights)
    sun_az = (bearing + 180.0) % 360.0

    # Confidence is checked before the geometry, not after. Bearings that
    # disagree average to a direction no sun ever occupied, and asking for the
    # hour angle of an impossible azimuth raises - which would turn "these
    # shadows do not agree" into a crash. A scene that cannot be solved should
    # report that it cannot be solved.
    if concentration < MIN_BEARING_CONCENTRATION:
        return SceneSun(
            date=date_iso, day_of_year=doy, declination_deg=dec,
            shadow_bearing_deg=bearing, concentration=concentration,
            sun_azimuth_deg=sun_az, hour_angle_deg=float("nan"),
            elevation_deg=float("nan"), solar_time_hours=float("nan"),
            votes=len(bearings_deg), morning=bool(morning) if morning is not None else False,
        )

    if morning is None:
        # Shadows north-west mean the sun is south-east, so morning; shadows
        # north-east mean an afternoon pass. The scene says which, not a guess
        # about the satellite's orbit.
        morning = sun_az < 180.0
    hour_angle = hour_angle_for_azimuth(sun_az, latitude, dec, morning=morning)
    elevation = solar_elevation(latitude, dec, hour_angle)

    return SceneSun(
        date=date_iso,
        day_of_year=doy,
        declination_deg=dec,
        shadow_bearing_deg=bearing,
        concentration=concentration,
        sun_azimuth_deg=sun_az,
        hour_angle_deg=hour_angle,
        elevation_deg=elevation,
        solar_time_hours=12.0 + hour_angle / 15.0,
        votes=len(bearings_deg),
        morning=morning,
    )


def solar_time_to_ist(solar_time_hours: float, longitude: float = config.SITE_LON) -> float:
    """Local solar time to Indian Standard Time, whose meridian is 82.5 E."""
    return solar_time_hours + (82.5 - longitude) / 15.0


# --- image measurement ----------------------------------------------------
# Kept apart from the geometry above so the geometry can be tested without a
# network, an image, or a dependency on Pillow.


def _direction(bearing_deg: float) -> tuple[float, float]:
    """Unit step in image pixels for a compass bearing. Image y runs down."""
    return math.sin(math.radians(bearing_deg)), -math.cos(math.radians(bearing_deg))


def extent_along(outline_px, centre_px: tuple[float, float], bearing_deg: float) -> float:
    """How far an outline reaches from its centre along a bearing, in pixels.

    The support function of the polygon. A single circular radius is wrong for
    anything but a circle: on an elongated stair-room block it starts the
    search metres clear of the object across the short axis and still inside it
    along the long one, which is enough to scatter the bearings beyond use.
    """
    dx, dy = _direction(bearing_deg)
    cx, cy = centre_px
    return max(((px - cx) * dx + (py - cy) * dy) for px, py in outline_px)


def _on_roof(mask, x: float, y: float) -> bool:
    """Is this pixel inside the roof we are allowed to measure on?"""
    if mask is None:
        return True
    row, col = int(y), int(x)
    if not (0 <= row < mask.shape[0] and 0 <= col < mask.shape[1]):
        return False
    return bool(mask[row, col])


def darkest_lobe_bearing(
    grey,
    centre_px: tuple[float, float],
    outline_px,
    metres_per_pixel: float,
    reach_m: float = 5.0,
    step_deg: int = 5,
    roof_mask=None,
    min_samples: int = 4,
    allowed: list[int] | None = None,
) -> tuple[float, float, float]:
    """Direction of the darkest band just outside an object.

    Returns ``(bearing, lobe_mean, roof_level)``. The roof level is the 70th
    percentile of a ring well outside the object, which ignores the shadow lobe
    itself without needing to know where it is.

    ``roof_mask`` confines every sample to the roof. Without it the darkest
    direction from an obstruction near a parapet is simply *off the roof*,
    where the ground is tree canopy: that is darker than any shadow and wins
    every time.

    The search in each direction starts at the outline's own extent in that
    direction, not at a single radius - see :func:`extent_along`.
    """
    import numpy as np

    cx, cy = centre_px
    h, w = grey.shape

    ring = []
    for angle in range(0, 360, 3):
        dx, dy = _direction(angle)
        base = extent_along(outline_px, centre_px, angle) * metres_per_pixel
        for metres in (8.0, 10.0, 12.0, 14.0, 16.0):
            d = base + metres
            px, py = cx + dx * d / metres_per_pixel, cy + dy * d / metres_per_pixel
            if 0 <= int(py) < h and 0 <= int(px) < w and _on_roof(roof_mask, px, py):
                ring.append(grey[int(py), int(px)])
    roof_level = float(np.percentile(ring, 70)) if ring else float("nan")

    best_bearing, best_value = float("nan"), float("inf")
    for angle in (allowed if allowed is not None else range(0, 360, step_deg)):
        dx, dy = _direction(angle)
        base = extent_along(outline_px, centre_px, angle) * metres_per_pixel
        samples = []
        metres = 0.4
        while metres < reach_m:
            d = base + metres
            px, py = cx + dx * d / metres_per_pixel, cy + dy * d / metres_per_pixel
            if 0 <= int(py) < h and 0 <= int(px) < w and _on_roof(roof_mask, px, py):
                samples.append(grey[int(py), int(px)])
            metres += metres_per_pixel
        if len(samples) >= min_samples:
            value = float(np.mean(samples))
            if value < best_value:
                best_bearing, best_value = float(angle), value

    return best_bearing, best_value, roof_level


def shadow_run(
    grey,
    centre_px: tuple[float, float],
    radius_px: float,
    bearing_deg: float,
    metres_per_pixel: float,
    roof_level: float,
    contrast: float,
    max_m: float = 14.0,
    roof_mask=None,
) -> float:
    """How far the shadow runs from the object's edge along the bearing.

    Walks outward and stops where brightness climbs back to within half the
    measured contrast of the roof. The half is deliberate: a shadow's edge is
    blurred by the sensor, so the midpoint of the ramp is a better estimate of
    the true edge than either end of it.
    """
    cx, cy = centre_px
    h, w = grey.shape
    dx, dy = _direction(bearing_deg)
    cutoff = roof_level - contrast / 2.0

    run = 0.0
    metres = 0.0
    recovered = 0
    while metres < max_m:
        d = radius_px * metres_per_pixel + metres
        px, py = cx + dx * d / metres_per_pixel, cy + dy * d / metres_per_pixel
        if not (0 <= int(py) < h and 0 <= int(px) < w):
            break
        if not _on_roof(roof_mask, px, py):
            break  # ran off the roof; whatever is beyond is not this shadow
        if grey[int(py), int(px)] >= cutoff:
            recovered += 1
            if recovered >= 2:  # two in a row, so one bright pixel is not an edge
                break
        else:
            recovered = 0
            run = metres
        metres += metres_per_pixel
    return run

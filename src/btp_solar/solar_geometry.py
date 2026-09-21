"""Solar position and row-spacing geometry.

Pure trigonometry with no heavy dependencies, so the inter-row spacing
derivation that FR-2 demands can be reproduced, tested and defended by hand.
pvlib is used elsewhere for the full hourly chain; these closed forms exist so
the single design number - the ground coverage ratio - is transparent.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

WINTER_SOLSTICE_DECLINATION_DEG = -23.44


def declination(day_of_year: int) -> float:
    """Solar declination in degrees (Cooper's equation)."""
    return WINTER_SOLSTICE_DECLINATION_DEG * math.cos(
        math.radians(360.0 * (day_of_year + 10) / 365.25)
    )


def solar_elevation(latitude: float, declination_deg: float, hour_angle_deg: float) -> float:
    """Solar elevation in degrees.

    hour_angle_deg is 0 at solar noon and -15 deg per hour before it.
    """
    phi, dec, h = map(math.radians, (latitude, declination_deg, hour_angle_deg))
    sin_alpha = math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.cos(h)
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_alpha))))


def solar_azimuth_from_south(
    latitude: float, declination_deg: float, hour_angle_deg: float
) -> float:
    """Absolute solar azimuth measured from true south, in degrees."""
    phi, dec = math.radians(latitude), math.radians(declination_deg)
    alpha = math.radians(solar_elevation(latitude, declination_deg, hour_angle_deg))
    denom = math.cos(alpha) * math.cos(phi)
    if abs(denom) < 1e-9:
        return 0.0
    cos_gamma = (math.sin(alpha) * math.sin(phi) - math.sin(dec)) / denom
    return math.degrees(math.acos(max(-1.0, min(1.0, cos_gamma))))


@dataclass(frozen=True)
class SunPosition:
    """The worst-case sun position a row spacing must clear."""

    elevation_deg: float
    azimuth_from_south_deg: float
    label: str

    def __post_init__(self) -> None:
        if self.elevation_deg <= 0.0:
            raise ValueError(
                f"sun is below the horizon at {self.label!r}; no spacing can clear it"
            )


def design_sun_position(latitude: float, criterion: str) -> SunPosition:
    """The sun position used as the no-shading design point.

    'winter_noon'   : solar noon on the winter solstice, the lowest noon sun.
    'winter_9_to_3' : 09:00 solar time on the winter solstice, i.e. the start of
                      the six-hour window that is conventionally kept clear.
    """
    dec = WINTER_SOLSTICE_DECLINATION_DEG
    if criterion == "winter_noon":
        hour_angle = 0.0
    elif criterion == "winter_9_to_3":
        hour_angle = -45.0  # three hours before solar noon
    else:
        raise ValueError(f"unknown shading criterion {criterion!r}")

    return SunPosition(
        elevation_deg=solar_elevation(latitude, dec, hour_angle),
        azimuth_from_south_deg=solar_azimuth_from_south(latitude, dec, hour_angle),
        label=criterion,
    )


def row_pitch_ratio(tilt_deg: float, sun: SunPosition) -> float:
    """Row pitch as a multiple of module length along the slope.

    A row of modules of slope length L tilted at beta stands h = L sin(beta)
    above the roof and occupies L cos(beta) of horizontal depth. Its shadow
    reaches h / tan(alpha) along the solar azimuth; the component normal to the
    rows, which is what sets the pitch, is that length times cos(gamma).

        pitch / L = cos(beta) + sin(beta) cos(gamma) / tan(alpha)
    """
    beta = math.radians(tilt_deg)
    alpha = math.radians(sun.elevation_deg)
    gamma = math.radians(sun.azimuth_from_south_deg)
    return math.cos(beta) + math.sin(beta) * math.cos(gamma) / math.tan(alpha)


def ground_coverage_ratio(tilt_deg: float, sun: SunPosition) -> float:
    """Module glass area divided by the ground area of the array field.

    This is the number that replaces the "assume 40 to 50 percent" rule of
    thumb the specification explicitly rules out.
    """
    if tilt_deg == 0.0:
        return 1.0
    return 1.0 / row_pitch_ratio(tilt_deg, sun)

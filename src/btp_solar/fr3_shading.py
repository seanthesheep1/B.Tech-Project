"""FR-3: shading analysis.

Week 6. Extrude the corrected footprints to a digital surface model using the
height estimates from FR-1, add parapets and tree canopy, and derive an hourly
shading factor per roof across a full year.

The heavy lifting is done by the UMEP plugin inside QGIS rather than in this
package; the functions here prepare its inputs, read its outputs back into the
register, and run the FR-3 acceptance check against a shadow measured in dated
satellite imagery.
"""

from __future__ import annotations

import math
from pathlib import Path

from . import config
from .solar_geometry import declination, solar_elevation


def shadow_length(height_m: float, sun_elevation_deg: float) -> float:
    """Length of the shadow cast by a vertical object on level ground."""
    if sun_elevation_deg <= 0:
        raise ValueError("the sun is below the horizon; no shadow is defined")
    return height_m / math.tan(math.radians(sun_elevation_deg))


def expected_shadow_length(
    height_m: float,
    day_of_year: int,
    hour_angle_deg: float,
    latitude: float = config.SITE_LAT,
) -> float:
    """Shadow length to compare against one measured in a dated image.

    This is the FR-3 validation path: pick a satellite image with a known
    acquisition date and time, measure a shadow on it, and compare.
    """
    elevation = solar_elevation(latitude, declination(day_of_year), hour_angle_deg)
    return shadow_length(height_m, elevation)


def build_digital_surface_model(footprints_path: Path, out_path: Path):  # pragma: no cover
    """Rasterise footprint height to a DSM for UMEP. Implement in week 6."""
    raise NotImplementedError(
        "Week 6: extrude footprints by building height to a DSM raster. "
        "Inputs are the corrected footprints from FR-1 and the storey counts "
        "recorded in week 3; add parapet height before extruding."
    )


def hourly_shading_factor(roof_id: str, umep_output: Path):  # pragma: no cover
    """Read UMEP's per-roof irradiance back into an hourly shading factor."""
    raise NotImplementedError(
        "Week 6: shading factor is UMEP shaded irradiance divided by the "
        "unshaded plane-of-array irradiance for the same hour."
    )

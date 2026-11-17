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
from dataclasses import dataclass
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


# --- the shading model ---------------------------------------------------
# Rather than rasterise a digital surface model and march rays across it hour
# by hour, the geometry is reduced once to a **horizon profile** per sample
# point: the highest obstruction elevation in each one-degree ring of azimuth.
# After that a point is sunlit at any moment simply when the sun stands higher
# than its horizon in the sun's own direction, which turns 8,760 ray traces
# into 8,760 array lookups.
#
# This replaces the UMEP plugin named in the workflow. UMEP runs inside the
# QGIS GUI, its output cannot be regenerated from a script, and it cannot be
# unit-tested - all three of which conflict with this project's rule that
# every number regenerates from raw data through a named script. The trade is
# that the model here is a vertical-prism approximation: buildings are flat
# tops on a flat campus, which the PVGIS horizon profile supports.


@dataclass(frozen=True)
class Caster:
    """A shade-casting object: a footprint and the height of its top."""

    name: str
    top_z: float
    outline: list[tuple[float, float]]


def densify(ring: list[tuple[float, float]], spacing: float = 2.0) -> list[tuple[float, float]]:
    """Add points along each edge so a long wall is not sampled only at corners.

    A building is represented by points on its outline, so an un-densified
    50 m wall would be two points and would leave the azimuths between them
    unshaded.
    """
    if spacing <= 0:
        raise ValueError("spacing must be positive")
    out: list[tuple[float, float]] = []
    for (x0, y0), (x1, y1) in zip(ring, list(ring[1:]) + [ring[0]]):
        out.append((x0, y0))
        length = math.hypot(x1 - x0, y1 - y0)
        for i in range(1, int(length // spacing)):
            f = i * spacing / length
            out.append((x0 + f * (x1 - x0), y0 + f * (y1 - y0)))
    return out


def spacing_for(distance_m: float, bins: int = config.HORIZON_BINS) -> float:
    """How finely to sample an outline that is this far from the observer.

    An outline is reduced to points, and consecutive points must land no more
    than one azimuth bin apart or the horizon acquires **holes** - bins that
    read as open sky in the middle of a wall, which lets the sun through where
    a building actually blocks it and quietly understates the shading.

    The azimuth step between two points ``s`` apart at distance ``r`` is
    ``s / r`` radians, so the spacing has to scale with distance. Half a bin is
    used for margin, and the result is floored so a very close object does not
    demand an unbounded number of points.
    """
    bin_rad = 2.0 * math.pi / bins
    # The floor keeps a very close object from demanding unbounded points. It
    # holds the guarantee down to about 1.2 m, and the 1 m setback means no
    # sample point sits closer than that to the parapet.
    return max(0.02, distance_m * bin_rad / 2.0)


def caster_points(casters: list[Caster], spacing: float | None = None, near=None):
    """Every caster reduced to an (x, y, top_z) point cloud.

    With ``near`` set to the bounding box of the roof being sampled, each
    caster is densified according to how close it comes to that roof, which is
    the worst case for any sample point on it. A fixed ``spacing`` overrides
    this and is used by the tests.
    """
    import numpy as np

    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for caster in casters:
        if spacing is not None:
            step = spacing
        else:
            step = spacing_for(_distance_to_box(caster.outline, near))
        for x, y in densify(caster.outline, step):
            xs.append(x)
            ys.append(y)
            zs.append(caster.top_z)
    if not xs:
        return np.zeros((0, 3))
    return np.column_stack([np.array(xs), np.array(ys), np.array(zs)])


def _distance_to_box(outline: list[tuple[float, float]], box) -> float:
    """Closest approach between an outline and a bounding box, zero if inside.

    Measured to the **edges**, not the corners. A long wall running past the
    observer has its nearest point in the middle of a segment, and judging it
    by its far-away corners would sample it too coarsely - which puts holes
    back in the horizon exactly where the wall is closest and matters most.
    """
    if box is None:
        return 50.0
    from shapely.geometry import LinearRing
    from shapely.geometry import box as make_box

    return float(LinearRing(outline).distance(make_box(*box)))


def horizon_profile(
    point: tuple[float, float, float],
    cloud,
    bins: int = config.HORIZON_BINS,
    radius: float = config.CASTER_RADIUS_M,
):
    """Highest obstruction elevation in each azimuth bin, seen from one point.

    Azimuth is measured clockwise from north, matching pvlib's convention, so
    a solar azimuth can index the result directly.
    """
    import numpy as np

    horizon = np.zeros(bins)
    if len(cloud) == 0:
        return horizon

    px, py, pz = point
    dx = cloud[:, 0] - px
    dy = cloud[:, 1] - py
    distance = np.hypot(dx, dy)

    rise = cloud[:, 2] - pz
    keep = (rise > 0.0) & (distance > 0.1) & (distance <= radius)
    if not keep.any():
        return horizon

    elevation = np.degrees(np.arctan2(rise[keep], distance[keep]))
    azimuth = np.degrees(np.arctan2(dx[keep], dy[keep])) % 360.0
    index = np.minimum((azimuth / (360.0 / bins)).astype(int), bins - 1)

    np.maximum.at(horizon, index, elevation)
    return horizon


def sky_view_factor(horizon) -> float:
    """Fraction of the isotropic sky an unobstructed horizontal surface would see.

    Integrating isotropic radiance over the visible sky gives cos^2 of the
    horizon elevation in each azimuth, normalised so an open site is 1.0.
    Applied to the diffuse component; the beam is handled geometrically.
    """
    import numpy as np

    return float(np.mean(np.cos(np.radians(horizon)) ** 2))


def sunlit_fraction(horizons, sun_azimuth: float, sun_elevation: float) -> float:
    """Fraction of a roof's sample points that can see the sun right now.

    This is the beam shading factor: 1.0 is unshaded, 0.0 fully shaded. Partial
    values are real - half a roof in shadow is the normal mid-winter case.
    """
    import numpy as np

    if sun_elevation <= 0:
        return 0.0
    bins = horizons.shape[1]
    index = min(int(sun_azimuth % 360.0 / (360.0 / bins)), bins - 1)
    return float(np.mean(sun_elevation > horizons[:, index]))


def sunlit_fraction_series(horizons, azimuths, elevations):
    """``sunlit_fraction`` across a whole year of sun positions at once.

    Done by counting rather than comparing. Sorting each azimuth column of the
    horizon once turns "how many sample points stand below this sun" into a
    binary search, so ten years of hourly positions cost 360 searches instead
    of one comparison per point per hour.
    """
    import numpy as np

    bins = horizons.shape[1]
    azimuths = np.asarray(azimuths, dtype=float)
    elevations = np.asarray(elevations, dtype=float)

    index = np.minimum((azimuths % 360.0 / (360.0 / bins)).astype(int), bins - 1)
    ordered = np.sort(horizons, axis=0)
    n_points = horizons.shape[0]

    lit = np.zeros(len(elevations))
    for b in np.unique(index):
        hours = index == b
        lit[hours] = np.searchsorted(ordered[:, b], elevations[hours], side="left") / n_points
    return np.where(elevations > 0, lit, 0.0)


def sample_grid(polygon, spacing: float = config.SHADING_SAMPLE_SPACING_M):
    """A grid of points over a polygon, used to sample one roof's array area."""
    from shapely.geometry import Point

    min_x, min_y, max_x, max_y = polygon.bounds
    points = []
    y = min_y + spacing / 2.0
    while y < max_y:
        x = min_x + spacing / 2.0
        while x < max_x:
            if polygon.contains(Point(x, y)):
                points.append((x, y))
            x += spacing
        y += spacing
    if not points:  # a roof smaller than the grid still needs one point
        centre = polygon.representative_point()
        points.append((centre.x, centre.y))
    return points


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

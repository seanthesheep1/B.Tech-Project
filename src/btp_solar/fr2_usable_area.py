"""FR-2: roof characterisation and usable area.

The area chain, in the order the report must present it:

    gross roof area
      - obstruction footprint (tanks, stair rooms, AC plant, lift rooms, SWH)
      - setback strip around the roof perimeter
      = net available area
      x ground coverage ratio   (derived, see solar_geometry)
      x packing factor          (walkways, inverter pads)
      = module glass area
      x module power density
      = installable capacity

Each intermediate value is written to the register as its own column so any
final figure can be traced back to the polygon it came from.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

from . import config
from .solar_geometry import design_sun_position, ground_coverage_ratio


@dataclass(frozen=True)
class RoofMeasurements:
    """What is digitised in QGIS for one building, in metres and square metres."""

    building_id: str
    gross_roof_area_m2: float
    obstruction_area_m2: float
    roof_perimeter_m: float

    def __post_init__(self) -> None:
        if self.gross_roof_area_m2 <= 0:
            raise ValueError(f"{self.building_id}: gross roof area must be positive")
        if self.obstruction_area_m2 < 0:
            raise ValueError(f"{self.building_id}: obstruction area cannot be negative")
        if self.obstruction_area_m2 > self.gross_roof_area_m2:
            raise ValueError(
                f"{self.building_id}: obstructions ({self.obstruction_area_m2:.1f} m2) "
                f"exceed the roof ({self.gross_roof_area_m2:.1f} m2); check the digitising"
            )
        if self.roof_perimeter_m <= 0:
            raise ValueError(f"{self.building_id}: perimeter must be positive")


@dataclass(frozen=True)
class UsableAreaResult:
    building_id: str
    gross_roof_area_m2: float
    obstruction_area_m2: float
    setback_area_m2: float
    net_available_area_m2: float
    ground_coverage_ratio: float
    packing_factor: float
    module_area_m2: float
    installable_capacity_kwp: float
    usable_fraction_of_roof: float
    design_sun_elevation_deg: float
    design_criterion: str

    def as_row(self) -> dict[str, float | str]:
        return asdict(self)


def setback_area(perimeter_m: float, gross_area_m2: float, setback_m: float) -> float:
    """Area of the clearance strip inside the roof edge.

    For a polygon eroded by a distance s the removed area is approximately
    P*s - pi*s^2 for convex corners, exact for a rectangle up to the corner
    terms. Where the QGIS negative buffer is available its measured area should
    be used in preference to this estimate; this exists so the register can be
    populated before the buffering is done, and as a cross-check afterwards.
    """
    if setback_m <= 0:
        return 0.0
    strip = perimeter_m * setback_m - math.pi * setback_m**2
    return max(0.0, min(strip, gross_area_m2))


def compute(
    roof: RoofMeasurements,
    *,
    tilt_deg: float = config.MODULE_TILT_DEG,
    setback_m: float = config.SETBACK_M,
    packing_factor: float = config.PACKING_FACTOR,
    power_density_w_per_m2: float = config.MODULE_POWER_DENSITY_W_PER_M2,
    criterion: str = config.SHADING_CRITERION,
    latitude: float = config.SITE_LAT,
    measured_setback_area_m2: float | None = None,
) -> UsableAreaResult:
    """Run the full area chain for one roof.

    Pass ``measured_setback_area_m2`` when the negative buffer has been computed
    in QGIS; the analytic estimate is then bypassed.
    """
    sun = design_sun_position(latitude, criterion)
    gcr = ground_coverage_ratio(tilt_deg, sun)

    strip = (
        measured_setback_area_m2
        if measured_setback_area_m2 is not None
        else setback_area(roof.roof_perimeter_m, roof.gross_roof_area_m2, setback_m)
    )

    net = roof.gross_roof_area_m2 - roof.obstruction_area_m2 - strip
    if net <= 0:
        raise ValueError(
            f"{roof.building_id}: nothing left after obstructions and setback; "
            "the roof is too small or too cluttered to host an array"
        )

    module_area = net * gcr * packing_factor
    capacity_kwp = module_area * power_density_w_per_m2 / 1000.0

    return UsableAreaResult(
        building_id=roof.building_id,
        gross_roof_area_m2=roof.gross_roof_area_m2,
        obstruction_area_m2=roof.obstruction_area_m2,
        setback_area_m2=strip,
        net_available_area_m2=net,
        ground_coverage_ratio=gcr,
        packing_factor=packing_factor,
        module_area_m2=module_area,
        installable_capacity_kwp=capacity_kwp,
        usable_fraction_of_roof=module_area / roof.gross_roof_area_m2,
        design_sun_elevation_deg=sun.elevation_deg,
        design_criterion=criterion,
    )

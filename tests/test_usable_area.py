"""The FR-2 area chain."""

from __future__ import annotations

import math

import pytest

from btp_solar import config, fr2_usable_area
from btp_solar.fr2_usable_area import RoofMeasurements


def square_roof(side: float = 40.0, obstructions: float = 60.0) -> RoofMeasurements:
    return RoofMeasurements(
        building_id="TEST",
        gross_roof_area_m2=side * side,
        obstruction_area_m2=obstructions,
        roof_perimeter_m=4 * side,
    )


def test_setback_area_of_a_square_matches_the_geometry():
    """A 40 m square eroded by 1 m loses 1600 - 38^2 = 156 m2."""
    computed = fr2_usable_area.setback_area(perimeter_m=160.0, gross_area_m2=1600.0, setback_m=1.0)
    assert computed == pytest.approx(160.0 - math.pi, abs=0.01)
    assert computed == pytest.approx(1600.0 - 38.0**2, rel=0.02)


def test_zero_setback_removes_nothing():
    assert fr2_usable_area.setback_area(160.0, 1600.0, 0.0) == 0.0


def test_area_chain_is_internally_consistent():
    result = fr2_usable_area.compute(square_roof())
    assert result.net_available_area_m2 == pytest.approx(
        result.gross_roof_area_m2 - result.obstruction_area_m2 - result.setback_area_m2
    )
    assert result.module_area_m2 == pytest.approx(
        result.net_available_area_m2 * result.ground_coverage_ratio * result.packing_factor
    )
    assert result.installable_capacity_kwp == pytest.approx(
        result.module_area_m2 * config.MODULE_POWER_DENSITY_W_PER_M2 / 1000.0
    )


def test_usable_fraction_lands_in_the_expected_band():
    """The derivation should land near the 40-50 per cent rule of thumb.

    Not a proof of either, but a disagreement here means one of the two is
    wrong and it needs explaining before the number goes in the report.
    """
    result = fr2_usable_area.compute(square_roof())
    assert 0.35 <= result.usable_fraction_of_roof <= 0.60


def test_measured_setback_overrides_the_estimate():
    result = fr2_usable_area.compute(square_roof(), measured_setback_area_m2=200.0)
    assert result.setback_area_m2 == 200.0


def test_obstructions_larger_than_the_roof_are_rejected():
    with pytest.raises(ValueError, match="exceed the roof"):
        RoofMeasurements("BAD", gross_roof_area_m2=100.0, obstruction_area_m2=150.0,
                         roof_perimeter_m=40.0)


def test_negative_area_is_rejected():
    with pytest.raises(ValueError, match="must be positive"):
        RoofMeasurements("BAD", gross_roof_area_m2=-1.0, obstruction_area_m2=0.0,
                         roof_perimeter_m=40.0)


def test_a_roof_with_nothing_left_is_rejected_loudly():
    tiny = RoofMeasurements("TINY", gross_roof_area_m2=20.0, obstruction_area_m2=18.0,
                            roof_perimeter_m=40.0)
    with pytest.raises(ValueError, match="too small or too cluttered"):
        fr2_usable_area.compute(tiny)

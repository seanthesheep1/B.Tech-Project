"""The acceptance criteria of the specification, as executable checks.

Section 2 of the functional specification attaches one criterion to each
module and requires sign-off before the next module begins. Each function here
returns a CheckResult so a module can be signed off from a script rather than
by assertion in prose.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import config


@dataclass(frozen=True)
class CheckResult:
    ref: str
    name: str
    passed: bool
    detail: str

    def __str__(self) -> str:
        return f"[{'PASS' if self.passed else 'FAIL'}] {self.ref} {self.name}: {self.detail}"


def _relative_gap(a: float, b: float) -> float:
    mean = (a + b) / 2.0
    if mean == 0:
        raise ValueError("cannot compare two zero quantities")
    return abs(a - b) / mean


def fr1_irradiance_agreement(
    pvgis_annual_ghi: float,
    nasa_annual_ghi: float,
    tol: float = config.IRRADIANCE_AGREEMENT_TOL,
) -> CheckResult:
    """FR-1: the two irradiance sources agree on annual GHI within 5 per cent."""
    gap = _relative_gap(pvgis_annual_ghi, nasa_annual_ghi)
    return CheckResult(
        "FR-1",
        "irradiance source agreement",
        gap <= tol,
        f"PVGIS {pvgis_annual_ghi:.0f} vs NASA POWER {nasa_annual_ghi:.0f} kWh/m2/yr, "
        f"gap {gap:.1%} against a {tol:.0%} tolerance",
    )


def fr2_segmentation_iou(iou: float, threshold: float = config.SEGMENTATION_MIN_IOU) -> CheckResult:
    """FR-2: segmentation IoU of at least 0.75 against manual ground truth."""
    return CheckResult(
        "FR-2",
        "segmentation accuracy",
        iou >= threshold,
        f"IoU {iou:.3f} against a {threshold:.2f} threshold",
    )


def fr3_shadow_length(
    modelled_m: float, observed_m: float, tol: float = config.SHADOW_LENGTH_TOL
) -> CheckResult:
    """FR-3: modelled shadow within 15 per cent of one measured in dated imagery."""
    gap = _relative_gap(modelled_m, observed_m)
    return CheckResult(
        "FR-3",
        "shadow geometry validation",
        gap <= tol,
        f"modelled {modelled_m:.1f} m vs observed {observed_m:.1f} m, "
        f"gap {gap:.1%} against a {tol:.0%} tolerance",
    )


def fr4_specific_yield(
    specific_yield: float, bounds: tuple[float, float] = config.SPECIFIC_YIELD_RANGE
) -> CheckResult:
    """FR-4: specific yield falls in the plausible band for Delhi."""
    low, high = bounds
    return CheckResult(
        "FR-4",
        "specific yield plausibility",
        low <= specific_yield <= high,
        f"{specific_yield:.0f} kWh/kWp/yr against a {low:.0f} to {high:.0f} band",
    )


def fr4_pvgis_agreement(
    modelled: float, pvgis: float, tol: float = config.PVGIS_AGREEMENT_TOL
) -> CheckResult:
    """FR-4: within 10 per cent of the PVGIS estimate for a reference building."""
    gap = _relative_gap(modelled, pvgis)
    return CheckResult(
        "FR-4",
        "PVGIS cross-check",
        gap <= tol,
        f"modelled {modelled:.0f} vs PVGIS {pvgis:.0f} kWh/kWp/yr, "
        f"gap {gap:.1%} against a {tol:.0%} tolerance",
    )


def fr5_base_case_calibration(
    modelled_kwh: float, billed_kwh: float, tol: float = config.FEEDER_LOADING_TOL
) -> CheckResult:
    """FR-5: base-case transformer loading reproduces billed consumption within 15 per cent."""
    gap = _relative_gap(modelled_kwh, billed_kwh)
    return CheckResult(
        "FR-5",
        "feeder base-case calibration",
        gap <= tol,
        f"modelled {modelled_kwh:.0f} vs billed {billed_kwh:.0f} kWh, "
        f"gap {gap:.1%} against a {tol:.0%} tolerance",
    )

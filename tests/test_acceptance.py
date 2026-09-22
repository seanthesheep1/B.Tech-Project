"""The specification's acceptance criteria, at and either side of the threshold."""

from __future__ import annotations

import pytest

from btp_solar import acceptance


def test_irradiance_agreement_passes_inside_five_percent():
    assert acceptance.fr1_irradiance_agreement(1900.0, 1940.0).passed


def test_irradiance_agreement_fails_outside_five_percent():
    result = acceptance.fr1_irradiance_agreement(1900.0, 2100.0)
    assert not result.passed
    assert "10.0%" in result.detail


def test_segmentation_iou_threshold_is_inclusive():
    assert acceptance.fr2_segmentation_iou(0.75).passed
    assert not acceptance.fr2_segmentation_iou(0.749).passed


def test_shadow_length_tolerance():
    assert acceptance.fr3_shadow_length(20.0, 21.0).passed
    assert not acceptance.fr3_shadow_length(20.0, 30.0).passed


def test_specific_yield_band_for_delhi():
    assert acceptance.fr4_specific_yield(1450.0).passed
    assert not acceptance.fr4_specific_yield(1250.0).passed
    assert not acceptance.fr4_specific_yield(1700.0).passed


def test_pvgis_cross_check():
    assert acceptance.fr4_pvgis_agreement(1500.0, 1560.0).passed
    assert not acceptance.fr4_pvgis_agreement(1500.0, 1800.0).passed


def test_feeder_calibration():
    assert acceptance.fr5_base_case_calibration(1.0e6, 1.1e6).passed
    assert not acceptance.fr5_base_case_calibration(1.0e6, 1.5e6).passed


def test_result_renders_readably():
    text = str(acceptance.fr4_specific_yield(1450.0))
    assert text.startswith("[PASS] FR-4")


# --- FR-1 shape comparison -------------------------------------------------

from btp_solar import fr1_data  # noqa: E402


def test_normalised_shape_sums_to_one():
    assert sum(fr1_data.normalised_shape([1.0, 2.0, 3.0, 4.0])) == pytest.approx(1.0)


def test_normalised_shape_is_scale_invariant():
    """Doubling every month must not change the shape - this is what makes the
    measured-generation arbitration independent of unknown plant capacity."""
    a = fr1_data.normalised_shape([1.0, 2.0, 3.0])
    b = fr1_data.normalised_shape([2.0, 4.0, 6.0])
    assert a == pytest.approx(b)


def test_empty_series_is_rejected():
    with pytest.raises(ValueError, match="empty or negative"):
        fr1_data.normalised_shape([0.0, 0.0])


def test_shape_error_is_zero_for_identical_series():
    s = fr1_data.normalised_shape([3.0, 1.0, 2.0])
    assert fr1_data.shape_error(s, s) == pytest.approx(0.0)


def test_shape_error_rejects_mismatched_lengths():
    with pytest.raises(ValueError, match="same length"):
        fr1_data.shape_error([0.5, 0.5], [0.3, 0.3, 0.4])

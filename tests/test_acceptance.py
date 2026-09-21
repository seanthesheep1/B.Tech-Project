"""The specification's acceptance criteria, at and either side of the threshold."""

from __future__ import annotations

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

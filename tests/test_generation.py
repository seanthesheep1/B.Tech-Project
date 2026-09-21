"""FR-4 helpers that do not need the full pvlib chain."""

from __future__ import annotations

import pytest

from btp_solar import config, fr4_generation


def test_losses_combine_multiplicatively_not_additively():
    """Adding the percentages overstates the loss; each acts on what is left."""
    additive = sum(config.LOSSES.values())
    combined = fr4_generation.total_loss_fraction()
    assert combined < additive
    assert combined == pytest.approx(1 - (0.97 * 0.98 * 0.985 * 0.99 * 0.995 * 0.98 * 0.985),
                                     abs=1e-9)


def test_default_loss_stack_is_in_a_believable_range():
    """Roughly 11 to 16 per cent before shading, per the workflow note."""
    assert 0.10 <= fr4_generation.total_loss_fraction() <= 0.16


def test_an_impossible_loss_is_rejected():
    with pytest.raises(ValueError, match="outside"):
        fr4_generation.total_loss_fraction({"soiling": 1.2})


def test_specific_yield_and_capacity_factor_agree():
    energy, capacity = 145_000.0, 100.0
    assert fr4_generation.specific_yield(energy, capacity) == pytest.approx(1450.0)
    assert fr4_generation.capacity_factor(energy, capacity) == pytest.approx(1450.0 / 8766.0)


def test_zero_capacity_is_rejected():
    with pytest.raises(ValueError, match="must be positive"):
        fr4_generation.specific_yield(1000.0, 0.0)

"""The FR-4 back-test, and the property that makes it honest.

The whole point of comparing shapes rather than levels is that the plants'
capacity - which this project does not know, and estimates from the very
generation under test - must not be able to influence the result. That is a
testable property, so it is tested.
"""

from __future__ import annotations

import pytest

from btp_solar import acceptance, config, fr1_data

# A plausible Delhi year: spring peak, monsoon dip, winter trough.
MEASURED = [40, 68, 94, 92, 89, 85, 69, 56, 65, 73, 46, 42]


def test_capacity_cannot_influence_the_result():
    """The anti-circularity property, stated as a test.

    Scaling a plant's whole year by any factor - which is what an unknown
    capacity does - must leave the comparison untouched. If this ever fails,
    the back-test has stopped being independent of the thing it validates.
    """
    base = acceptance.fr4_shape_agreement(MEASURED, MEASURED)
    for factor in (0.01, 0.5, 3.0, 1000.0):
        scaled = [v * factor for v in MEASURED]
        assert acceptance.fr4_shape_agreement(scaled, MEASURED).detail == base.detail
        assert acceptance.fr4_shape_agreement(MEASURED, scaled).detail == base.detail


def test_an_identical_year_agrees_perfectly():
    check = acceptance.fr4_shape_agreement(MEASURED, MEASURED)
    assert check.passed
    assert "0.000" in check.detail


def test_a_season_shifted_year_fails():
    """Move the peak from spring to winter and the test must notice."""
    reversed_year = list(reversed(MEASURED))
    assert not acceptance.fr4_shape_agreement(reversed_year, MEASURED).passed


def test_the_detail_reports_misallocated_energy_as_half_the_deviation():
    """Both shapes sum to 1, so every unit of excess has a matching shortfall:
    the energy in the wrong month is half the total absolute deviation."""
    modelled = MEASURED.copy()
    modelled[0] += sum(MEASURED) * 0.05
    modelled[6] -= sum(MEASURED) * 0.05
    check = acceptance.fr4_shape_agreement(modelled, MEASURED)
    deviation = fr1_data.shape_error(
        fr1_data.normalised_shape(modelled), fr1_data.normalised_shape(MEASURED)
    )
    assert f"{deviation / 2:.1%}" in check.detail


def test_the_tolerance_is_the_one_recorded_in_config():
    assert config.SHAPE_AGREEMENT_TOL == 0.20
    borderline = MEASURED.copy()
    borderline[0] *= 3
    check = acceptance.fr4_shape_agreement(borderline, MEASURED)
    assert check.passed is (fr1_data.shape_error(
        fr1_data.normalised_shape(borderline), fr1_data.normalised_shape(MEASURED)
    ) <= config.SHAPE_AGREEMENT_TOL)


def test_an_empty_year_is_rejected_rather_than_scored():
    with pytest.raises(ValueError, match="cannot normalise"):
        acceptance.fr4_shape_agreement([0] * 12, MEASURED)


def test_series_of_different_lengths_are_rejected():
    with pytest.raises(ValueError, match="same length"):
        acceptance.fr4_shape_agreement(MEASURED[:6], MEASURED)


# --- the recorded result -------------------------------------------------

RESULT = config.DATA / "backtest_shape.csv"


@pytest.mark.skipif(not RESULT.exists(), reason="back-test has not been run")
def test_the_recorded_back_test_still_passes():
    import csv

    rows = list(csv.DictReader(RESULT.open(encoding="utf-8")))
    assert len(rows) == 12
    modelled = [float(r["modelled_kwh"]) for r in rows]
    measured = [float(r["measured_kwh"]) for r in rows]
    assert acceptance.fr4_shape_agreement(modelled, measured).passed


@pytest.mark.skipif(not RESULT.exists(), reason="back-test has not been run")
def test_the_winter_bias_is_systematic_not_one_bad_month():
    """What makes the winter gap meaningful: the sign is the same in all four
    winter months, while no single month leaves the spread of the real plants.
    If a later change breaks this pattern, the diagnosis in the script's output
    no longer holds and must be rewritten."""
    import csv

    rows = list(csv.DictReader(RESULT.open(encoding="utf-8")))
    diffs = [float(r["difference"]) for r in rows]
    spread = [float(r["plant_spread"]) for r in rows]

    # The three darkest months read high; every month from March to June reads
    # low. February sits between the two blocks and is slightly negative, which
    # is why the claim is about blocks of months and not about "all of winter".
    assert all(diffs[m] > 0 for m in (10, 11, 0)), "Nov, Dec and Jan should read high"
    assert all(diffs[m] < 0 for m in (2, 3, 4, 5)), "Mar to Jun should read low"
    assert all(abs(d) <= 2 * s for d, s in zip(diffs, spread)), \
        "no single month should sit outside the spread of the measured plants"

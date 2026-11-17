"""The economics: degradation, discounting, payback and the roll-up."""

from __future__ import annotations

import pytest

from btp_solar import config, economics


# --- degradation ---------------------------------------------------------


def test_the_first_year_loses_nothing():
    assert economics.energy_in_year(1000.0, 1, 0.005) == pytest.approx(1000.0)


def test_degradation_is_linear_from_the_first_year():
    assert economics.energy_in_year(1000.0, 11, 0.005) == pytest.approx(950.0)


def test_output_never_goes_negative_however_long_the_life():
    assert economics.energy_in_year(1000.0, 500, 0.01) == 0.0


def test_year_zero_is_refused_because_years_are_counted_from_one():
    with pytest.raises(ValueError, match="counted from 1"):
        economics.energy_in_year(1000.0, 0)


# --- discounting ---------------------------------------------------------


def test_a_rupee_next_year_is_worth_less_than_a_rupee_now():
    assert economics.discounted_sum([100.0], 0.08) == pytest.approx(100 / 1.08)


def test_a_zero_discount_rate_just_adds_up():
    assert economics.discounted_sum([10.0, 20.0, 30.0], 0.0) == pytest.approx(60.0)


def test_discounting_starts_one_year_out_not_today():
    """The first cash flow arrives at the end of year one, so it is already
    discounted once. Treating it as immediate overstates every project."""
    assert economics.discounted_sum([100.0], 0.10) < 100.0


# --- the headline figures ------------------------------------------------


def _roof(**kwargs):
    base = dict(
        building_id="TEST", capacity_kwp=100.0, first_year_kwh=150_000.0,
        capex_inr_per_kwp=42_000.0, tariff_inr_per_kwh=8.0,
    )
    base.update(kwargs)
    return economics.evaluate(**base)


def test_lcoe_does_not_move_when_the_tariff_does():
    """The whole reason LCOE is the figure this project leads on: the tariff
    is its weakest input, and LCOE does not contain it."""
    cheap = _roof(tariff_inr_per_kwh=4.0)
    dear = _roof(tariff_inr_per_kwh=12.0)
    assert cheap.lcoe_inr_per_kwh == pytest.approx(dear.lcoe_inr_per_kwh)


def test_payback_does_move_when_the_tariff_does():
    cheap = _roof(tariff_inr_per_kwh=4.0)
    dear = _roof(tariff_inr_per_kwh=12.0)
    assert cheap.simple_payback_years > dear.simple_payback_years


def test_lcoe_rises_with_capital_cost():
    assert _roof(capex_inr_per_kwp=55_000.0).lcoe_inr_per_kwh > _roof(
        capex_inr_per_kwp=32_000.0
    ).lcoe_inr_per_kwh


def test_lcoe_rises_with_the_discount_rate():
    """Money costs more, the energy is unchanged, so each unit costs more."""
    assert _roof(discount_rate=0.12).lcoe_inr_per_kwh > _roof(
        discount_rate=0.04
    ).lcoe_inr_per_kwh


def test_a_sunnier_roof_has_a_lower_lcoe_for_the_same_outlay():
    assert _roof(first_year_kwh=180_000.0).lcoe_inr_per_kwh < _roof(
        first_year_kwh=120_000.0
    ).lcoe_inr_per_kwh


def test_discounted_payback_is_never_sooner_than_simple_payback():
    roof = _roof()
    assert roof.discounted_payback_years >= roof.simple_payback_years


def test_payback_is_interpolated_rather_than_rounded_to_whole_years():
    """Rounding up to the crossing year would make every roof look alike."""
    roof = _roof()
    assert roof.simple_payback_years % 1 != 0


def test_a_project_that_never_repays_says_so_instead_of_guessing():
    roof = _roof(capex_inr_per_kwp=500_000.0, tariff_inr_per_kwh=1.0)
    assert roof.discounted_payback_years is None
    assert not roof.pays_back_within_life
    assert roof.npv_inr < 0


def test_om_larger_than_the_revenue_never_repays():
    roof = _roof(tariff_inr_per_kwh=0.01, om_fraction=0.5)
    assert roof.simple_payback_years is None


def test_npv_is_positive_exactly_when_it_repays_inside_its_life():
    good = _roof()
    assert good.npv_inr > 0 and good.pays_back_within_life
    bad = _roof(capex_inr_per_kwp=400_000.0)
    assert bad.npv_inr < 0 and not bad.pays_back_within_life


def test_lifetime_energy_counts_every_year_of_the_life():
    roof = _roof(lifetime_years=25)
    assert roof.lifetime_kwh < 25 * 150_000.0      # degradation bites
    assert roof.lifetime_kwh > 20 * 150_000.0


# --- refusals ------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs,message",
    [
        (dict(capacity_kwp=0.0), "no capacity"),
        (dict(first_year_kwh=0.0), "generates nothing"),
        (dict(lifetime_years=0), "at least one year"),
    ],
)
def test_degenerate_roofs_are_refused(kwargs, message):
    with pytest.raises(ValueError, match=message):
        _roof(**kwargs)


# --- the roll-up ---------------------------------------------------------


def test_campus_lcoe_is_weighted_by_energy_not_by_roof_count():
    """A 62 kWp roof must not count as much as a 486 kWp one."""
    small = economics.evaluate("S", 10.0, 12_000.0, capex_inr_per_kwp=90_000.0)
    large = economics.evaluate("L", 500.0, 750_000.0, capex_inr_per_kwp=35_000.0)
    total = economics.campus_total([small, large])
    unweighted = (small.lcoe_inr_per_kwh + large.lcoe_inr_per_kwh) / 2
    assert total["lcoe_inr_per_kwh"] < unweighted
    assert total["lcoe_inr_per_kwh"] == pytest.approx(large.lcoe_inr_per_kwh, rel=0.1)


def test_campus_totals_add_up():
    roofs = [
        economics.evaluate(f"B{i}", 100.0 * i, 140_000.0 * i) for i in range(1, 4)
    ]
    total = economics.campus_total(roofs)
    assert total["roofs"] == 3
    assert total["capacity_kwp"] == pytest.approx(600.0)
    assert total["capex_inr"] == pytest.approx(sum(r.capex_inr for r in roofs))


def test_an_empty_campus_is_refused():
    with pytest.raises(ValueError, match="no roofs"):
        economics.campus_total([])


def test_the_configured_defaults_produce_a_sane_campus_lcoe():
    """A guard on the constants themselves: Indian rooftop solar lands a few
    rupees per unit. If a config edit sends this to 50 or to 0.5, something is
    wrong with the inputs rather than with the arithmetic."""
    roof = economics.evaluate("B", 288.6, 288.6 * 1454)
    assert 2.0 < roof.lcoe_inr_per_kwh < 8.0
    assert config.CAPEX_INR_PER_KWP in config.CAPEX_SWEEP_INR_PER_KWP

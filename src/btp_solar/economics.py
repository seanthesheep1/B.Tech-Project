"""What the energy is worth, and what it would cost to get.

Two numbers are reported for every roof and they are not equally trustworthy,
so the difference is worth stating before any of the arithmetic.

**LCOE is the defensible one.** It divides discounted lifetime cost by
discounted lifetime energy. The tariff does not appear in it anywhere, which
matters here because the tariff is the weakest input the project has: DERC
publishes no current retail schedule, only backward-looking true-up orders,
and ``config.TARIFF_INR_PER_KWH`` is a placeholder until a campus bill
arrives. An LCOE can be compared against whatever the Institute actually pays,
later, by someone who knows that number.

**Payback is the one everybody asks for, and it moves with the tariff.** It is
reported because a report without it reads as evasive, but it is reported with
its dependence visible rather than buried: halve the tariff and the payback
roughly doubles.

Capital cost is swept, not asserted. MNRE's benchmark turned out to be a
residential scheme with no institutional rate above 100 kW, so applying it to a
2.2 MW campus would have inflated the answer substantially while looking
official. The sweep spans the band published for Indian commercial and
institutional rooftop, and the spread is reported as the result.

One thing deliberately absent: there is no ranking here. Ordering the roofs
into a build sequence is a separate decision with its own criteria - grid
connection, occupancy, who pays - and dressing a sort by payback up as a
deployment plan would claim more than the arithmetic supports.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import config


def energy_in_year(
    first_year_kwh: float,
    year: int,
    degradation_per_year: float = config.MODULE_DEGRADATION_PER_YEAR,
) -> float:
    """Output in year ``year`` (1 is the first), after linear degradation."""
    if year < 1:
        raise ValueError("years are counted from 1")
    if not 0.0 <= degradation_per_year < 1.0:
        raise ValueError(f"degradation {degradation_per_year} is not a fraction")
    remaining = 1.0 - degradation_per_year * (year - 1)
    return first_year_kwh * max(remaining, 0.0)


def discounted_sum(values, discount_rate: float) -> float:
    """Present value of a stream starting one year from now."""
    if discount_rate <= -1.0:
        raise ValueError("discount rate below -100% is meaningless")
    return sum(v / (1.0 + discount_rate) ** (i + 1) for i, v in enumerate(values))


@dataclass(frozen=True)
class RoofEconomics:
    """The cost side, the energy side, and what falls out of the two."""

    building_id: str
    capacity_kwp: float
    first_year_kwh: float
    capex_inr: float
    annual_om_inr: float
    lifetime_years: int
    discount_rate: float
    tariff_inr_per_kwh: float

    lcoe_inr_per_kwh: float
    lifetime_kwh: float
    simple_payback_years: float | None
    discounted_payback_years: float | None
    npv_inr: float

    @property
    def pays_back_within_life(self) -> bool:
        return (
            self.discounted_payback_years is not None
            and self.discounted_payback_years <= self.lifetime_years
        )


def evaluate(
    building_id: str,
    capacity_kwp: float,
    first_year_kwh: float,
    capex_inr_per_kwp: float = config.CAPEX_INR_PER_KWP,
    tariff_inr_per_kwh: float = config.TARIFF_INR_PER_KWH,
    om_fraction: float = config.OM_FRACTION_OF_CAPEX,
    degradation_per_year: float = config.MODULE_DEGRADATION_PER_YEAR,
    lifetime_years: int = config.PROJECT_LIFETIME_YEARS,
    discount_rate: float = config.DISCOUNT_RATE,
) -> RoofEconomics:
    """Cost, energy and the usual derived figures for one roof."""
    if capacity_kwp <= 0:
        raise ValueError("a roof with no capacity has no economics")
    if first_year_kwh <= 0:
        raise ValueError("a roof that generates nothing has no economics")
    if lifetime_years < 1:
        raise ValueError("lifetime must be at least one year")

    capex = capacity_kwp * capex_inr_per_kwp
    annual_om = capex * om_fraction

    energy = [
        energy_in_year(first_year_kwh, y, degradation_per_year)
        for y in range(1, lifetime_years + 1)
    ]
    om = [annual_om] * lifetime_years

    discounted_energy = discounted_sum(energy, discount_rate)
    discounted_cost = capex + discounted_sum(om, discount_rate)
    lcoe = discounted_cost / discounted_energy

    savings = [e * tariff_inr_per_kwh - annual_om for e in energy]
    npv = discounted_sum(savings, discount_rate) - capex

    return RoofEconomics(
        building_id=building_id,
        capacity_kwp=capacity_kwp,
        first_year_kwh=first_year_kwh,
        capex_inr=capex,
        annual_om_inr=annual_om,
        lifetime_years=lifetime_years,
        discount_rate=discount_rate,
        tariff_inr_per_kwh=tariff_inr_per_kwh,
        lcoe_inr_per_kwh=lcoe,
        lifetime_kwh=sum(energy),
        simple_payback_years=_payback(capex, savings, discount_rate=0.0),
        discounted_payback_years=_payback(capex, savings, discount_rate),
        npv_inr=npv,
    )


def _payback(capex: float, savings, discount_rate: float) -> float | None:
    """Year in which cumulative savings first cover the capital cost.

    Interpolated within the crossing year rather than rounded up to it: a
    project that repays in the first month of year seven is not a seven-year
    project, and rounding would make every roof look alike.

    Returns ``None`` when the stream never covers the cost, which is a real
    answer and better than a number that implies it eventually does.
    """
    running = 0.0
    for index, value in enumerate(savings):
        present = value / (1.0 + discount_rate) ** (index + 1)
        if running + present >= capex:
            if present <= 0:
                return None
            shortfall = capex - running
            return index + shortfall / present
        running += present
    return None


def campus_total(results) -> dict:
    """Roll a set of roofs up, weighting LCOE by the energy behind it."""
    results = list(results)
    if not results:
        raise ValueError("no roofs to total")
    capex = sum(r.capex_inr for r in results)
    lifetime_kwh = sum(r.lifetime_kwh for r in results)
    first_year = sum(r.first_year_kwh for r in results)
    # An unweighted mean of ten LCOEs would let a 62 kWp roof count as much as
    # a 486 kWp one. The campus pays per kilowatt-hour, so weight by them.
    weighted_lcoe = sum(r.lcoe_inr_per_kwh * r.lifetime_kwh for r in results) / lifetime_kwh
    return {
        "roofs": len(results),
        "capacity_kwp": sum(r.capacity_kwp for r in results),
        "capex_inr": capex,
        "first_year_kwh": first_year,
        "lifetime_kwh": lifetime_kwh,
        "lcoe_inr_per_kwh": weighted_lcoe,
        "npv_inr": sum(r.npv_inr for r in results),
    }

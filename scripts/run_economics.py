"""What the campus potential costs, and what it is worth.

    make economics

Leads on **LCOE**, because the tariff is this project's weakest input and LCOE
does not contain it. Payback is reported too, with its dependence on the tariff
shown rather than buried.

Capital cost is swept across the band published for Indian commercial and
institutional rooftop rather than asserted at a point: MNRE's benchmark turned
out to be a residential scheme with no institutional rate above 100 kW, and
DERC publishes no current retail schedule. See ``docs/decisions.md``.

There is deliberately **no ranked build order** here. Sorting ten roofs by
payback and calling the result a deployment plan would claim more than the
arithmetic supports; grid connection, occupancy and who pays all belong in that
decision and none of them is in this model.

Writes ``data/economics.csv``.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from btp_solar import config, economics, register  # noqa: E402

OUT = config.DATA / "economics.csv"
RAIN = config.DATA / (
    f"nasa_precip_{config.SITE_LAT}_{config.SITE_LON}_20140101_20231231.json"
)


def shading_by_roof(rows) -> dict[str, float]:
    """Annual shading loss per roof, from the register.

    The register is where FR-3 wrote its answer, so it is where the economics
    reads it. `shading_factors.csv` is monthly working detail, not the figure.
    """
    return {
        r["building_id"]: float(r["annual_shading_loss"])
        for r in rows
        if r.get("annual_shading_loss") and r.get("shading_applied") == "yes"
    }


def soiling_annual_loss(monthly_shares) -> float:
    """Annual soiling loss at the **stated** rate, not the fitted one.

    Computed from the rainfall record rather than read back from the sweep's
    output file. `make soiling` searches for the rate that minimises the
    back-test residual; using that rate as a model input here would feed a
    fitted parameter into the thing it was fitted against. The sweep is a
    diagnostic and `config.SOILING_RATE_PER_DAY` is the input.
    """
    if not RAIN.exists():
        return 0.0
    from btp_solar import soiling

    rainfall = soiling.load_daily_rainfall(RAIN)
    loss = soiling.soiling_loss(rainfall, soiling_rate=config.SOILING_RATE_PER_DAY)
    monthly = soiling.monthly_mean_loss(loss)
    # Weighted by each month's share of output, so the dirtiest months do not
    # count as if they were also the sunniest.
    return sum(l * s for l, s in zip(monthly, monthly_shares))


def monthly_shares() -> list[float]:
    """Modelled campus output by month, as fractions of the year."""
    path = config.DATA / "generation_monthly.csv"
    if not path.exists():
        return [1.0 / 12] * 12
    totals = [0.0] * 12
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            totals[int(row["month"]) - 1] += float(row["mean_kwh"])
    total = sum(totals)
    return [v / total for v in totals] if total else [1.0 / 12] * 12


def main() -> int:
    rows = [r for r in register.load() if r["building_id"].startswith("B")]
    shade = shading_by_roof(rows)
    soil = soiling_annual_loss(monthly_shares())

    print("Rupee figures in this project are indicative and say so.")
    print("  - MNRE's benchmark is residential only, with no rate above 100 kW")
    print("  - DERC publishes no current retail schedule, only true-up orders")
    print(f"  - so the tariff is a placeholder at Rs {config.TARIFF_INR_PER_KWH:.2f}/kWh")
    print("  - and capital cost is swept rather than asserted")
    print("LCOE is reported first because it contains neither of them.\n")

    print(f"Assumptions: {config.PROJECT_LIFETIME_YEARS} year life, "
          f"{config.MODULE_DEGRADATION_PER_YEAR:.1%}/yr degradation, "
          f"{config.OM_FRACTION_OF_CAPEX:.1%} of capex per year O&M,")
    print(f"             {config.DISCOUNT_RATE:.0%} discount rate, "
          f"soiling {soil:.1%} of annual output")

    roofs = []
    for row in rows:
        capacity = float(row["installable_capacity_kwp"])
        yield_ = float(row["specific_yield"])
        loss = shade.get(row["building_id"], 0.0)
        first_year = capacity * yield_ * (1.0 - loss) * (1.0 - soil)
        roofs.append((row, capacity, first_year, loss))

    print(f"\nFirst-year energy after {len(shade)} shading factors and soiling")
    print(f"  {'id':<5}{'name':<26}{'kWp':>9}{'yield':>8}{'shade':>7}"
          f"{'MWh/yr':>9}")
    for row, capacity, first_year, loss in roofs:
        print(f"  {row['building_id']:<5}{row['building_name'][:25]:<26}"
              f"{capacity:>9.1f}{float(row['specific_yield']):>8.0f}"
              f"{loss:>7.1%}{first_year / 1000:>9.0f}")

    total_kwp = sum(c for _, c, _, _ in roofs)
    total_kwh = sum(e for _, _, e, _ in roofs)
    print(f"  {'':<5}{'campus':<26}{total_kwp:>9.1f}{'':>8}{'':>7}"
          f"{total_kwh / 1000:>9.0f}")

    # --- the sweep --------------------------------------------------------
    print(f"\nCapital cost swept across the published band. "
          f"Campus is {total_kwp:,.0f} kWp.")
    print(f"  {'Rs/kWp':>8}{'capex Rs cr':>13}{'LCOE Rs/kWh':>13}"
          f"{'payback yr':>12}{'NPV Rs cr':>12}")
    for capex in config.CAPEX_SWEEP_INR_PER_KWP:
        evaluated = [
            economics.evaluate(row["building_id"], capacity, first_year,
                               capex_inr_per_kwp=capex)
            for row, capacity, first_year, _ in roofs
        ]
        total = economics.campus_total(evaluated)
        paybacks = [e.discounted_payback_years for e in evaluated
                    if e.discounted_payback_years is not None]
        payback = sum(paybacks) / len(paybacks) if paybacks else float("nan")
        print(f"  {capex:>8,.0f}{total['capex_inr'] / 1e7:>13.1f}"
              f"{total['lcoe_inr_per_kwh']:>13.2f}{payback:>12.1f}"
              f"{total['npv_inr'] / 1e7:>12.1f}")

    # --- per roof at the midpoint ----------------------------------------
    print(f"\nPer roof at Rs {config.CAPEX_INR_PER_KWP:,.0f}/kWp, the midpoint")
    print(f"  {'id':<5}{'capex Rs L':>12}{'LCOE':>8}{'simple':>9}"
          f"{'disc.':>8}{'NPV Rs L':>11}")
    evaluated = []
    for row, capacity, first_year, loss in roofs:
        e = economics.evaluate(row["building_id"], capacity, first_year)
        evaluated.append((row, e, loss, first_year))
        simple = f"{e.simple_payback_years:.1f}" if e.simple_payback_years else "never"
        disc = f"{e.discounted_payback_years:.1f}" if e.discounted_payback_years else "never"
        print(f"  {e.building_id:<5}{e.capex_inr / 1e5:>12.1f}"
              f"{e.lcoe_inr_per_kwh:>8.2f}{simple:>9}{disc:>8}"
              f"{e.npv_inr / 1e5:>11.1f}")

    spread = [e.lcoe_inr_per_kwh for _, e, _, _ in evaluated]
    print(f"\n  LCOE spread across the ten roofs: Rs {min(spread):.2f} to "
          f"Rs {max(spread):.2f} per kWh, a {max(spread) / min(spread) - 1:.0%} range.")
    print("  That spread is the whole reason roofs are not interchangeable.")

    # --- how much the tariff assumption is carrying ----------------------
    print(f"\nHow much of the payback rests on the placeholder tariff")
    print(f"  {'Rs/kWh':>8}{'campus payback yr':>20}{'NPV Rs cr':>12}")
    for tariff in (5.0, 6.5, 8.0, 9.5, 11.0):
        evals = [
            economics.evaluate(row["building_id"], capacity, first_year,
                               tariff_inr_per_kwh=tariff)
            for row, capacity, first_year, _ in roofs
        ]
        paybacks = [e.discounted_payback_years for e in evals
                    if e.discounted_payback_years is not None]
        payback = (f"{sum(paybacks) / len(paybacks):.1f}" if paybacks
                   else f"never ({len(evals) - len(paybacks)} roofs)")
        total = economics.campus_total(evals)
        marker = "  <- placeholder" if tariff == config.TARIFF_INR_PER_KWH else ""
        print(f"  {tariff:>8.2f}{payback:>20}{total['npv_inr'] / 1e7:>12.1f}{marker}")
    print("  LCOE is unchanged down this column. That is the point of it.")

    # --- against the grid -------------------------------------------------
    best = min(spread)
    print(f"\nThe comparison that does not need the tariff")
    print(f"  cheapest roof generates at Rs {best:.2f}/kWh over its life")
    print(f"  campus average             Rs "
          f"{economics.campus_total([e for _, e, _, _ in evaluated])['lcoe_inr_per_kwh']:.2f}/kWh")
    print(f"  placeholder grid tariff    Rs {config.TARIFF_INR_PER_KWH:.2f}/kWh")
    print("  Whatever the Institute actually pays, the comparison is to these.")

    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "building_id", "building_name", "capacity_kwp", "specific_yield",
            "shading_loss", "soiling_loss", "first_year_kwh", "capex_inr",
            "lcoe_inr_per_kwh", "simple_payback_years",
            "discounted_payback_years", "npv_inr", "capex_inr_per_kwp",
            "tariff_inr_per_kwh", "discount_rate", "lifetime_years", "source",
        ])
        for row, e, loss, first_year in evaluated:
            writer.writerow([
                e.building_id, row["building_name"], f"{e.capacity_kwp:.1f}",
                row["specific_yield"], f"{loss:.4f}", f"{soil:.4f}",
                f"{first_year:.0f}", f"{e.capex_inr:.0f}",
                f"{e.lcoe_inr_per_kwh:.3f}",
                f"{e.simple_payback_years:.2f}" if e.simple_payback_years else "",
                f"{e.discounted_payback_years:.2f}" if e.discounted_payback_years else "",
                f"{e.npv_inr:.0f}", f"{config.CAPEX_INR_PER_KWP:.0f}",
                f"{config.TARIFF_INR_PER_KWH:.2f}", f"{config.DISCOUNT_RATE:.3f}",
                config.PROJECT_LIFETIME_YEARS, "indicative_swept_capex",
            ])
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    print("No build order is produced here, deliberately - see the module note.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

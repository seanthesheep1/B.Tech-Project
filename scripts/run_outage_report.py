"""Which existing campus PV plants have stopped, and what that has cost.

The Estate Office workbooks record a reading every day whether or not the
plant is generating, so a dead plant looks exactly like a live one until the
register is differenced. This script does that differencing and reports the
plants whose register has not moved for longer than config.OUTAGE_MONTHS.

    uv run python scripts/run_outage_report.py

Every rupee figure here is an ESTIMATE built on two assumptions - the
back-calculated capacity in campus_meters.Plant.estimated_kwp, and the tariff
below, which is not yet confirmed by the Institute. The outages themselves are
a matter of fact; the money is indicative and must be reported as such.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "src")

from btp_solar import campus_meters, config  # noqa: E402

TARIFF_RS_PER_KWH = 8.0  # provisional: DERC institutional rate, D38 not yet received


def main() -> int:
    plants = campus_meters.load(sorted(config.DATA.glob(config.METER_WORKBOOK_GLOB)))
    all_months = sorted({m for p in plants.values() for m in p.monthly_kwh})
    if not all_months:
        print("No monthly data parsed.")
        return 1
    as_of = all_months[-1]

    stopped = [p for p in plants.values() if p.lost_kwh(as_of) > 0]
    stopped.sort(key=lambda p: -p.lost_kwh(as_of))

    print(f"Meter record runs to {as_of}. "
          f"{len(stopped)} of {len(plants)} plants have stopped generating.\n")
    if not stopped:
        return 0

    header = f"{'plant':<34}{'est kWp':>9}{'last gen':>10}{'months':>8}{'lost MWh':>10}"
    print(header)
    print("-" * len(header))
    total = 0.0
    for p in stopped:
        lost = p.lost_kwh(as_of)
        total += lost
        print(f"{p.location[:33]:<34}{p.estimated_kwp:>9.0f}{p.live_months[-1]:>10}"
              f"{p.months_idle(as_of):>8}{lost/1000:>10.1f}")
    print("-" * len(header))
    print(f"{'TOTAL':<53}{total/1000:>8.1f} MWh")

    idle_kwp = sum(p.estimated_kwp for p in stopped)
    monthly = idle_kwp * 5.5 * 30 * config.PERFORMANCE_RATIO
    print(f"\n  ~Rs {total * TARIFF_RS_PER_KWH / 1e5:,.1f} lakh of electricity not generated"
          f" (at Rs {TARIFF_RS_PER_KWH:.0f}/kWh)")
    print(f"  ~Rs {monthly * TARIFF_RS_PER_KWH / 1e5:,.2f} lakh per month still being lost"
          f" from {idle_kwp:.0f} kWp sitting idle")
    print("\n  Capacity and tariff are both estimates - see the module docstring.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

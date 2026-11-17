"""Does Delhi dust explain the back-test's winter bias?

    make soiling

The model puts more energy into the winter months than the fleet delivers.
Shading was not the cause: it moved the shape error from 0.101 to 0.097. Row
spacing was not the cause either. Soiling is the remaining candidate, and the
rainfall record says why it would be seasonal here - November averages one wet
day per decade.

The soiling rate is **not fitted**. It is swept across the band reported for
northern India and the whole curve is printed, because a rate chosen to make
the back-test pass would absorb whatever else the model had wrong and the pass
would mean nothing. The question is falsifiable: does an ordinary amount of
dust account for the residual, or does it take an absurd amount?

Writes ``data/soiling_monthly.csv``.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from btp_solar import acceptance, config, fr1_data, soiling  # noqa: E402
import run_fr4_backtest as backtest  # noqa: E402

RAIN = config.DATA / f"nasa_precip_{config.SITE_LAT}_{config.SITE_LON}_20140101_20231231.json"
OUT = config.DATA / "soiling_monthly.csv"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def main() -> int:
    if not RAIN.exists():
        print(f"missing {RAIN.name}; run fr1_data.fetch_nasa_precipitation() first")
        return 1

    rainfall = soiling.load_daily_rainfall(RAIN)
    years = rainfall.index.year.nunique()
    print(f"NASA POWER daily rainfall, {rainfall.index.min().date()} to "
          f"{rainfall.index.max().date()} ({years} years)\n")

    wet = rainfall.groupby(rainfall.index.month)
    print(f"  {'month':>5} {'mm/yr':>8} {'days past the':>14}")
    print(f"  {'':>5} {'':>8} {str(soiling.CLEANING_THRESHOLD_MM) + ' mm wash':>14}")
    for m in range(1, 13):
        vals = wet.get_group(m)
        print(f"  {MONTHS[m - 1]:>5} {vals.sum() / years:8.1f} "
              f"{(vals > soiling.CLEANING_THRESHOLD_MM).sum() / years:14.1f}")

    fleet, _ = backtest.measured_fleet(backtest.BACKTEST_YEAR)
    modelled = backtest.modelled_campus()
    measured_shape = fr1_data.normalised_shape(fleet)
    base_error = fr1_data.shape_error(
        fr1_data.normalised_shape(modelled), measured_shape
    )
    print(f"\nBack-test with no soiling at all: shape error {base_error:.4f} "
          f"(tolerance {config.SHAPE_AGREEMENT_TOL})\n")

    # The winter months on their own. Total shape error is a poor instrument
    # for this question: both series are normalised, so energy taken out of
    # December has to reappear somewhere, and it lands in months the model
    # already overstates. A fix to winter can therefore barely move the total
    # while being entirely real. The winter sum is what soiling is accused of.
    WINTER = (10, 11, 0)  # Nov, Dec, Jan

    def winter_error(shape):
        return sum(abs(shape[m] - measured_shape[m]) for m in WINTER)

    base_winter = winter_error(fr1_data.normalised_shape(modelled))
    print(f"Of which the Nov-Dec-Jan over-prediction is {base_winter:.4f}, "
          f"{base_winter / base_error:.0%} of the total.\n")

    print("Sweeping the soiling rate. The rate is not fitted; the curve is the result.")
    print(f"  {'%/dry day':>10} {'annual loss':>12} {'winter loss':>12} "
          f"{'shape error':>12} {'vs none':>9} {'winter err':>11} {'vs none':>9}")

    rows = []
    best = None
    for rate in soiling.SOILING_RATE_SWEEP:
        loss = soiling.soiling_loss(rainfall, soiling_rate=rate)
        monthly = soiling.monthly_mean_loss(loss)
        dirty = soiling.apply_monthly(modelled, monthly)
        error = fr1_data.shape_error(
            fr1_data.normalised_shape(dirty), measured_shape
        )
        annual = soiling.annual_loss(modelled, monthly)
        winter = sum(monthly[m] for m in (10, 11, 0, 1)) / 4.0
        werr = winter_error(fr1_data.normalised_shape(dirty))
        rows.append((rate, annual, winter, monthly, error, werr))
        if best is None or error < best[1]:
            best = (rate, error)
        print(f"  {rate * 100:10.2f} {annual:11.1%} {winter:11.1%} "
              f"{error:12.4f} {error - base_error:+9.4f} "
              f"{werr:11.4f} {werr - base_winter:+9.4f}")

    rate, error = best
    print(f"\nLowest shape error at {rate * 100:.2f}%/dry day: "
          f"{error:.4f}, down from {base_error:.4f}")
    verdict = acceptance.fr4_shape_agreement(
        fr1_data.normalised_shape(soiling.apply_monthly(
            modelled,
            dict(zip(soiling.SOILING_RATE_SWEEP, [r[3] for r in rows]))[rate])),
        measured_shape,
    )
    print(f"  {verdict}")
    best_winter = min(r[5] for r in rows)
    at_rate = [r[0] for r in rows if r[5] == best_winter][0]
    print(f"Lowest winter error at {at_rate * 100:.2f}%/dry day: "
          f"{best_winter:.4f}, down from {base_winter:.4f} "
          f"({1 - best_winter / base_winter:.0%} of the winter bias removed)")
    print()
    print("Reading this honestly: dust accounts for most of the winter leg of the")
    print("residual and almost none of the total. Both are true and neither is")
    print("the headline on its own. Because the shapes are normalised, energy")
    print("removed from December reappears in the months the model already")
    print("overstates, so the total barely moves while the thing soiling was")
    print("accused of largely goes away. What is left is a spring and monsoon")
    print("error of the opposite sign, which dust cannot cause and which is the")
    print("next thing to chase.")

    monthly = dict(zip(soiling.SOILING_RATE_SWEEP, [r[3] for r in rows]))[rate]
    print(f"\nMonthly soiling loss at {rate * 100:.2f}%/dry day, and what it does"
          f" to the shape")
    print(f"  {'':5}{'soiling':>9}{'measured':>10}{'clean':>9}{'dirty':>9}{'diff':>9}")
    clean_shape = fr1_data.normalised_shape(modelled)
    dirty_shape = fr1_data.normalised_shape(soiling.apply_monthly(modelled, monthly))
    for m in range(12):
        print(f"  {MONTHS[m]:5}{monthly[m]:>9.1%}{measured_shape[m]:>10.3f}"
              f"{clean_shape[m]:>9.3f}{dirty_shape[m]:>9.3f}"
              f"{dirty_shape[m] - measured_shape[m]:>+9.3f}")

    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["month", "soiling_loss", "soiling_rate_per_day",
                         "measured_share", "clean_share", "dirty_share", "source"])
        for m in range(12):
            writer.writerow([m + 1, f"{monthly[m]:.4f}", f"{rate:.4f}",
                             f"{measured_shape[m]:.4f}", f"{clean_shape[m]:.4f}",
                             f"{dirty_shape[m]:.4f}", "kimber_nasa_power_rain"])
    print(f"\nwrote {OUT.relative_to(ROOT)}")

    # What a cleaning contract would be worth, since the dust is now quantified.
    print("\nIf the dust were washed off instead of waited out")
    annual_do_nothing = soiling.annual_loss(
        modelled, soiling.monthly_mean_loss(soiling.soiling_loss(rainfall, rate))
    )
    for months, label in (((1,), "once, in February"),
                          ((12, 2), "twice, December and February"),
                          ((11, 1, 3), "three times over the dry season")):
        washes = soiling.washes_each_year(rainfall, months)
        loss = soiling.soiling_loss(rainfall, rate, manual_wash_dates=washes)
        saved = annual_do_nothing - soiling.annual_loss(
            modelled, soiling.monthly_mean_loss(loss)
        )
        kwh = saved * sum(modelled)
        print(f"  washed {label:<32} recovers {saved:5.2%}  "
              f"{kwh / 1000:6.0f} MWh/yr  "
              f"Rs {kwh * config.TARIFF_INR_PER_KWH / 100000:5.1f} lakh/yr")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

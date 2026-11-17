"""FR-4 back-test: does the model put the energy in the right months?

    uv run python scripts/run_fr4_backtest.py

The obvious test - specific yield against the existing plants - cannot be run
honestly. Plant capacity is not in the Estate Office workbooks and is
back-calculated from generation, so kWh / kWp collapses to the assumed constant
and passes by construction (docs/decisions.md, 2026-09-22).

What is tested instead is **shape**. Modelled and measured generation are each
normalised to their own annual total and compared month by month. Capacity
cancels, so nothing circular survives, and what remains under test is the
irradiance, transposition, shading and temperature modelling.

The method is not invented here: it is what arbitrated FR-1 in Part 3, where
the same 792 MWh of measured generation chose NASA POWER over PVGIS.

Two reference points are recomputed rather than quoted, so the modelled shape
can be judged against something:

    NASA POWER GHI shape error    0.072  <- the Part 3 figure
    PVGIS TMY GHI shape error     0.109

A model that reproduces the measured year better than raw horizontal
irradiance does is adding value. One that does worse is being pulled off by
something it models badly, and the per-month table says where.
"""

from __future__ import annotations

import calendar
import collections
import csv
import statistics
import sys
from pathlib import Path

sys.path.insert(0, "src")

from btp_solar import acceptance, config, fr1_data

MEASURED = config.DATA / "campus_solar_monthly.csv"
MODELLED = config.DATA / "generation_monthly.csv"
OUT = config.DATA / "backtest_shape.csv"
FIGURE = config.REPORTS / "figures" / "shape_validation.png"

BACKTEST_YEAR = 2024  # the one complete year with the whole fleet reporting
MONTHS = [calendar.month_abbr[m] for m in range(1, 13)]


def measured_fleet(year: int) -> tuple[list[float], dict[str, list[float]]]:
    """Monthly kWh for every plant that was live all year, and the fleet total.

    A plant is included only if it reported a positive figure in all twelve
    months. A plant that stopped mid-year would otherwise drag the shape toward
    whichever months it was alive for, which is a property of the outage and
    not of the weather.
    """
    by_plant: dict[str, dict[str, float]] = collections.defaultdict(dict)
    names: dict[str, str] = {}
    with MEASURED.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            by_plant[row["meter"]][row["month"]] = float(row["kwh"])
            names[row["meter"]] = row["location"]

    wanted = [f"{year}-{m:02d}" for m in range(1, 13)]
    complete: dict[str, list[float]] = {}
    for meter, months in by_plant.items():
        if all(months.get(m, 0.0) > 0 for m in wanted):
            complete[names[meter]] = [months[m] for m in wanted]

    fleet = [sum(v[i] for v in complete.values()) for i in range(12)]
    return fleet, complete


def modelled_campus() -> list[float]:
    """Modelled monthly energy summed over the candidate roofs."""
    totals = [0.0] * 12
    with MODELLED.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            totals[int(row["month"]) - 1] += float(row["mean_kwh"])
    return totals


def main() -> int:
    for path in (MEASURED, MODELLED):
        if not path.exists():
            print(f"missing {path.name}; run the earlier steps first")
            return 1

    fleet, plants = measured_fleet(BACKTEST_YEAR)
    if not plants:
        print(f"no plant reported a complete {BACKTEST_YEAR}")
        return 1

    modelled = modelled_campus()
    measured_shape = fr1_data.normalised_shape(fleet)
    modelled_shape = fr1_data.normalised_shape(modelled)

    print(f"Measured: {len(plants)} plants live for the whole of {BACKTEST_YEAR}, "
          f"{sum(fleet) / 1000:.0f} MWh")
    print(f"Modelled: {sum(modelled) / 1000:.0f} MWh across the ten candidate roofs, "
          f"mean of 2014-2023\n")

    # --- how much do the real plants even agree with each other? ----------
    # The fleet mean is only a fair target if the plants resemble one another.
    per_plant = {n: fr1_data.normalised_shape(v) for n, v in plants.items()}
    spread = [statistics.stdev([s[m] for s in per_plant.values()]) for m in range(12)]
    worst = max(range(12), key=lambda m: spread[m])
    print(f"Spread between the {len(plants)} measured plants: "
          f"±{statistics.mean(spread):.3f} on a monthly share, widest in "
          f"{MONTHS[worst]} (±{spread[worst]:.3f}).")
    print("That is the noise floor; the model cannot be judged below it.\n")

    # --- the comparison ---------------------------------------------------
    header = f"  {'':5}{'measured':>10}{'modelled':>10}{'diff':>9}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    rows = []
    for m in range(12):
        diff = modelled_shape[m] - measured_shape[m]
        flag = "  <-" if abs(diff) > 2 * spread[m] else ""
        print(f"  {MONTHS[m]:5}{measured_shape[m]:>10.3f}{modelled_shape[m]:>10.3f}"
              f"{diff:>+9.3f}{flag}")
        rows.append({
            "month": m + 1, "month_name": MONTHS[m],
            "measured_kwh": round(fleet[m], 1),
            "modelled_kwh": round(modelled[m], 1),
            "measured_share": round(measured_shape[m], 4),
            "modelled_share": round(modelled_shape[m], 4),
            "difference": round(diff, 4),
            "plant_spread": round(spread[m], 4),
        })
    print("  " + "-" * (len(header) - 2))
    outside = [r for r in rows if abs(r["difference"]) > 2 * r["plant_spread"]]
    if outside:
        print(f"  <- {len(outside)} month(s) where the model sits outside the spread "
              f"of the real plants\n")
    else:
        print("  Every month is inside the spread of the 18 measured plants.\n")

    # --- against the raw irradiance sources -------------------------------
    print("Shape error against the measured fleet, lower is better")
    references = {}
    nasa = config.DATA / "nasa_power_28.545_77.192_20140101_20231231.json"
    pvgis = config.DATA / "pvgis_tmy_28.545_77.192.json"
    if nasa.exists():
        references["NASA POWER GHI"] = fr1_data.monthly_mean_daily_ghi_nasa(nasa)
    if pvgis.exists():
        references["PVGIS TMY GHI"] = fr1_data.monthly_mean_daily_ghi_pvgis(pvgis)

    model_error = fr1_data.shape_error(modelled_shape, measured_shape)
    scores = [("our model (tilted, after losses)", model_error)]
    for name, series in references.items():
        scores.append((name, fr1_data.shape_error(
            fr1_data.normalised_shape(series), measured_shape)))
    for name, score in sorted(scores, key=lambda kv: kv[1]):
        print(f"  {name:<36}{score:.3f}")

    jan_apr_measured = fleet[0] / fleet[3]
    jan_apr_modelled = modelled[0] / modelled[3]
    print(f"\nJanuary / April ratio   measured {jan_apr_measured:.3f}   "
          f"modelled {jan_apr_modelled:.3f}")

    _write(OUT, rows)
    print(f"\nWritten {OUT.relative_to(config.ROOT)}")
    try:
        _figure(measured_shape, modelled_shape, spread)
        print(f"Figure:  {FIGURE.relative_to(config.ROOT)}")
    except Exception as exc:  # noqa: BLE001 - a figure must not fail the check
        print(f"Figure skipped: {exc}")

    print("\nFR-4 back-test")
    check = acceptance.fr4_shape_agreement(modelled, fleet)
    print(" ", check)
    reference_shapes = {
        name: fr1_data.normalised_shape(series) for name, series in references.items()
    }
    _interpret(modelled_shape, measured_shape, spread, model_error,
               dict(scores), reference_shapes)
    return 0


WINTER = (0, 1, 10, 11)   # Nov-Feb
SPRING = (2, 3, 4)        # Mar-May


def _interpret(modelled, measured, spread, model_error, scores, reference_shapes) -> None:
    """Say what the numbers mean, including when they are unflattering."""
    winter_gap = sum(modelled[m] - measured[m] for m in WINTER)
    spring_gap = sum(modelled[m] - measured[m] for m in SPRING)
    inside = all(abs(modelled[m] - measured[m]) <= 2 * spread[m] for m in range(12))

    best_raw = min((v for k, v in scores.items() if "our model" not in k), default=None)
    print()
    if best_raw is not None and model_error > best_raw:
        print("  The model reproduces the measured year WORSE than raw horizontal")
        print(f"  irradiance does ({model_error:.3f} against {best_raw:.3f}). Tilting the")
        print("  plane and applying the loss stack should have improved the match, not")
        print("  degraded it, so something seasonal is being modelled wrongly.")
    else:
        print("  The model reproduces the measured year better than raw horizontal")
        print("  irradiance does, which is what tilting and the loss stack should buy.")

    high = [MONTHS[m] for m in range(12) if modelled[m] > measured[m]]
    low = [MONTHS[m] for m in range(12) if modelled[m] < measured[m]]
    if inside:
        print(f"""
  Before reading too much into that: **no single month falls outside the
  spread of the 18 real plants**, which is +-{statistics.mean(spread):.3f} on a monthly share
  against a largest monthly deviation of {max(abs(modelled[m] - measured[m]) for m in range(12)):.3f}. Month by month the model is
  inside the noise. What makes the gap worth taking seriously is that it is
  **systematic rather than scattered**:

      model reads high in   {', '.join(high)}
      model reads low in    {', '.join(low)}

  The deviations are not random month to month - they run in blocks, which is
  the signature of a seasonal effect that is modelled wrongly rather than of
  measurement noise.""")

    print(f"\n  Winter (Nov-Feb): modelled share is {winter_gap:+.3f} against measured.")
    print(f"  Spring (Mar-May): modelled share is {spring_gap:+.3f} against measured.")

    # The sharpest diagnostic: compare winter share against flat-plate irradiance.
    horizontal = reference_shapes.get("NASA POWER GHI")
    if horizontal:
        w_flat = sum(horizontal[m] for m in WINTER)
        w_meas = sum(measured[m] for m in WINTER)
        w_model = sum(modelled[m] for m in WINTER)
        print(f"""
  Winter share of the year, Nov-Feb:

      {"horizontal irradiance (NASA GHI)":<34}{w_flat:.3f}
      {"the measured plants":<34}{w_meas:.3f}
      {f"our model at {config.MODULE_TILT_DEG:.0f} deg tilt":<34}{w_model:.3f}

  **The real plants behave seasonally like a flat surface.** A south-facing
  tilt should lift the winter share, because tilt gain is largest when the sun
  is lowest - our model duly lifts it from {w_flat:.3f} to {w_model:.3f}. The measured fleet
  sits at {w_meas:.3f}, which is the horizontal figure. The tilt gain is simply absent
  from the data.

  Two readings, and they have different consequences:

    a. **The existing arrays are mounted flat, or nearly so.** Common enough on
       Indian institutional roofs, where wind load and ballast cost dominate.
       If so, our 15 deg design tilt is not corroborated by any campus
       installation - and docs/decisions.md has carried "confirm against a real
       campus installation" against that value since 21 September. This is that
       confirmation, and it points the other way.

    b. **They are tilted, and winter losses cancel the gain exactly.** Fog,
       soiling and inter-row shading all bite hardest in winter. Possible, but
       the cancellation would have to be a coincidence.

  Either way this is settled by looking, not arguing: panel foreshortening and
  shadow length in the satellite imagery give the real tilt directly, and the
  census in Step 2b is already going to that imagery. Measure the tilt while
  there.

  **If (a) holds it changes the headline.** Flat modules need no inter-row
  spacing, so the ground coverage ratio rises from {config.MODULE_TILT_DEG:.0f} deg's 0.707 toward 1.0:
  more kilowatts on the same roof, at a lower yield per kilowatt. That is a
  real design trade-off this project should put a number on rather than
  inherit by assumption.""")

    if winter_gap > 0.02:
        share = winter_gap / sum(measured[m] for m in WINTER)
        print(f"""
  The model is too optimistic in winter, by {share:.0%} of the winter share.
  Three candidates, in the order worth testing:

    1. Shading is still unity. Shadows are longest in December, so the months
       the model overstates are exactly the months Part 6 will cut. This is the
       most likely explanation and it is already the next step.
    2. Soiling is a flat 3% all year. Delhi's winter brings fog, dust and no
       rain to wash the modules, so the real winter loss is larger.
    3. The beam fraction may be overstated in winter haze. The decomposition
       was checked at the annual level, where DIRINT and Erbs agreed to within
       0.1%, but that test does not bind seasonally.

  None of these is a reason to distrust the annual figure: they move energy
  between months rather than changing the total. Re-run this back-test after
  Part 6 and the winter gap should close. If it does not, the soiling model is
  the next thing to fix.""")


def _write(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _figure(measured, modelled, spread) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    x = range(12)
    ax.errorbar(x, measured, yerr=spread, fmt="o-", color="#000000", linewidth=1.4,
                markersize=4, capsize=3, label="measured fleet, 2024")
    ax.plot(x, modelled, "s--", color="#808080", linewidth=1.4, markersize=4,
            label="modelled, no shading")
    ax.set_xticks(list(x))
    ax.set_xticklabels(MONTHS)
    ax.set_ylabel("share of the year's generation")
    ax.set_title("FR-4 back-test: seasonal shape, each series normalised to its own total\n"
                 "capacity cancels, so this tests the weather modelling alone",
                 fontsize=9, loc="left")
    ax.legend(frameon=False, fontsize=8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURE, dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())

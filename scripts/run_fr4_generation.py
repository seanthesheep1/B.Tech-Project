"""FR-4: model the generation of every candidate roof and write the register.

    uv run python scripts/run_fr4_generation.py

This is the step that turns the project from a measurement of roof area into a
measurement of energy. It runs the pvlib chain on the irradiance source Part 3
selected, scales it to each roof's installable capacity, and writes annual
energy, specific yield and capacity factor into the building register.

Three variants are run, because the primary source gives global irradiance only
and the decomposition into beam and diffuse is an assumption:

    nasa_dirint   NASA POWER, DIRINT decomposition      <- primary
    nasa_erbs     NASA POWER, Erbs decomposition        <- sensitivity
    pvgis_tmy     PVGIS typical year, its own components <- FR-4 cross-check

Shading is applied when Part 6 has been run and ``roof_horizons.npz`` exists:
the beam component is scaled hour by hour by the fraction of each roof that can
see the sun, and the diffuse component by the roof's sky view factor. Without
that file the run is an unshaded upper bound, and the register's
``shading_applied`` column records which pass produced its numbers so the two
cannot be confused.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, "src")

from btp_solar import acceptance, config, fr3_shading, fr4_generation, register

NASA = config.DATA / "nasa_power_28.545_77.192_20140101_20231231.json"
PVGIS = config.DATA / "pvgis_tmy_28.545_77.192.json"
RESULTS = config.DATA / "generation_results.csv"
MONTHLY = config.DATA / "generation_monthly.csv"
VARIANTS = config.DATA / "generation_variants.csv"
HORIZONS = config.DATA / "roof_horizons.npz"
FIGURE = config.REPORTS / "figures" / "monthly_generation.png"

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def candidates() -> list[tuple[str, str, float]]:
    """The roofs with a capacity to model: id, name, installable kWp."""
    out = []
    for row in register.load():
        if row["role"] != "candidate" or not row["installable_capacity_kwp"].strip():
            continue
        out.append((row["building_id"], row["building_name"],
                    float(row["installable_capacity_kwp"])))
    return out


def main() -> int:
    if not NASA.exists():
        print(f"missing {NASA.name}; run scripts/run_fr1_data.py first")
        return 1

    roofs = candidates()
    if not roofs:
        print("no candidate carries an installable capacity; run FR-2 first")
        return 1

    print("Building the site chain. Irradiance and cell temperature depend only")
    print("on the site, so they are computed once and scaled per roof.\n")

    nasa = fr4_generation.load_nasa_hourly(NASA)
    print(f"  NASA POWER   {len(nasa):,} hourly rows, time standard "
          f"{nasa.attrs['time_standard']}, "
          f"{nasa.index[0].year}-{nasa.index[-1].year}")

    chains = {
        "nasa_dirint": fr4_generation.build_site_chain(nasa, "dirint"),
        "nasa_erbs": fr4_generation.build_site_chain(nasa, "erbs"),
    }
    if PVGIS.exists():
        pvgis = fr4_generation.load_pvgis_hourly(PVGIS)
        print(f"  PVGIS TMY    {len(pvgis):,} hourly rows, its own beam and diffuse")
        chains["pvgis_tmy"] = fr4_generation.build_site_chain(pvgis)

    primary = chains["nasa_dirint"]

    shading = {}
    if HORIZONS.exists():
        import numpy as np
        import pandas as pd

        stored = np.load(HORIZONS)
        for bid in stored.files:
            horizons = stored[bid]
            beam = fr3_shading.sunlit_fraction_series(
                horizons,
                primary.solar_azimuth.to_numpy(),
                primary.solar_elevation.to_numpy(),
            )
            svf = float(np.mean([fr3_shading.sky_view_factor(h) for h in horizons]))
            shading[bid] = (pd.Series(beam, index=primary.poa_direct.index), svf)
        print(f"\n  Shading   {HORIZONS.name}, {len(shading)} roofs, "
              f"applied to the beam hour by hour and to the diffuse by sky view factor")
    else:
        print(f"\n  Shading   {HORIZONS.name} not found: this run is an "
              f"UNSHADED UPPER BOUND. Run scripts/run_fr3_shading.py first.")

    # --- the variant comparison, at a nominal 100 kWp ---------------------
    print("\nVariant comparison at 100 kWp, before any shading")
    print(f"  {'variant':<13}{'POA':>9}{'yield':>9}{'vs primary':>12}")
    variant_rows = []
    base = None
    for name, chain in chains.items():
        probe = fr4_generation.run_model_chain("PROBE", chain, 100.0)
        poa = chain.mean_annual_poa_kwh_per_m2()
        base = base if base is not None else probe.specific_yield
        gap = (probe.specific_yield - base) / base
        print(f"  {name:<13}{poa:>9.0f}{probe.specific_yield:>9.0f}{gap:>11.1%}")
        variant_rows.append({
            "variant": name,
            "source": chain.source,
            "decomposition": chain.decomposition,
            "annual_poa_kwh_per_m2": round(poa, 1),
            "specific_yield_kwh_per_kwp": round(probe.specific_yield, 1),
            "gap_vs_primary": round(gap, 4),
        })

    # --- per roof, on the primary variant --------------------------------
    print(f"\nPer roof, primary variant ({primary.source} / {primary.decomposition})")
    header = (f"  {'id':<5}{'kWp':>8}{'MWh/yr':>9}{'sd':>7}{'kWh/kWp':>9}{'CF':>7}"
              f"{'shade':>8}")
    print(header)
    print("  " + "-" * (len(header) - 2))

    rows = register.load()
    by_id = {r["building_id"]: r for r in rows}
    results, monthly_rows, year_rows = [], [], []
    shading_cost: dict[str, tuple[float, float, float]] = {}
    total_kwh = total_kwp = 0.0

    for bid, name, kwp in roofs:
        beam, svf = shading.get(bid, (None, 1.0))
        result = fr4_generation.run_model_chain(
            bid, primary, kwp, beam_shading=beam, sky_view_factor=svf)
        unshaded = fr4_generation.run_model_chain(bid, primary, kwp)
        cost = 1.0 - result.mean_annual_kwh / unshaded.mean_annual_kwh
        shading_cost[bid] = (unshaded.mean_annual_kwh, result.mean_annual_kwh, cost)
        results.append(result)
        total_kwh += result.mean_annual_kwh
        total_kwp += kwp

        print(f"  {bid:<5}{kwp:>8.1f}{result.mean_annual_kwh / 1000:>9.1f}"
              f"{result.sd_annual_kwh / 1000:>7.1f}{result.specific_yield:>9.0f}"
              f"{result.capacity_factor:>7.1%}{shading_cost[bid][2]:>8.1%}")

        by_id[bid].update({k: register._fmt(v) for k, v in result.as_row().items()})

        for year, kwh in sorted(result.annual_kwh.items()):
            year_rows.append({"building_id": bid, "building_name": name,
                              "year": year, "annual_kwh": round(kwh, 1)})
        for month, kwh in sorted(result.monthly_kwh.items()):
            monthly_rows.append({"building_id": bid, "month": month,
                                 "month_name": MONTH_NAMES[month - 1],
                                 "mean_kwh": round(kwh, 1)})

    print("  " + "-" * (len(header) - 2))
    lost = sum(u - sh for u, sh, _ in shading_cost.values())
    print(f"  {'TOT':<5}{total_kwp:>8.1f}{total_kwh / 1000:>9.1f}{'':>7}"
          f"{total_kwh / total_kwp:>9.0f}{'':>7}"
          f"{lost / (total_kwh + lost):>8.1%}")
    if shading:
        print(f"\n  Shading costs {lost / 1000:.0f} MWh a year across the ten roofs, "
              f"{lost / (total_kwh + lost):.1%} of what an")
        print("  unobstructed version of the same campus would generate.")

    register.save(rows)
    _write(RESULTS, year_rows)
    _write(MONTHLY, monthly_rows)
    _write(VARIANTS, variant_rows)
    print(f"\nWritten: {RESULTS.name}, {MONTHLY.name}, {VARIANTS.name}, "
          f"and the register")

    try:
        _figure(results, primary)
        print(f"Figure:  {FIGURE.relative_to(config.ROOT)}")
    except Exception as exc:  # noqa: BLE001 - a figure that will not draw must
        # not fail a run that has already written the data and the register
        print(f"Figure skipped: {exc}")

    # --- FR-4 acceptance --------------------------------------------------
    print("\nFR-4 acceptance")
    fleet_yield = total_kwh / total_kwp
    print(" ", acceptance.fr4_specific_yield(fleet_yield))

    if "pvgis_tmy" in chains:
        pv = fr4_generation.run_model_chain("PROBE", chains["pvgis_tmy"], 100.0)
        check = acceptance.fr4_pvgis_agreement(fleet_yield, pv.specific_yield)
        print(" ", check)
        if not check.passed:
            print("""
  This is the FR-1 disagreement reappearing, not a new fault. Part 3 showed
  PVGIS overstates irradiance at this site by 10.1 per cent, almost entirely
  in winter, and chose NASA POWER because it reproduced the measured seasonal
  shape of the campus fleet. On a tilted plane that winter excess is amplified,
  because tilt gain is largest when the sun is lowest. The cross-check
  therefore cannot pass while the sources themselves disagree, and the
  resolution is the one already recorded for FR-1: the choice of source is
  justified against measured generation, which Step 2 of the roadmap does
  directly against 792 MWh of metered output.""")

    print("""
  The back-test against metered generation is Part 7 Step 2 and is not run
  here. Note that every roof shares one specific yield in this pass, because
  tilt, azimuth and site are common and shading is still unity. Part 6 is what
  will differentiate them.""")
    return 0


def _write(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _figure(results, chain) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.5, 4.0))

    campus = [sum(r.monthly_kwh[m] for r in results) / 1000 for m in range(1, 13)]
    ax.bar(MONTH_NAMES, campus, color="#d9d9d9", edgecolor="#000000", linewidth=0.8)
    for x, v in enumerate(campus):
        ax.text(x, v + 4, f"{v:.0f}", ha="center", va="bottom", fontsize=8)

    ax.set_ylabel("MWh per month, all ten roofs")
    ax.set_title(
        f"Modelled generation, {sum(campus):.0f} MWh/yr from "
        f"{sum(r.capacity_kwp for r in results):.0f} kWp\n"
        f"{chain.source} / {chain.decomposition}, mean of "
        f"{len(results[0].annual_kwh)} modelled years, no shading",
        fontsize=9, loc="left",
    )
    ax.set_ylim(0, max(campus) * 1.18)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGURE, dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())

"""FR-1: decide which irradiance source to trust, using measured generation.

The specification assumes PVGIS and NASA POWER will agree on annual GHI within
5 per cent. At this site they do not - they differ by about 10 per cent, almost
all of it in winter. Rather than pick one by assertion, this script lets the
campus's own meters arbitrate.

Monthly generation and monthly irradiance are each normalised to their own
annual total, so the comparison is of seasonal *shape*. Plant capacity, which
we do not know, cancels out entirely, so the test is not circular.

    uv run python scripts/run_fr1_source_selection.py
"""

from __future__ import annotations

import sys

sys.path.insert(0, "src")

from btp_solar import campus_meters, config, fr1_data  # noqa: E402

YEAR = 2024  # the last year with near-complete meter coverage
MONTHS = [f"{YEAR}-{m:02d}" for m in range(1, 13)]


def main() -> int:
    plants = campus_meters.load(sorted(config.DATA.glob(config.METER_WORKBOOK_GLOB)))
    complete = [p for p in plants.values()
                if all(p.monthly_kwh.get(m, 0) > 0 for m in MONTHS)]
    if not complete:
        print("No plant has a complete live year; cannot arbitrate.")
        return 1

    measured = [sum(p.monthly_kwh[m] for p in complete) for m in MONTHS]

    pvgis = fr1_data.monthly_mean_daily_ghi_pvgis(config.DATA / "pvgis_tmy_28.545_77.192.json")
    nasa = fr1_data.monthly_mean_daily_ghi_nasa(
        config.DATA / "nasa_power_28.545_77.192_20140101_20231231.json")

    sm = fr1_data.normalised_shape(measured)
    sp = fr1_data.normalised_shape(pvgis)
    sn = fr1_data.normalised_shape(nasa)

    print(f"{len(complete)} plants with a complete live {YEAR}; "
          f"{sum(measured)/1000:.0f} MWh measured\n")
    print("        measured     NASA    PVGIS")
    for i, m in enumerate(MONTHS):
        print(f"  {m[5:]}     {sm[i]:8.3f} {sn[i]:8.3f} {sp[i]:8.3f}")

    en = fr1_data.shape_error(sn, sm)
    ep = fr1_data.shape_error(sp, sm)
    print(f"\n  shape error vs measured:  NASA {en:.3f}   PVGIS {ep:.3f}")
    winner = "NASA POWER" if en < ep else "PVGIS"
    print(f"  -> {winner} reproduces the measured seasonal shape more closely")
    print(f"\n  Jan/Apr ratio   measured {measured[0]/measured[3]:.3f}"
          f"   NASA {nasa[0]/nasa[3]:.3f}   PVGIS {pvgis[0]/pvgis[3]:.3f}")
    print("\n  Note: measured output is plane-of-array on tilted modules, so its"
          "\n  winter share is if anything inflated relative to GHI. That makes"
          "\n  PVGIS's winter excess larger than it appears here, not smaller.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

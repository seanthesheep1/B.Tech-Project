"""Parse the campus solar meter workbooks and write the monthly series.

    uv run python scripts/run_campus_meters.py

Writes data/campus_solar_monthly.csv and prints a fleet summary
including which plants have stopped generating.
"""

from __future__ import annotations

import csv
import sys

sys.path.insert(0, "src")

from btp_solar import campus_meters, config  # noqa: E402

WORKBOOKS = sorted(config.DATA.glob(config.METER_WORKBOOK_GLOB))
OUT = config.CAMPUS_METERS_CSV


def main() -> int:
    if not WORKBOOKS:
        print(f"No meter workbooks matching {config.METER_WORKBOOK_GLOB!r} in data/")
        return 1

    plants = campus_meters.load(WORKBOOKS)
    months = sorted({m for p in plants.values() for m in p.monthly_kwh})
    dropped = sum(len(p.dropped) for p in plants.values())
    readings = sum(len(p.readings) for p in plants.values())

    print(f"{len(plants)} meters, {readings:,} clean readings over {len(months)} months "
          f"({months[0]} to {months[-1]})")
    print(f"{dropped} readings dropped as transcription errors or blanks\n")

    header = f"{'location':<34}{'meter':>10}{'MF':>4}{'2024':>8}{'2025':>8}{'2026':>8}  status"
    print(header)
    print("-" * len(header))

    rows = []
    for plant in sorted(plants.values(), key=lambda p: -p.annual_kwh(2024)):
        y24, y25, y26 = (plant.annual_kwh(y) / 1000 for y in (2024, 2025, 2026))
        # 2026 covers four months, so compare against a third of the best year
        best = max(y24, y25)
        status = ("STOPPED" if y26 < max(0.5, 0.05 * best)
                  else "weak" if y26 < 0.15 * best else "generating")
        print(f"{plant.location[:33]:<34}{plant.meter:>10}{plant.meter_factor:>4.0f}"
              f"{y24:>8.1f}{y25:>8.1f}{y26:>8.1f}  {status}")
        for month, kwh in sorted(plant.monthly_kwh.items()):
            rows.append({"meter": plant.meter, "location": plant.location,
                         "meter_factor": plant.meter_factor, "month": month,
                         "kwh": round(kwh, 1)})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["meter", "location", "meter_factor",
                                                "month", "kwh"])
        writer.writeheader()
        writer.writerows(rows)

    totals = {y: sum(p.annual_kwh(y) for p in plants.values()) / 1000 for y in (2024, 2025, 2026)}
    print("-" * len(header))
    print(f"{'TOTAL MWh':<48}{totals[2024]:>8.1f}{totals[2025]:>8.1f}{totals[2026]:>8.1f}")
    print(f"\nWrote {len(rows)} rows to {OUT.relative_to(config.ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

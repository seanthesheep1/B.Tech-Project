"""What tilt actually buys, once row spacing is counted against yield.

    uv run python scripts/run_tilt_tradeoff.py

The project inherited a 15 degree tilt as a design assumption, flagged from the
first week as "confirm against a real campus installation". Two things since
have made that worth settling with a number rather than a default:

1. The FR-4 back-test found the metered fleet shows **no winter tilt gain at
   all**, and sweeping the model's tilt reproduces the measured seasonal shape
   best at 0 to 5 degrees - evidence the existing campus arrays are mounted
   flat.
2. Tilt is not free. Tilted rows shade each other, so they must be spaced
   apart, and the ground coverage ratio derived in Part 4 falls as tilt rises.
   A steeper array earns more per kilowatt and fits fewer kilowatts on a roof.

The right measure for a roof of fixed area is therefore **energy per square
metre of available roof**, not specific yield, and that is what this reports.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "src")

from btp_solar import config, fr4_generation, register
from btp_solar.solar_geometry import design_sun_position, ground_coverage_ratio

NASA = config.DATA / "nasa_power_28.545_77.192_20140101_20231231.json"
TILTS = (0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 28.5)


def main() -> int:
    if not NASA.exists():
        print(f"missing {NASA.name}")
        return 1

    net_area = sum(
        float(r["net_available_area_m2"])
        for r in register.load()
        if r["role"] == "candidate" and r["net_available_area_m2"].strip()
    )
    print(f"Net available roof across the ten candidates: {net_area:,.0f} m2")
    print(f"Design sun: {config.SHADING_CRITERION}, "
          f"packing factor {config.PACKING_FACTOR}, "
          f"{config.MODULE_POWER_DENSITY_W_PER_M2:.0f} W/m2\n")

    sun = design_sun_position(config.SITE_LAT, config.SHADING_CRITERION)
    weather = fr4_generation.load_nasa_hourly(NASA)

    header = (f"  {'tilt':>6}{'GCR':>7}{'kWp':>9}{'kWh/kWp':>9}"
              f"{'MWh/yr':>9}{'kWh/m2':>9}")
    print(header)
    print("  " + "-" * (len(header) - 2))

    best = None
    rows = []
    for tilt in TILTS:
        gcr = 1.0 if tilt == 0 else ground_coverage_ratio(tilt, sun)
        module_area = net_area * gcr * config.PACKING_FACTOR
        kwp = module_area * config.MODULE_POWER_DENSITY_W_PER_M2 / 1000.0

        chain = fr4_generation.build_site_chain(weather, tilt_deg=tilt)
        result = fr4_generation.run_model_chain("sweep", chain, kwp)
        per_m2 = result.mean_annual_kwh / net_area

        mark = "  <- current" if abs(tilt - config.MODULE_TILT_DEG) < 0.01 else ""
        print(f"  {tilt:>5.1f}°{gcr:>7.3f}{kwp:>9.0f}{result.specific_yield:>9.0f}"
              f"{result.mean_annual_kwh / 1000:>9.0f}{per_m2:>9.0f}{mark}")
        rows.append((tilt, gcr, kwp, result.specific_yield, result.mean_annual_kwh, per_m2))
        if best is None or per_m2 > best[5]:
            best = rows[-1]

    current = next(r for r in rows if abs(r[0] - config.MODULE_TILT_DEG) < 0.01)
    gain = best[5] / current[5] - 1.0
    print(f"""
  Flat modules need no inter-row spacing, so the ground coverage ratio rises
  from {current[1]:.3f} at {current[0]:.0f}° to 1.000 at 0°. That is {best[2] / current[2] - 1:.0%} more capacity on the
  same roof, at {1 - best[3] / current[3]:.0%} lower yield per kilowatt.

  Per square metre of available roof - the quantity a fixed campus actually
  constrains - **{best[0]:.0f}° wins by {gain:.0%}**: {best[5]:.0f} kWh/m2/yr against {current[5]:.0f}.

  Caveats before this changes the design. Flat modules soil faster and are not
  self-cleaning in rain, which the flat 3% soiling figure in config.LOSSES does
  not capture and which Delhi's dust would punish. Mounting cost, wind load and
  drainage all differ. And the ten roofs' obstruction shading was computed at
  {config.MODULE_TILT_DEG:.0f}°; a denser flat array would see somewhat more of it.

  What this does establish is that **the 15° assumption is not free and was
  never tested**, and that the campus's own installers appear to have reached
  the same conclusion. Measure the tilt of a real array in the imagery during
  the census and the question closes.""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

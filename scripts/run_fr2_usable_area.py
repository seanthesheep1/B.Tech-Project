"""FR-2: run the usable-area chain for every digitised building.

Reads the hand-digitised geometry from the register, computes the area chain,
and writes the derived columns back. Buildings whose geometry has not been
digitised yet are skipped and reported.

    uv run python scripts/run_fr2_usable_area.py
"""

from __future__ import annotations

import sys

sys.path.insert(0, "src")

from btp_solar import config, fr2_usable_area, register
from btp_solar.solar_geometry import design_sun_position

GEOMETRY_COLUMNS = ("gross_roof_area_m2", "obstruction_area_m2", "roof_perimeter_m")

# Superseded once the roofs were digitised. This script re-derives the area
# chain from the register's own rounded columns, while run_fr2_from_gpkg.py
# derives it from the full-precision geometry in roofs.gpkg. The two disagree
# in the fourth significant figure - enough to move the campus total between
# 2220.6 and 2220.4 kWp depending on which ran last, which is exactly the kind
# of drift the register exists to prevent. Only one script may own a column.
SUPERSEDED_BY = "scripts/run_fr2_from_gpkg.py"


def main() -> int:
    gpkg = config.DATA / "roofs.gpkg"
    if gpkg.exists():
        print(f"""Refusing to run: {gpkg.name} exists.

The roofs have been digitised, so the area chain must be derived from that
geometry rather than from the register's rounded columns. Use

    uv run python {SUPERSEDED_BY}

which owns these columns. Running both leaves the campus total depending on
whichever ran last.""")
        return 1

    sun = design_sun_position(config.SITE_LAT, config.SHADING_CRITERION)
    print(
        f"Design sun position ({sun.label}): elevation {sun.elevation_deg:.2f} deg, "
        f"azimuth {sun.azimuth_from_south_deg:.2f} deg from south"
    )
    print(f"Tilt {config.MODULE_TILT_DEG} deg, setback {config.SETBACK_M} m\n")

    rows = register.load()
    done, skipped = 0, []

    for row in rows:
        if not all(row.get(c, "").strip() for c in GEOMETRY_COLUMNS):
            skipped.append(row["building_id"])
            continue

        roof = fr2_usable_area.RoofMeasurements(
            building_id=row["building_id"],
            gross_roof_area_m2=float(row["gross_roof_area_m2"]),
            obstruction_area_m2=float(row["obstruction_area_m2"]),
            roof_perimeter_m=float(row["roof_perimeter_m"]),
        )
        result = fr2_usable_area.compute(roof)
        row.update({k: register._fmt(v) for k, v in result.as_row().items()})
        done += 1
        print(
            f"{roof.building_id}: {result.installable_capacity_kwp:8.1f} kWp  "
            f"(GCR {result.ground_coverage_ratio:.3f}, "
            f"{result.usable_fraction_of_roof:.1%} of gross roof)"
        )

    if done:
        register.save(rows)
        print(f"\nRegister updated for {done} building(s).")
    if skipped:
        print(f"Not yet digitised, skipped: {', '.join(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

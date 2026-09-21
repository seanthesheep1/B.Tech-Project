"""FR-1: fetch both irradiance sources and run the 5 per cent agreement check.

    uv run python scripts/run_fr1_data.py
"""

from __future__ import annotations

import sys

sys.path.insert(0, "src")

from btp_solar import acceptance, fr1_data  # noqa: E402


def main() -> int:
    print("Fetching PVGIS TMY ...")
    pvgis_path = fr1_data.fetch_pvgis_tmy()
    print(f"  cached at {pvgis_path}")

    print("Fetching NASA POWER hourly ...")
    nasa_path = fr1_data.fetch_nasa_power()
    print(f"  cached at {nasa_path}")

    pvgis_ghi = fr1_data.annual_ghi_from_pvgis(pvgis_path)
    nasa_ghi = fr1_data.annual_ghi_from_nasa(nasa_path)

    result = acceptance.fr1_irradiance_agreement(pvgis_ghi, nasa_ghi)
    print()
    print(result)
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

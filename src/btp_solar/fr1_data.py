"""FR-1: data acquisition and consolidation.

Week 2 of the workflow. Assembles footprints, heights and two independent
hourly irradiance series for the campus point, and checks that the two sources
agree to within 5 per cent on annual global horizontal irradiation.

The fetchers below hit public endpoints; both cache into data/ so a
rerun is offline and the report is reproducible from the cached files.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import config

PVGIS_TMY_URL = "https://re.jrc.ec.europa.eu/api/v5_2/tmy"
NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"


def fetch_pvgis_tmy(
    lat: float = config.SITE_LAT,
    lon: float = config.SITE_LON,
    cache_dir: Path = config.DATA,
) -> Path:
    """Download the PVGIS typical meteorological year for the site.

    Returns the path to the cached JSON. Hourly GHI, DNI, DHI, temperature and
    wind speed for a typical year.
    """
    import requests

    cache_dir.mkdir(parents=True, exist_ok=True)
    out = cache_dir / f"pvgis_tmy_{lat}_{lon}.json"
    if out.exists():
        return out

    response = requests.get(
        PVGIS_TMY_URL,
        params={"lat": lat, "lon": lon, "outputformat": "json", "browser": 0},
        timeout=120,
    )
    response.raise_for_status()
    out.write_text(json.dumps(response.json(), indent=1), encoding="utf-8")
    return out


def fetch_nasa_power(
    lat: float = config.SITE_LAT,
    lon: float = config.SITE_LON,
    start: str = "20140101",
    end: str = "20231231",
    cache_dir: Path = config.DATA,
) -> Path:
    """Download the NASA POWER hourly series for the site as the second source."""
    import requests

    cache_dir.mkdir(parents=True, exist_ok=True)
    out = cache_dir / f"nasa_power_{lat}_{lon}_{start}_{end}.json"
    if out.exists():
        return out

    response = requests.get(
        NASA_POWER_URL,
        params={
            "parameters": "ALLSKY_SFC_SW_DWN,T2M,WS2M",
            "community": "RE",
            "latitude": lat,
            "longitude": lon,
            "start": start,
            "end": end,
            "format": "JSON",
        },
        timeout=300,
    )
    response.raise_for_status()
    out.write_text(json.dumps(response.json(), indent=1), encoding="utf-8")
    return out


def annual_ghi_from_pvgis(path: Path) -> float:
    """Annual global horizontal irradiation in kWh/m2/yr from a cached TMY file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    hourly = payload["outputs"]["tmy_hourly"]
    return sum(float(h["G(h)"]) for h in hourly) / 1000.0


def annual_ghi_from_nasa(path: Path) -> float:
    """Mean annual GHI in kWh/m2/yr from a cached NASA POWER hourly file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    series = payload["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
    values = [v for v in series.values() if v is not None and v > -900]
    years = len(values) / (365.25 * 24)
    return sum(values) / 1000.0 / years


def monthly_mean_daily_ghi_pvgis(path: Path) -> list[float]:
    """Mean daily GHI in Wh/m2 for each calendar month, from a cached TMY."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    totals, hours = [0.0] * 12, [0] * 12
    for row in payload["outputs"]["tmy_hourly"]:
        m = int(row["time(UTC)"][4:6]) - 1
        totals[m] += float(row["G(h)"])
        hours[m] += 1
    return [t / (h / 24) for t, h in zip(totals, hours)]


def monthly_mean_daily_ghi_nasa(path: Path) -> list[float]:
    """Mean daily GHI in Wh/m2 for each calendar month, from cached POWER hourly."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    series = payload["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
    totals, hours = [0.0] * 12, [0] * 12
    for stamp, value in series.items():
        if value is None or value < -900:
            continue
        m = int(stamp[4:6]) - 1
        totals[m] += float(value)
        hours[m] += 1
    return [t / (h / 24) for t, h in zip(totals, hours)]


def normalised_shape(monthly: list[float]) -> list[float]:
    """Monthly values as fractions of their own total.

    Comparing shapes rather than levels is what lets measured generation
    arbitrate between two irradiance sources: the plants' capacity, which we do
    not know, cancels out.
    """
    total = sum(monthly)
    if total <= 0:
        raise ValueError("cannot normalise an empty or negative series")
    return [v / total for v in monthly]


def shape_error(candidate: list[float], reference: list[float]) -> float:
    """Total absolute deviation between two normalised monthly shapes."""
    if len(candidate) != len(reference):
        raise ValueError("series must be the same length")
    return sum(abs(c - r) for c, r in zip(candidate, reference))


# --- footprints ----------------------------------------------------------
# Week 2. Both sources are downloaded and reconciled by hand in QGIS in week 3;
# OSM is usually right in outline and wrong in detail, Google Open Buildings the
# reverse. The corrected footprint and its source go into the register.
def load_footprints(path: Path):  # pragma: no cover - needs geopandas and data
    """Read a footprint layer into the working CRS. Implement in week 2."""
    import geopandas as gpd

    return gpd.read_file(path).to_crs(config.CRS_WORKING)

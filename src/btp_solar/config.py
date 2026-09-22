"""Project-wide constants and paths.

Every number here is a design decision that must be justified in the report.
Where the specification fixes a value, the clause is cited.
"""

from __future__ import annotations

from pathlib import Path

# --- paths ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
# Every data file lives in this one folder: downloaded inputs, the workbooks
# from the Estate Office, and the products this code writes.
DATA = ROOT / "data"
REGISTER_CSV = DATA / "building_register.csv"
REGISTER_SCHEMA = DATA / "register_schema.yml"
CAMPUS_METERS_CSV = DATA / "campus_solar_monthly.csv"
METER_WORKBOOK_GLOB = "Solar*"
QGIS_DIR = ROOT / "qgis"
REPORTS = ROOT / "reports"

# --- site ----------------------------------------------------------------
# Specification FR-1: irradiance series requested for this point.
SITE_LAT = 28.545  # degrees north
SITE_LON = 77.192  # degrees east
SITE_ELEVATION_M = 229.0  # PVGIS DEM for this point, 2026-09-22
SITE_TZ = "Asia/Kolkata"

# Projected CRS for all area and length computation. WGS 84 / UTM zone 43N.
# Areas must never be computed in EPSG:4326.
CRS_WORKING = "EPSG:32643"
CRS_GEOGRAPHIC = "EPSG:4326"

# --- array design assumptions -------------------------------------------
# These drive FR-2 usable area. Each is an assumption to defend, not a default
# to accept silently; record any change in docs/decisions.md.
SETBACK_M = 1.0              # fire/maintenance clearance from every roof edge
MODULE_TILT_DEG = 15.0       # flat-roof ballasted racking, south facing
MODULE_AZIMUTH_DEG = 180.0   # true south
PACKING_FACTOR = 0.85        # walkways, inverter pads, cable trays within the array field
MODULE_POWER_DENSITY_W_PER_M2 = 215.0  # ~22% efficient module, glass area basis

# No-shading design criterion for inter-row spacing (FR-2).
# "winter_noon"  : no row-to-row shading at solar noon on the winter solstice
# "winter_9_to_3": no row-to-row shading between 09:00 and 15:00 solar time on
#                  the winter solstice. This is the stricter, industry-standard
#                  criterion and is the project default.
SHADING_CRITERION = "winter_9_to_3"

# --- capacity back-estimation (used where nameplate kWp is unknown) ------
# Installed capacity is absent from the Estate Office workbooks, so it is
# back-calculated from monthly energy. Both values below are assumptions and
# every figure derived from them must be labelled an estimate.
# See docs/decisions.md, 2026-09-22, for the circularity this must not be used
# for: capacity derived this way can never validate the FR-4 generation model.
PEAK_SUN_HOURS = {  # kWh/m2/day on a 15 deg south plane at Delhi, by month
    1: 4.8, 2: 5.5, 3: 6.2, 4: 6.6, 5: 6.5, 6: 5.6,
    7: 4.6, 8: 4.5, 9: 5.2, 10: 5.7, 11: 5.1, 12: 4.6,
}
PERFORMANCE_RATIO = 0.78
MIN_MONTHS_FOR_CAPACITY = 3   # below this the median is not meaningful
OUTAGE_MONTHS = 6             # idle this long counts as stopped, not seasonal

# --- loss stack (FR-4) ---------------------------------------------------
# Itemised rather than a single lumped figure, as the specification requires.
LOSSES = {
    "soiling": 0.030,       # Delhi dust; seasonal, to be refined from literature
    "mismatch": 0.020,
    "wiring_dc": 0.015,
    "wiring_ac": 0.010,
    "inverter_clipping": 0.005,
    "availability": 0.020,
    "light_induced_degradation": 0.015,
}

# --- acceptance thresholds (from the specification) ----------------------
IRRADIANCE_AGREEMENT_TOL = 0.05        # FR-1: PVGIS vs NASA POWER annual GHI
SEGMENTATION_MIN_IOU = 0.75            # FR-2
SHADOW_LENGTH_TOL = 0.15               # FR-3
SPECIFIC_YIELD_RANGE = (1300.0, 1600.0)  # FR-4, kWh/kWp/yr
PVGIS_AGREEMENT_TOL = 0.10             # FR-4
FEEDER_LOADING_TOL = 0.15              # FR-5, modelled vs billed

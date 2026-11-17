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

# --- generation model chain (FR-4) --------------------------------------
# New assumptions introduced by Part 7. Each is recorded in docs/decisions.md
# with its basis, exactly as the FR-2 design values were.
IRRADIANCE_SOURCE = "nasa_power"   # chosen in Part 3 against measured generation
DECOMPOSITION_MODEL = "dirint"     # NASA POWER supplies global irradiance only,
                                   # so beam and diffuse must be separated before
                                   # transposition. "erbs" is the sensitivity case.
TRANSPOSITION_MODEL = "perez"      # specification FR-4
GROUND_ALBEDO = 0.20               # concrete and gravel roof surround
MODULE_TEMP_COEFF_PER_C = -0.0035  # -0.35 %/degC, typical mono-PERC module
INVERTER_EFFICIENCY = 0.96         # flat conversion efficiency; clipping is carried
                                   # in LOSSES, since inverter sizing is not yet chosen
WIND_SHEAR_EXPONENT = 0.14         # power law, to bring 10 m wind down to 2 m
MODULE_WIND_HEIGHT_M = 2.0         # the height the cell-temperature model expects

# --- shading (FR-3) ------------------------------------------------------
# The far horizon was shown flat by the PVGIS profile (0.0-1.9 deg in every
# direction, docs/decisions.md 2026-09-22), so all shading here is local:
# neighbouring buildings, the roof's own parapet, and objects on the roof.
PARAPET_HEIGHT_M = 1.0        # above the roof surface. ASSUMED; measure on site
ARRAY_MID_HEIGHT_M = 0.5      # module mid-point above the roof, 15 deg racking
HORIZON_BINS = 360            # one degree of azimuth per bin
SHADING_SAMPLE_SPACING_M = 5.0  # grid over the usable area of each roof
CASTER_RADIUS_M = 300.0       # a 30 m block at 6 deg sun casts 285 m; beyond
                              # this the beam is too weak to matter
DEFAULT_STOREY_HEIGHT_M = 3.5
DEFAULT_NEIGHBOUR_HEIGHT_M = 10.5   # 3 storeys, where OSM gives no height at all

# Heights of the objects digitised on the roofs in Part 4. Every one is an
# assumption by type, not a measurement, and each is worth a site check.
OBSTRUCTION_HEIGHTS_M = {
    "water_tank": 3.0,     # typically on a stand
    "stair_room": 3.0,
    "lift_room": 4.0,
    "solar_panel": 1.5,    # existing arrays shade too
    "other": 2.5,          # unidentified; the mid of the range above
    "open_air": 0.0,       # a hole in the roof, not an object: casts nothing
}

# --- the solar alarm ------------------------------------------------------
# A plant is called underperforming when its share of the fleet's output falls
# well below its own usual share and stays there. Share is used rather than
# kWh so that weather cancels: a dull month pulls every plant down together.
UNDERPERFORMANCE_RATIO = 0.60    # below 60% of its baseline share
UNDERPERFORMANCE_MONTHS = 2      # for this many months running, so one odd
                                 # reading is not an alarm
MIN_MONTHS_FOR_BASELINE = 6      # below this a plant has no baseline yet
BASELINE_MONTHS = 12             # the baseline is how a plant behaved when the
                                 # record opened, NOT its median over all time.
                                 # Director's Lodge died in month seven of
                                 # twenty-eight, so its all-time median IS the
                                 # dead level and it would measure itself
                                 # against its own corpse.
COLLAPSE_RATIO = 0.05            # below this of baseline is not underperforming,
                                 # it has effectively stopped - even though the
                                 # meter still creeps a few kWh a month and so
                                 # never looks idle
TARIFF_INR_PER_KWH = 8.0         # PROVISIONAL. DERC institutional rate; D38
                                 # has not arrived, so every rupee figure in
                                 # this project is indicative and says so.

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
# FR-4 back-test. The specification says "back-tested against metered output"
# without quantifying it, and the naive specific-yield test is circular because
# plant capacity is itself back-calculated from generation (docs/decisions.md,
# 2026-09-22). The test used instead compares the *shape* of the modelled and
# measured years, each normalised to its own annual total, so capacity cancels.
# The measure is the total absolute deviation between two shapes that each sum
# to 1; half of it is the fraction of annual energy placed in the wrong month.
# The threshold below therefore allows a tenth of annual energy to be
# misallocated across the year. It is OUR criterion, not the specification's,
# and needs the supervisor's agreement before the final report leans on it.
SHAPE_AGREEMENT_TOL = 0.20             # FR-4, total absolute monthly deviation
FEEDER_LOADING_TOL = 0.15              # FR-5, modelled vs billed

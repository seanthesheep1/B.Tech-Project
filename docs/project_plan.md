# Project plan: data files and work parts

Rooftop Solar Potential Mapping of the IIT Delhi Campus.
Every data file the project touches is listed once here with an ID. Each work
part below names the IDs it consumes and the IDs it produces, so at any point
it is clear what is blocked and on what.

Status legend: **HAVE** in hand · **GET** we can fetch ourselves · **ASK**
must come from the Estate Office or the supervisor · **MAKE** we produce it.

---

## 1. The data file list

### Files we have

| ID | File name | Status | What it is |
|----|-----------|--------|------------|
| D01 | `Solar reading jan-24 to dec-24.xlsm` | HAVE | Daily generation-meter readings, 12 monthly sheets, Jan–Dec 2024. From the supervisor. |
| D02 | `Solar meter Report-2025 & 2026.xlsx` | HAVE | Same format, 16 monthly sheets, Jan 2025 – Apr 2026. From the supervisor. |
| D03 | `campus_solar_monthly.csv` | HAVE | 687 rows. Cleaned monthly kWh per plant, parsed from D01 + D02. |
| D04 | `building_register.csv` | HAVE | The audit trail. One row per building, one column per computed number. Currently 12 empty template rows. |
| D05 | `register_schema.yml` | HAVE | Data dictionary for D04. Every column must have an entry or a test fails. |

### Files we can fetch ourselves

| ID | File name | Status | What it is |
|----|-----------|--------|------------|
| D06 | `pvgis_tmy_28.545_77.192.json` | GET | PVGIS typical meteorological year. Hourly GHI, DNI, DHI, temperature, wind. |
| D07 | `nasa_power_28.545_77.192.json` | GET | NASA POWER hourly series. The independent second irradiance source. |
| D08 | `footprints_osm.geojson` | GET | OpenStreetMap building outlines for the campus bounding box. |
| D09 | `footprints_google_open_buildings.csv` | GET | Google Open Buildings footprints with height estimates. |
| D10 | `campus_imagery/` | GET | Sub-metre satellite tiles. **Record the acquisition date of every scene** — D31 validation depends on a dated image. |
| D11 | `inria_aerial_dataset/` | GET | INRIA aerial image labelling dataset, training data for the segmentation model. |

### Files we must ask for

| ID | File name | Status | Priority | What it is |
|----|-----------|--------|----------|------------|
| D12 | `existing_pv_plant_schedule.xlsx` | ASK | **1 — blocking** | Per plant: meter no., building, **installed kWp**, module type and count, inverter, tilt, azimuth, commissioning date. |
| D13 | `buildings_without_solar.xlsx` | ASK | 2 | List of campus buildings with no rooftop PV, to pick candidates from. |
| D14 | `meter_factor_confirmation` | ASK | 2 | Written confirmation that register reading × MF = kWh, and that the MF row applies to the Jan–Jun 2024 sheets too. |
| D15 | `hostel_meter_readings_2025` | ASK | 2 | The missing year. D02's 2025 sheets carry 17 columns, not 31 — all 13 hostel meters absent. |
| D16 | `electricity_bills_2024_2025.xlsx` | ASK | 3 | Monthly consumption per building, two years. We currently hold **zero** consumption data. |
| D17 | `campus_single_line_diagram.pdf` | ASK | 3 | Campus SLD, PDF or DWG. |
| D18 | `transformer_schedule.xlsx` | ASK | 3 | Rating in kVA, location, and which buildings each transformer / 11 kV feeder supplies. |
| D19 | `feeder_layout.pdf` | ASK | 3 | 11 kV feeder routing. |
| D20 | `plant_outage_log` | ASK | 3 | Why six plants stopped: Central Library, Amaltas Guest House, Main Building, Vishwakarma ×2, SIT. |
| D21 | `meter_replacement_log.xlsx` | ASK | 4 | Explains register resets and the 29490555 → 42490555 relabelling. |
| D22 | `net_metering_agreement.pdf` | ASK | 4 | Is generation exported or consumed behind the meter? Decides how D16 is interpreted. |
| D23 | `cable_schedule.xlsx` | ASK | 4 | Cable sizes and approximate lengths on the study feeder. |
| D24 | `interval_meter_data.csv` | ASK | 5 — optional | Hourly or 15-minute consumption, if it exists. |
| D25 | `campus_footprints.dwg` | ASK | 5 — optional | Campus CAD. Would replace D08/D09 if accurate. |
| D26 | `roof_plans_photos/` | ASK | 5 — optional | Roof plans or photos of tanks, stair rooms, existing arrays. |
| D27 | `previous_solar_survey.pdf` | ASK | 5 — optional | Any earlier rooftop solar survey. |

### Files we will produce

| ID | File name | Status | What it is |
|----|-----------|--------|------------|
| D28 | `campus.qgz` | MAKE | The QGIS project. |
| D29 | `roofs.gpkg` | MAKE | Digitised roof outlines, obstructions, setback buffers, array fields. |
| D30 | `dsm.tif` | MAKE | Digital surface model, footprints extruded by height. |
| D31 | `shading_factors.csv` | MAKE | Hourly shading factor per roof, from UMEP. |
| D32 | `generation_results.csv` | MAKE | Annual energy, specific yield, capacity factor per building. |
| D33 | `feeder_model.dss` | MAKE | The OpenDSS feeder model. |
| D34 | `feeder_results.csv` | MAKE | Voltage rise, reverse power flow, losses, hosting capacity. |
| D35 | `campus_heatmap.png` | MAKE | Campus map coloured by annual specific yield. |

**Totals: 5 held · 6 fetchable · 16 to request · 8 to produce.**

---

## 2. The work parts

### Part 1 — Lock the scope and fire off the data requests

**Do:** Walk the campus and confirm which buildings are candidates. Send the
data request, ordered by the priority column above — D12 first, because
without installed kWp nothing in Part 3 can be validated. Fill the identity
columns of D04 for every building chosen.

**Uses:** D03 (tells you which 29 roofs are already taken), D13
**Produces:** D04 populated with names, categories, roles
**Done when:** the supervisor has confirmed the building list and the requests are acknowledged.

> **Scope change to raise first.** The specification assumes 8–10 candidates
> with no PV plus **two** existing installations for validation. D03 shows
> **29 locations already carry PV**, about 20 of them generating. The
> validation set is an order of magnitude better than planned, and the
> untapped set is smaller. Settle this before anything else is built on it.

---

### Part 2 — Characterise the existing fleet *(mostly done)*

**Do:** Parse the supervisor's workbooks, repair the transcription errors,
produce monthly energy per plant, and identify which plants are dead.

**Uses:** D01, D02
**Produces:** D03
**Status:** **complete.** 17,006 readings parsed, 97 dropped as decimal slips,
blanks-as-zero and text dates. 31 plants, Jan 2024 – Apr 2026. Six plants
found stopped. Run `make` target `run_campus_meters.py` to reproduce.

**Still blocked:** turning this into specific yield needs D12. Confirming the
units needs D14. Explaining the 2025 gap needs D15, the outages D20, the meter
relabelling D21.

---

### Part 3 — Acquire the base geospatial and irradiance data

**Do:** Download both irradiance sources and check they agree on annual GHI
within 5%. Download both footprint sources. Collect dated satellite imagery.

**Uses:** —
**Produces:** D06, D07, D08, D09, D10
**Acceptance (FR-1):** the two irradiance sources agree within 5%, and every
candidate building carries a corrected footprint and a height with a recorded source.
**Blocked by:** nothing. **This can start today.**

---

### Part 4 — Digitise the roofs and derive usable area

**Do:** Trace every roof outline and every object on it — water tanks, stair
rooms, AC plant, lift rooms, solar water heaters. Apply the 1 m setback as a
negative buffer. Run the area chain to installable kWp.

**Uses:** D08, D09, D10, D28, D04
**Produces:** D29, D04 gains the usable-area columns
**Acceptance (FR-2):** usable area derived from a documented setback and ground
coverage ratio, not an assumed percentage.
**Status:** the maths is built and tested — GCR 0.707 at 15° tilt, ~50% of
gross roof. Only the digitising is outstanding.
**Blocked by:** nothing but Part 1's building list.

---

### Part 5 — Rooftop segmentation model

**Do:** Train a segmentation network on INRIA, run it on campus imagery,
compare against the hand-digitised truth from Part 4.

**Uses:** D10, D11, D29
**Produces:** segmentation accuracy report
**Acceptance (FR-2):** IoU ≥ 0.75 against manual ground truth.
**Note:** the hand-drawn version stays the official one. If the model
underperforms, that is still a result — report where it failed and why.

---

### Part 6 — Shading analysis

**Do:** Extrude footprints to a DSM, add parapets and tree canopy, run UMEP for
hourly shading factors across the year. Validate against a shadow measured in a
dated satellite image.

**Uses:** D29, D09 (heights), D10 (**the dated image**)
**Produces:** D30, D31
**Acceptance (FR-3):** modelled shadow within 15% of the observed one.

---

### Part 7 — Generation modelling and validation

**Do:** pvlib model chain per building — Perez transposition, explicit cell
temperature, itemised loss stack. Apply the Part 6 shading factors. Then
back-test against the real fleet.

**Uses:** D06, D31, D04, and **D12 + D03 for validation**
**Produces:** D32, D35
**Acceptance (FR-4):** specific yield 1300–1600 kWh/kWp/yr, within 10% of PVGIS,
back-tested against metered output.
**Blocked by:** **D12.** Without installed kWp the back-test cannot run at all —
28 months of generation data with no capacity to divide by. This is the single
most important missing file in the project.

---

### Part 8 — Feeder impact study

**Do:** Build one 11 kV feeder in OpenDSS with transformers, cable lengths and
per-building load profiles. Run the annual time series with and without solar.
Find voltage rise, reverse power flow, and hosting capacity.

**Uses:** D17, D18, D19, D23, D16, D22, D32
**Produces:** D33, D34
**Acceptance (FR-5):** base-case loading within 15% of billed consumption.
**Blocked by:** D16, D17, D18. If they never arrive, the specification's own
mitigation applies — build a representative feeder from transformer ratings and
map distances, and declare every assumption.

> **Method note.** D01/D02 are *daily* totals, so they cannot give the hourly
> generation shape this part needs. Model the shape with pvlib and calibrate it
> against the daily totals — and say so explicitly in the report.

---

### Part 9 — Synthesis and report

**Do:** Ranked table of untapped buildings by capacity and yield, campus-level
MWp and MWh, hosting capacity, payback and levelised cost, avoided emissions.
Clean code that regenerates every figure from the raw data.

**Uses:** everything
**Produces:** the interim report

---

## 3. What is blocked on what

| Part | Can start now? | Blocked by |
|------|----------------|------------|
| 1 | **yes** | — |
| 2 | done | D12, D14, D15, D20, D21 to go further |
| 3 | **yes** | — |
| 4 | **yes** (after Part 1's list) | — |
| 5 | yes | Part 4 ground truth |
| 6 | yes | Part 4 |
| 7 | partly | **D12** for validation |
| 8 | no | D16, D17, D18 |
| 9 | no | everything above |

**Three parts can start today and need nothing from anybody: 1, 3 and 4.**
The one request that unblocks the most downstream work is **D12**.

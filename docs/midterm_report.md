---
lang: en-GB
---

![](reports/figures/iitd_logo.png){width=48mm}

# Rooftop Solar Potential Mapping of the IIT Delhi Campus

## B.Tech Project — Mid-term Review Report

**Department of Electrical Engineering**\
**Indian Institute of Technology Delhi**

---

**Submitted by**

| | |
|---|---|
| Tejas Suresh Kamble | 2023EE10974 |
| Surbhi Rathore | 2023EE11224 |

**Supervisor**

Prof. Yashasvi Bansal\
Department of Electrical Engineering, IIT Delhi

---

**Review period:** 18 August 2026 – 31 October 2026\
**Report date:** 24 September 2026\
**Status at mid-term:** 4 of 9 work parts complete

**Project repository:** <https://github.com/seanthesheep1/B.Tech-Project.git>

*All code, data and figures in this report are reproducible from the repository above.
Every number quoted traces to `data/building_register.csv`, `data/roofs.gpkg`, or the
generation-meter workbooks, through a named script.*

<div class="pagebreak"></div>

# Abstract

This project measures how much additional rooftop photovoltaic capacity the IIT Delhi
campus could carry, and whether the campus electrical network could absorb it. The work
is divided into nine parts; four are complete and are reported here.

Ten candidate buildings with no existing photovoltaic installation were selected from a
campus-wide survey, chosen on a **matched-pair** principle so that each candidate sits
beside a near-identical building that already carries panels and can serve as a
validation reference. Every one of the ten roofs was then hand-traced in QGIS against
satellite imagery, together with all twenty-one objects standing on them. Applying a
1 m fire setback and a ground coverage ratio derived from the winter sun position
rather than assumed, the ten roofs yield **10,328 m² of module area and 2,220.6 kWp of
installable capacity** — roughly three times the existing campus fleet, which is
estimated at 765 kWp.

Three findings emerged that were not anticipated in the project specification.

**First, four existing plants have stopped generating**, for between 6 and 23 months,
representing 166.8 MWh of electricity never produced — roughly ₹13 lakh at a
provisional tariff, with about ₹1 lakh a month still being lost from 95 kWp standing
idle. A meter reading was recorded every day throughout; nobody had differenced one
day against the next. A fifth location, the SIT Building, has generated only 248 kWh in
its entire record.

**Second, the two standard irradiance sources disagree by 10.1 per cent**, against the
specification's 5 per cent tolerance, so acceptance criterion FR-1 fails as written. The
disagreement is almost entirely a winter effect and was resolved by arbitration against
792 MWh of measured campus generation, which selected NASA POWER over PVGIS. Had PVGIS
been used unexamined, every yield figure in this project would have been about 10 per
cent too high.

**Third, open building-footprint data overstates roof area by 29 per cent**, and does so
unevenly — from 0.3 per cent on one building to 67 per cent on another. No single
correction factor could have repaired it, which is the quantified argument for manual
digitising over scaling.

The remaining five parts — segmentation modelling, shading analysis, generation
modelling, feeder impact and synthesis — are planned in Section 12. Only the feeder
study is blocked, on three documents that cannot be derived, fetched or estimated.

# Contents

1. Data inventory and sources
2. Introduction
3. How the project is divided: the nine parts
4. Part 1 — Choosing the buildings
5. Part 2 — Characterising the existing fleet
6. Part 3 — Irradiance and base geospatial data
7. Part 4 — Digitising the roofs and deriving usable area
8. Key findings
9. Acceptance criteria: status at mid-term
10. Assumptions and decisions register
11. Deviations from the specification
12. Plan for Parts 5 to 9
13. Risks and blockers
14. Timeline
15. References

Appendix A — Per-building results\
Appendix B — The building register and its schema\
Appendix C — Reproducibility

# Abbreviations and symbols

| Term | Meaning |
|---|---|
| CEA | Central Electricity Authority (India) |
| CERC | Central Electricity Regulatory Commission |
| DERC | Delhi Electricity Regulatory Commission |
| DHI / DNI | Diffuse / Direct Normal Irradiance |
| DSM | Digital Surface Model |
| EPSG:32643 | Coordinate reference system, UTM zone 43 North — measures in metres |
| EPSG:4326 | Coordinate reference system, latitude/longitude — measures in degrees |
| ERA5 | ECMWF atmospheric reanalysis dataset, the basis of the PVGIS TMY used here |
| FR-1 … FR-5 | Functional Requirements 1 to 5 of the project specification |
| GCR | Ground Coverage Ratio — module area divided by the ground area it occupies |
| GHI | Global Horizontal Irradiance |
| IoU | Intersection over Union, a segmentation accuracy measure |
| kWp / MWp | Kilowatt-peak / Megawatt-peak — photovoltaic capacity at standard test conditions |
| kWh / MWh | Kilowatt-hour / Megawatt-hour — energy |
| MF | Meter Factor — multiplier converting a register difference to kWh |
| MNRE | Ministry of New and Renewable Energy |
| OSM | OpenStreetMap |
| PR | Performance Ratio |
| PSH | Peak Sun Hours |
| PV | Photovoltaic |
| PVGIS | Photovoltaic Geographical Information System, European Commission |
| TMY | Typical Meteorological Year |
| UMEP | Urban Multi-scale Environmental Predictor, a QGIS plugin |

<div class="pagebreak"></div>

# 1. Data inventory and sources

Every data file the project touches is listed here once, with an identifier, its origin
and its status. The identifiers `D01`–`D38` are used throughout the rest of this report
and in `docs/project_plan.md`.

**Status legend** — **HAVE** in hand · **GET** fetchable by us · **ASK** must come from
the Institute · **MAKE** produced by us · **DERIVE** obtained by computation rather than
request.

## 1.1 Given to us

Received from **Sachin sir**, who maintains the campus generation-meter records. These
two workbooks are the only data the project did not obtain for itself, and they underpin
the whole of Part 2 as well as the source arbitration in Part 3.

| ID | File | Status | What it is |
|---|---|---|---|
| D01 | `Solar reading jan-24 to dec-24.xlsm` | HAVE | Daily generation-meter readings, 12 monthly sheets, Jan–Dec 2024 |
| D02 | `Solar meter Report-2025 & 2026.xlsx` | HAVE | Same format, 16 monthly sheets, Jan 2025 – Apr 2026 |

These are **generation** meters, not consumption meters. They record what the existing
photovoltaic plants produced; they say nothing about what any building consumed, which
is why FR-5 remains blocked.

> **Data handling.** D01 and D02 are the Institute's records. They are held in the
> project repository so that the raw data survives a lost laptop, and they must not be
> redistributed without the supervisor's permission.

## 1.2 Fetched by us

Obtained from public sources by query or download. Each was recorded in
`docs/decisions.md` at the time it was fetched, with the exact query and the date.

| ID | File | Status | Source | What it is |
|---|---|---|---|---|
| D06 | `pvgis_tmy_28.545_77.192.json` | HAVE | PVGIS, European Commission | Typical Meteorological Year: 8,760 hourly rows of GHI, DNI, DHI, temperature, wind |
| D07 | `nasa_power_28.545_77.192_20140101_20231231.json` | HAVE | NASA POWER | 10 years of hourly irradiance, 2014–2023, 87,648 records |
| D08 | `footprints_osm.json` | HAVE | OpenStreetMap | 1,257 building polygons in the campus bounding box, 102 of them named |
| — | `horizon_28.545_77.192.json` | HAVE | PVGIS | Far-horizon elevation profile in every direction |
| D09 | `footprints_google_open_buildings.csv` | **descoped** | Google Open Buildings | Independent footprints and heights — no longer needed, see §11 |
| D10 | `campus_imagery/` | GET | Esri World Imagery | Sub-metre satellite tiles; acquisition date must be recorded for the FR-3 validation |
| D11 | `inria_aerial_dataset/` | GET | INRIA | Aerial image labelling dataset, training data for Part 5 |
| D36 | `mnre_benchmark_cost.pdf` | GET | MNRE / CERC | Benchmark capital cost for rooftop solar, ₹/Wp — Part 9 input |
| D37 | `cea_emission_factor.pdf` | GET | CEA | Grid emission factor, tCO₂/MWh — Part 9 input |
| D38 | `campus_electricity_tariff` | ASK / GET | DERC order / Institute | The rate the Institute pays per kWh. An indicative public figure is fetchable; only the contracted rate needs asking |

D36, D37 and D38 are deferred to Part 9 because nothing before the economics needs them.

## 1.3 Derived and produced by us

| ID | File | Status | What it is |
|---|---|---|---|
| D03 | `campus_solar_monthly.csv` | MAKE | 687 rows. Cleaned monthly kWh per plant, parsed from D01 + D02 |
| D04 | `building_register.csv` | MAKE | The audit trail. One row per building, one column per computed number |
| D05 | `register_schema.yml` | MAKE | Data dictionary for D04. A test fails if a column appears without an entry |
| D13 | `buildings_without_solar` | **DERIVE** | Originally on the request list. Derived instead: D03 names the roofs that already carry PV, and D08 plus imagery gives the rest |
| D28 | `QGIS Software.qgz` | MAKE | The QGIS project |
| D29 | `roofs.gpkg`, `obstructions.gpkg` | MAKE | **Hand-digitised roof outlines and obstructions — the project's primary measurement** |
| D30 | `dsm.tif` | MAKE | Digital surface model, footprints extruded by height — Part 6 |
| D31 | `shading_factors.csv` | MAKE | Hourly shading factor per roof, from UMEP — Part 6 |
| D32 | `generation_results.csv` | MAKE | Annual energy, specific yield, capacity factor per building — Part 7 |
| D33 | `feeder_model.dss` | MAKE | OpenDSS feeder model — Part 8 |
| D34 | `feeder_results.csv` | MAKE | Voltage rise, reverse power flow, losses, hosting capacity — Part 8 |
| D35 | `campus_heatmap.png` | MAKE | Campus map coloured by annual specific yield — Part 9 |

D03, D04, D05, D28 and D29 exist today. The rest are produced by Parts 6 to 9.

## 1.4 Requested but not yet received

| ID | File | Priority | Why it matters |
|---|---|---|---|
| **D12** | `existing_pv_plant_schedule.xlsx` | **1** | Per plant: installed kWp, module type and count, inverter, tilt, azimuth, commissioning date. Without installed kWp the FR-4 back-test has 28 months of generation and nothing to divide by |
| **D16** | `electricity_bills_2024_2025.xlsx` | **1 — blocker** | Monthly consumption per building. **Cannot be derived, fetched or estimated.** FR-5's criterion is calibration against billed consumption |
| **D17** | `campus_single_line_diagram.pdf` | **1 — blocker** | Network topology. Which buildings sit on which feeder is not visible from imagery nor inferable from generation data |
| **D18** | `transformer_schedule.xlsx` | **1 — blocker** | Transformer ratings and which buildings each supplies. **Cannot be derived** |
| D14 | `meter_factor_confirmation` | 2 | Written confirmation that register reading × MF = kWh, and that the MF row applies to the Jan–Jun 2024 sheets too |
| D15 | `hostel_meter_readings_2025` | 2 | The missing year — all 13 hostel meters are absent from every 2025 sheet |
| D19 | `feeder_layout.pdf` | 3 | 11 kV feeder routing |
| D20 | `plant_outage_log` | 3 | Why the stopped plants stopped |
| D21 | `meter_replacement_log.xlsx` | 4 | Explains register resets and the 29490555 → 42490555 relabelling |
| D22 | `net_metering_agreement.pdf` | 4 | Is generation exported or consumed behind the meter? Decides how D16 is interpreted |
| D23 | `cable_schedule.xlsx` | 4 | Cable sizes and lengths on the study feeder |
| D24 | `interval_meter_data.csv` | 5 — optional | Hourly or 15-minute consumption, if it exists |
| D25 | `campus_footprints.dwg` | 5 — optional | Campus CAD; would replace D08 if accurate |
| D26 | `roof_plans_photos/` | 5 — optional | Roof plans or photographs of tanks, stair rooms, existing arrays |
| D27 | `previous_solar_survey.pdf` | 5 — optional | Any earlier rooftop solar survey |

## 1.5 Summary

| Category | Count |
|---|---|
| Given to us | 2 |
| Fetched by us | 9 |
| Derived or produced by us | 12 |
| Requested, still outstanding | 15 |
| **Total tracked** | **38** |

Of the seventeen files originally on the request list, only three — **D16, D17 and
D18** — cannot be derived, fetched or estimated. All three are needed by Part 8 alone.
Every other part of the project can proceed without the Estate Office.

# 2. Introduction

## 2.1 The problem

The IIT Delhi campus already generates some of its own electricity from rooftop solar.
Thirty-one meters at twenty-nine locations record daily generation, and the Institute
has been collecting those readings since at least January 2024.

Many campus roofs, however, carry no panels at all. They are flat, unshaded, structurally
ordinary, and as far as anyone has established, nobody has measured what they could
generate. The question the Institute cannot presently answer is a simple one:

> *If we installed solar on the roofs that are still empty, how much electricity would we
> get, and could the campus network carry it?*

Answering that requires more than multiplying roof area by a rule of thumb. The usable
part of a roof is much smaller than the roof, because water tanks, stair rooms, lift
machine rooms and air-conditioning plant stand on it; because fire access requires a
clear strip around every edge; and because tilted panel rows must be spaced so that one
row does not shade the next. Each of those subtractions has to be measured rather than
assumed, and the project specification explicitly forbids assuming a fixed usable
percentage.

## 2.2 What this project is trying to solve

Four objectives, restated from the specification in plain terms:

1. **Find the roofs that are still unused.** Establish which campus buildings have no
   photovoltaic installation and are suitable for one.
2. **Measure what is genuinely usable.** Not the building footprint — the module area
   that survives obstructions, setbacks and inter-row spacing.
3. **Estimate the electricity.** Model annual generation per building from measured
   irradiance, modelled shading and an explicit loss stack, then validate that model
   against the campus's own metered output.
4. **Check the grid can absorb it.** Model one campus feeder and find the voltage rise,
   reverse power flow and hosting capacity that the new generation would imply.

## 2.3 How we are trying to solve it

The approach rests on three commitments that shape everything in this report.

**Every number is traceable.** A single file, `data/building_register.csv`, holds one row
per building and one column per computed number. Every column is described in
`register_schema.yml` with the module that produced it and the formula behind it, and an
automated test fails if a column appears without an entry. The register is stored as CSV
rather than a spreadsheet binary so that a changed number shows up as a readable diff.

**Every acceptance criterion is executable.** The specification's five functional
requirements are implemented as callable checks in `src/btp_solar/acceptance.py`. A part
is signed off by running a check, not by asserting in prose that it passed. This is why
Section 9 can report that FR-1 *fails* — the check said so, and the failure was then
diagnosed rather than hidden.

**Every assumption is dated and written down.** `docs/decisions.md` records each choice a
number depends on, with the date and the reasoning, including what was rejected. Where
this report says "we assumed", that file is what it is quoting.

**Site.** All work is referenced to 28.545° N, 77.192° E, at an elevation of 229 m above
sea level. All area and length measurement is performed in EPSG:32643 (UTM zone 43 North),
which measures in metres; measuring in degrees is the single most common way to get a
rooftop area wrong by a factor of ten thousand.

# 3. How the project is divided: the nine parts

The work is broken into nine parts, grouped into four stages. Each part names the data it
consumes and the data it produces, so that at any moment it is clear what is blocked and
on what. **Four parts are complete and are reported in Sections 4 to 7.**

![The nine work parts. Four are complete; one is blocked on data that cannot be derived.](reports/figures/nine_parts.png)

| Stage | Part | Name | Produces | Acceptance | Status |
|---|---|---|---|---|---|
| A | 1 | Choose the buildings | Candidate list, register identity columns | — | **Complete** |
| A | 2 | Read the meter data | D03 monthly generation per plant | — | **Complete** |
| A | 3 | Collect sunshine data | D06, D07, D08 | FR-1 | **Complete (FR-1 fails, §9)** |
| B | 4 | Measure the roofs | D29, register usable-area columns | FR-2 | **Complete (FR-2 passes)** |
| B | 5 | Machine learning | Segmentation accuracy report | FR-2 (IoU ≥ 0.75) | To do |
| C | 6 | Shadows | D30, D31 | FR-3 | To do |
| C | 7 | Calculate electricity | D32, D35 | FR-4 | To do |
| D | 8 | Grid impact | D33, D34 | FR-5 | **Blocked** |
| D | 9 | Report and costs | Final report | — | To do |

Showing all nine at once makes two things explicit. The machine-learning component is
**one part of nine**, not the centrepiece of the project — it exists to scale the method
past ten buildings, not as an end in itself. And only Part 8 is blocked; every other
remaining part can proceed on data already in hand.

# 4. Part 1 — Choosing the buildings

## 4.1 What this part was for

Before anything can be measured, the set of buildings to measure has to be fixed and
defended. The specification anticipated eight to ten candidate buildings with no existing
photovoltaic installation, plus two existing installations retained for validation.

## 4.2 Method

The candidate pool was **derived rather than requested**, which removed
`buildings_without_solar.xlsx` (D13) from the data request entirely.

1. **Download every campus building outline.** An OpenStreetMap query over the campus
   bounding box returned **1,257 building polygons**, of which **102 carry a name**.
2. **Remove the roofs that are already taken.** The 29 locations that appear in the
   generation-meter data (Part 2) were cross-referenced against those names. This is the
   step that makes the candidate list defensible: the occupied roofs were identified from
   the Institute's own meter records, not by walking around hoping to spot panels.
3. **Assess the remainder.** Thirty buildings were shortlisted and each was checked —
   some by visiting the building, others by inspecting high-resolution satellite imagery
   — against four questions:
   - Is the roof flat?
   - Are there panels on it already?
   - How many floors does it have?
   - Are there obstacles to a solar installation?

## 4.3 What the assessment removed

| Outcome | Count | Buildings |
|---|---|---|
| Ruled out — roof not flat | 3 | `4 LT 3`, `6 LT 1`, `2A/05` |
| Ruled out — panels already present | 6 | Blocks 1, 2 (two polygons), 5, 6, Focus Incubation Centre |
| **Viable candidates remaining** | **21** | — |
| **Selected** | **10** | See §4.4 |

Five buildings are held as a ranked reserve, in order: Academic Complex West, Admin
Building, Mathematics Department, RnI Park, Dogra Hall.

## 4.4 The ten candidates, and why each was chosen

The ten were **not** chosen for roof size. They were chosen on a **matched-pair**
principle: seven of them sit in groups where a near-identical building already carries
photovoltaic panels and is in the validation set.

| ID | Building | Type | Storeys | Why this one |
|---|---|---|---|---|
| B01 | **Block 3** | academic | 4 | Blocks 1, 2, 5 and 6 have PV; 3 and 4 do not. Same design, same era, same orientation |
| B02 | **Block 4** | academic | 4 | Same matched pair |
| B03 | **Dronagiri House** | hostel | 7 | One of only three hostels without PV, against thirteen that have it |
| B04 | **Saptagiri House** | hostel | 7 | Same |
| B05 | **Vindhyachal Hostel** | hostel | 4 | Same |
| B06 | Lecture Hall Complex | academic | 5 | Large roof; daytime load profile matches generation |
| B07 | Academic Complex East | academic | 6 | Tallest candidate, large roof |
| B08 | Dept of Textile Technology | laboratory | 4 | Laboratory block, per the specification's scope |
| B09 | Dept of Material Science | laboratory | 4 | Laboratory block, per the specification's scope |
| B10 | Central Workshop | service | 2 | The low-rise service building the scope requires |

**Why matched pairs matter.** The specification's back-test is a generic plausibility
check: does the model predict a sensible specific yield? Matched pairs turn it into a
**like-for-like prediction** — the model can be asked to predict Block 3 from Block 1,
two buildings of identical design and era, one instrumented and one not. That is a
materially stronger claim than the specification anticipated.

## 4.5 The validation set, widened from two to six

The meter data revealed 29 locations already carrying photovoltaic panels, about 20 of
them generating — an order of magnitude more than the two the specification reserved. Six
are now carried as the primary validation set, chosen for record length and for pairing
with the candidates:

| ID | Building |
|---|---|
| V01 | Bharti Block |
| V02 | Block No. 1 (KSBS) |
| V03 | Block No. 5 (Near V-112) |
| V04 | Block No. 6 (Near VI-136) |
| V05 | Karakoram Boys Hostel |
| V06 | Shivalik Boys Hostel |

The remaining live plants stay available as a secondary validation set.
`tests/test_register.py` was updated accordingly.

## 4.6 Outputs and open items

**Produced:** `data/candidate_shortlist.csv`; the identity columns of the building
register (`building_id`, `building_name`, `category`, `role`, `has_existing_pv`,
`osm_id`, `lat`, `lon`, `storeys`).

**Carried forward.** Building heights are recorded as **storey count × 3.5 m** and flagged
`provisional` in `height_source`. A wrong floor height propagates directly into the FR-3
shading model, so the true floor height should be confirmed before Part 6.

`Student Activity Centre` and `Students Activity Center` are two OpenStreetMap polygons
120 m apart. Neither was selected, but if either is promoted from the reserve list, it
must first be established whether they are one building or two.

# 5. Part 2 — Characterising the existing fleet

## 5.1 What this part was for

Two workbooks of daily generation-meter readings, D01 and D02, had to be turned into
trustworthy monthly energy per plant. This part does that, and in doing so produces the
list of occupied roofs that made Part 1 possible.

## 5.2 What was parsed

| Quantity | Value |
|---|---|
| Daily readings parsed | **17,006** |
| Readings dropped as transcription errors | **97** |
| Meters | **31** |
| Locations | **29** |
| Monthly sheets | 28 |
| Period covered | January 2024 – April 2026 |

Output: `data/campus_solar_monthly.csv`, 687 rows of cleaned monthly kWh per plant.
Reproduce with `scripts/run_campus_meters.py`.

## 5.3 Four format problems, each of which changes the numbers

These workbooks could not be read naively. Four handling decisions were required, and
each one alters the result.

**Meter factor.** Every column carries a meter factor between 1 and 80; energy is the
register *difference* multiplied by that factor. The January–June 2024 sheets omit the
meter-factor row entirely, but the registers run continuously into the July sheets, so
the later factors were applied throughout. Written confirmation of this is request D14.

**Column order changes between sheets.** Sheets were therefore joined on meter number,
never on column position.

**Transcription errors.** 97 readings were dropped: decimal slips (1113411.2 recorded for
113341.7), blanks entered as zero, and one month whose dates were stored as text. This is
not a cosmetic repair — **naive differencing of the raw register inflates annual
generation by roughly a factor of ten.**

**Two meter numbers, one plant.** Meters 29490555 and 42490555 are the same installation
relabelled, not two separate plants. The last reading under the first number (31 July
2025, 155597.2) and the first under the second (1 August 2025, 155631.2) differ by one
ordinary day's generation. A genuinely replaced meter would restart near zero. The two
are folded together in `METER_ALIASES`.

## 5.4 The finding: plants that stopped generating

Differencing the registers showed that **six meters at five locations had stopped
generating**. Four of those locations carry a quantifiable loss:

| Plant | est. kWp | Last generated | Months idle | Lost MWh |
|---|---|---|---|---|
| Main / Amaltas Guest House | 34 | May 2024 | 23 | 97.9 |
| Central Library | 38 | June 2025 | 10 | 47.4 |
| Main Building | 14 | August 2025 | 8 | 14.7 |
| Vishwakarma (2 meters) | 9 | October 2025 | 6 | 6.8 |
| | | | | **166.8** |

At a provisional ₹8/kWh that is roughly **₹13.3 lakh of electricity never generated**,
with about **₹0.97 lakh a month** still being lost from **95 kWp standing idle**.

**The fifth location is the SIT Building.** It last generated in April 2024, but it has
produced only **248 kWh in its entire record**. That is too little to back-calculate a
capacity from, so no rupee figure can honestly be attached to it — but a plant that has
generated 248 kWh in total is itself a finding worth reporting.

**Why it went unnoticed.** A reading was written down every day throughout. The register
simply never moved. The data was collected faithfully, filed, and never differenced. The
evidence was in the workbooks from the day they were handed over.

**Guard against false positives.** `lost_kwh` reports nothing until a plant has been idle
longer than `config.OUTAGE_MONTHS` (six months), so a monsoon lull or a spell of missing
readings is not announced as a failure. `test_a_short_gap_is_not_an_outage` pins this
behaviour. Reproduce with `scripts/run_outage_report.py`.

> **Honesty about these numbers.** The **outages are fact** — a register that does not
> move has not generated, and there is no modelling assumption in that claim. The
> **rupee figures are estimates**, resting on a back-calculated plant capacity and on a
> provisional ₹8/kWh tariff that stands until D38 arrives. They are reported as
> indicative. The outage count and durations need no such caveat.

## 5.5 Fleet capacity, and the circularity trap

Installed capacity in kWp is **not** present anywhere in D01 or D02. All 28 sheets, every
cell, the raw XML, cell comments and hidden sheets were searched; the only non-reading
content is the meter-factor row, a plant index row, and monthly total rows. The supervisor
agreed the project may proceed on estimates.

Capacity is therefore back-calculated per plant from monthly energy:

```
kWp = monthly kWh / (days × peak sun hours × performance ratio)
```

taken as the median across all live months. The fleet total is approximately **765 kWp**,
with an interquartile range of 575 to 938 kWp. Per-plant quartile spreads are tight,
which indicates the method is stable across seasons.

**The circularity trap.** Capacity derived this way must never be used for the FR-4
back-test. Specific yield would become `kWh / (kWh / (PSH × days × PR))`, which collapses
to the assumed constant for every plant. The acceptance test would pass by construction
and prove nothing. The back-test is therefore restructured into two checks that are
genuinely independent of the generation data — shape validation, and capacity measured
from module rows visible in imagery. This is set out in §12.3.

**Capacity for the candidate roofs is unaffected by any of this.** It comes from roof
area, ground coverage ratio and module power density in Part 4, and never touches the
meter data.

## 5.6 Data gaps found

**The whole of 2025 is missing the hostel meters.** Sheets Jan-25 through Dec-25 carry
only 17 of the 31 columns — **all 13 hostel meters are absent**. The 2025 total of
540 MWh is therefore *not* comparable with 2024's 955 MWh, and the difference must not be
read as a decline. Recovering the missing year is request D15.

# 6. Part 3 — Irradiance and base geospatial data

## 6.1 What this part was for

Before you can work out how much electricity a roof could make, you need two things: how
much sunshine falls on Delhi, and where the buildings are. Part 3 collects both.

## 6.2 The three sources

### OpenStreetMap — where the buildings are

A free world map anyone can edit, like Google Maps but downloadable. The query asked for
every building inside a bounding box around IIT Delhi, and returned **1,257 building
shapes, 102 of them named**. Those 102 names, matched against the 29 locations already
carrying photovoltaic panels, are what made Part 1 possible.

File: `footprints_osm.json`, 202 KB. Tracked in the repository because OpenStreetMap is a
living map — a later re-download would not reproduce the same footprints.

### PVGIS — the standard irradiance source

Run by the European Commission's Joint Research Centre, and the tool almost every solar
project in the world uses. Two products were downloaded.

**(a) The Typical Meteorological Year.** One full year of weather, hour by hour — 8,760
rows, each carrying sunshine, temperature, humidity and wind. It is not a real year: it is
assembled from the most typical months selected out of 2005–2023, so it represents "a
normal year in Delhi".

Result: **1,930.0 kWh/m²/yr**. File `pvgis_tmy_28.545_77.192.json`, 1.4 MB.

**(b) The horizon profile.** This was downloaded incidentally while chasing the TMY, and
turned out to be worth keeping for two independent reasons.

*The far horizon is flat* — between **0.0° and 1.9°** in every direction. No distant
terrain shades the campus, so every shadow falling on these roofs comes from something
local: the building next door, a parapet wall, a tree. That simplifies Part 6
considerably.

*It independently confirms the solar geometry.* PVGIS computes its own solar positions,
and its winter-solstice series agrees with our closed-form derivation to within rounding:

| | ours | PVGIS |
|---|---|---|
| Elevation at solar noon, 21 December | 38.01° | 38.00° |
| Elevation at the 09:00 design point | 22.32° | 22.30° |
| Azimuth at the 09:00 design point | 44.53° E of S | 44.50° E of S |

This matters more than it first appears. Those angles set the ground coverage ratio; the
ground coverage ratio sets every usable-area and installable-capacity figure in the
project. The agreement is now pinned by `test_matches_pvgis_winter_solstice`.

The horizon file also corrected the **site elevation** from an assumed 216 m to PVGIS's
digital-elevation value of **229 m**.

### NASA POWER — the independent second opinion

NASA's meteorological database, built from **satellite observations of the actual sky**.
This is the key methodological difference from PVGIS: the PVGIS TMY used here is derived
from **ERA5 reanalysis**, a physical model of the atmosphere, whereas NASA POWER is
observational.

Ten years of hourly data were requested, 2014–2023 — **87,648 records**.

Result: **1,744.7 kWh/m²/yr**. File 6.4 MB.

> **A note on availability.** PVGIS was initially unreachable: `re.jrc.ec.europa.eu`
> resolved and completed the TLS handshake, then closed without responding — on the
> v5_2 endpoint, the v5_3 endpoint and the plain web page alike. The whole host was
> unreachable from the working machine, not merely the API. Both PVGIS products had to be
> downloaded through a browser by hand. Until the TMY arrived, FR-1 could not be
> evaluated at all, because its criterion requires two independent sources and only one
> was in hand.

## 6.3 The problem: the two sources disagree

FR-1 requires the two irradiance sources to agree on annual GHI within 5 per cent.

| Source | Period | Annual GHI |
|---|---|---|
| PVGIS TMY (ERA5) | 2005–2023 | **1,930.0** kWh/m²/yr |
| NASA POWER | 2014–2023 | **1,744.7** kWh/m²/yr |
| | | **Gap: 10.1%** |

At more than double the allowed tolerance, **FR-1 does not pass as written**.

**It was checked first that this was not our own error.** Units were verified — NASA POWER
returns Wh/m² per hour, with no fill values in this record — and the PVGIS TMY was
confirmed to have a full 8,760 rows. The gap is not an arithmetic mistake. The
disagreement is real.

### Where the disagreement lives

Mean daily GHI, kWh/m²/day:

| | January | April | July | October |
|---|---|---|---|---|
| NASA POWER | 2.84 | 6.55 | 4.82 | 4.62 |
| PVGIS | 4.19 | 7.14 | 4.69 | 5.40 |
| | **PVGIS +47%** | close | they agree | |

**They agree through the monsoon and diverge sharply in winter**, where PVGIS claims up
to 47 per cent more January sun. That is the signature of **winter fog and aerosol over
the Indo-Gangetic Plain**, which ERA5 reanalysis is known to represent poorly. NASA's
satellites observe the haze blocking the sun; a reanalysis model of the atmosphere does
not reproduce how severe Delhi's winter actually is.

## 6.4 How it was settled — using the campus's own meters

Rather than choosing by assertion, the campus's own generation was used to arbitrate.

**The method: compare shapes, not sizes.** Eighteen plants with a complete live 2024 —
totalling **792 MWh of real, measured electricity** — were taken, and the question asked
was: what share of the year's output arrived in January? In February? And so on. The same
question was then asked of each irradiance source.

Monthly generation and monthly irradiance were each **normalised to their own annual
total**. Because plant capacity is unknown, this matters: normalising makes plant size
cancel out completely, so the test is **not circular**.

```
total absolute shape error    NASA 0.072      PVGIS 0.109

How much smaller is January than April?
  Real campus meters : 0.429
  NASA POWER         : 0.433    almost exactly right
  PVGIS              : 0.587    37% too high
```

NASA POWER reproduces the measured seasonal shape closely. On the January-to-April ratio
it is almost exact, while PVGIS is 37 per cent too high.

**The tilt effect strengthens this rather than weakening it.** Measured output is
plane-of-array on modules tilted at about 15°, which *raises* the winter share relative to
GHI; summer temperature derating raises it further. The true GHI winter share implied by
the measurements is therefore *lower* still, so PVGIS's winter excess is larger than the
table shows. The conclusion is conservative, not marginal.

## 6.5 Decision

**NASA POWER becomes the primary irradiance source for FR-4.** PVGIS is retained as the
secondary source, and its divergence is carried forward as a declared uncertainty band.

Had PVGIS been used without checking — as most rooftop studies do — **annual yield across
the campus would have been overstated by roughly 10 per cent.**

Reproduce with `scripts/run_fr1_source_selection.py`.

## 6.6 What we decided not to fetch

**Google Open Buildings (D09) was descoped.** Its value under FR-1 was an independent
footprint and an independent height. For ten buildings being digitised by hand in Part 4,
the footprint adds nothing; and a better independent height is available from the storey
counts already collected plus shadow length measured in imagery during Part 6. Dropping it
avoids a large download for no analytical gain.

**MNRE capital cost (D36) and the CEA emission factor (D37)** are Part 9 inputs and are
deferred until the economics are written.

## 6.7 How each file is used next

| File | Used in | For what |
|---|---|---|
| `footprints_osm.json` | Part 4 | Loads into QGIS as the starting outlines, traced over and corrected |
| `horizon_...json` | Part 6 | Establishes that distant terrain can be ignored; only local shadows need modelling |
| `nasa_power_...json` | Part 7 | The primary input to the generation model — every hour of sun feeds the calculation |
| `pvgis_tmy_...json` | Part 7 | Hourly temperature, since modules lose efficiency when hot; and the cross-check |

# 7. Part 4 — Digitising the roofs and deriving usable area

## 7.1 What this part was for

Before you can say how much electricity a roof will make, you have to know how much of
that roof you can actually put panels on. That is not the size of the building. You have
to take away:

- the things already standing on the roof — water tanks, stair rooms, lift machine rooms,
  air-conditioning plant;
- a clear strip round the edge, for fire access and maintenance;
- the gaps between rows of panels, so that one row does not shade the next.

Part 4 measures all of that, for each of the ten candidate buildings.

## 7.2 Why it was done by hand

The starting point was OpenStreetMap, which gave an outline for each of the ten buildings
in seconds. Those outlines turned out to be **wrong by 29 per cent on average**. They are
*building* outlines drawn by volunteers, not *roof* outlines, and they frequently wrap
open ground, courtyards and adjoining structures.

Every roof was therefore re-traced by hand against satellite imagery. This is the slow
part of the project, and it is the part the specification says decides everything after
it.

## 7.3 The tools

| Tool | What it did |
|---|---|
| **QGIS** | Free open-source mapping software. Used to display the satellite imagery and draw on it |
| **Esri World Imagery** | Satellite photographs of the campus, streamed into QGIS as a background layer |
| **EPSG:32643** | The coordinate system — UTM zone 43 North, which **measures in metres**. Critical: in the default latitude/longitude system QGIS measures in degrees, and every roof area comes out about ten thousand times wrong |

![The QGIS working environment: the ten traced roof outlines (red) and the obstructions layer (orange fill) over Esri World Imagery, in EPSG:32643.](reports/figures/qgis_workspace.jpeg)

## 7.4 Step by step

| Step | What was done |
|---|---|
| 1 | Load the ten OpenStreetMap outlines into QGIS over Esri satellite imagery |
| 2 | Set the coordinate system to EPSG:32643, so that measurements are in metres |
| 3 | Drag each corner of the outline onto the real edge of the roof in the imagery; punch courtyards out as holes |
| 4 | Draw a polygon around every object standing on every roof — 21 in total |
| 5 | Run the seven automated validity checks |
| 6 | Run the area chain and write every intermediate value to the register |

### Rules followed while tracing

- Trace the **roof**, not the building. They differ wherever there is an overhang or a
  porch.
- If a wing has a **lower roof at a different height**, trace only the main flat area. A
  different level is a different surface.
- **Courtyards and light wells are not roof.** Where a roof wraps around an open area,
  that area is punched out as a hole using QGIS's *Add Ring* tool. B01 and B06 both
  required this.

### What was deliberately not drawn as an obstruction

Twenty-one obstruction polygons were drawn: 10 typed `other`, 4 `stair_room`,
4 `water_tank`, 2 `solar_panel`, 1 `open_air`. Three categories were deliberately
excluded:

- **Tree overhang.** A tree blocks light; it does not occupy roof area. Subtracting it
  here *and* modelling it in the shading analysis would penalise the same square metres
  twice. Overhangs belong to Part 6.
- **Courtyards and gaps between blocks.** Not roof at all, so they are holes in the roof
  polygon instead. Both treatments subtract the area, but only the hole also adds the
  gap's edge to the perimeter, so that the fire setback is correctly applied around it.
- **Shadows.** Shadows move. The object casting the shadow is what gets drawn.

> **Rule of thumb.** Something standing *on* the roof is an obstruction. Something that is
> *not roof at all* is a hole. Something that blocks *light* rather than occupying area is
> shading, and belongs to FR-3.

## 7.5 The seven validity checks

`scripts/check_roofs.py` runs seven checks. **Each one exists because that exact mistake
occurred during this work and was invisible on screen.**

| Check | The mistake it catches |
|---|---|
| Every building present | A roof deleted and never redrawn |
| No duplicate buildings | Redrawing adds a feature, it does not replace one |
| All vertices on campus | A polygon fetched from entirely the wrong place |
| No self-intersections | An outline folded over itself, making its area meaningless |
| No duplicate vertices | A stray double-click leaving two nodes in one spot |
| Obstructions on the right roof | An obstruction named after the neighbouring block |
| Every obstruction has a type | A blank type field |

Two of these are worth expanding, because they caught errors that would otherwise have
reached the final figure.

**The wrong building entirely.** B06 Lecture Hall Complex is an OpenStreetMap *relation*,
but the geometry query asked for `way(id:19120455)`. Way ids and relation ids are separate
number spaces, so the query returned a different building carrying the same number — one
in Ohio, at 40.08° N, 82.46° W. It came back with a plausible 7,158 m² and was carried
straight into the preliminary campus total. Nothing about the number looked wrong. It was
caught only when converting to UTM, where B06 landed at a coordinate that is not on
Earth's land surface. `test_every_polygon_is_on_the_campus` now checks every vertex of
every candidate against a campus bounding box on every run.

**Obstructions assigned to the wrong building.** All six polygons drawn on the two
parallel blocks named the neighbouring block, because the labels sit near the gap between
them. This was caught by testing each polygon's centroid against each roof outline, not by
eye, and corrected in bulk.

## 7.6 The calculation

```
gross roof area                    what you traced
  − obstruction area               the tanks and stair rooms
  − setback strip                  1 m clear round every edge, including courtyards
  = net available area
  × 0.707   ground coverage ratio  leaves room between panel rows
  × 0.85    packing factor         walkways and inverter space
  = module area
  × 215 W/m²                       panel power per square metre
  = installable capacity in kWp
```

### Where 0.707 comes from

This is the one number the specification insisted must be **derived, not assumed**.

Panels are tilted, so each row casts a shadow behind it. Space the rows too close and the
back row sits in shadow all winter. The design rule adopted here is that **no row shades
the next between 09:00 and 15:00 solar time on 21 December**, the shortest day — the
conventional six-hour design window, and the stricter of the two common criteria.

At IIT Delhi the sun at that design point sits **22.32° above the horizon, 44.53° east of
south**. From the geometry of a tilted row:

```
pitch / L = cos β + sin β · cos γ / tan α
GCR       = L / pitch  =  0.707 at 15° tilt
```

where `L` is the module slope length, `β` the tilt, `α` the solar elevation and `γ` the
solar azimuth relative to the row normal.

Those sun angles were checked against PVGIS, which computes them independently, and agree
to within rounding (§6.2). **The number on which every capacity figure in this project
depends is confirmed by an outside source.**

The alternative, laxer criterion — no shading at solar noon only — gives a ground coverage
ratio of 0.771, about 8 per cent more module area, at the cost of a materially higher
winter-morning loss. The stricter criterion was chosen and recorded in `docs/decisions.md`.

## 7.7 Results

![From traced roof to installed panels: every subtraction in the area chain, in m².](reports/figures/bold/area_chain.png)

| id | building | gross m² | obstructions | setback | net | module | **kWp** | usable % |
|---|---|---|---|---|---|---|---|---|
| B01 | Block 3 | 3,132 | 275 | 622 | 2,235 | 1,342 | **288.6** | 42.9% |
| B02 | Block 4 | 2,729 | 204 | 454 | 2,071 | 1,244 | **267.5** | 45.6% |
| B03 | Dronagiri House | 2,214 | 848 | 236 | 1,130 | 678 | **145.9** | 30.6% |
| B04 | Saptagiri House | 2,161 | 823 | 228 | 1,110 | 666 | **143.3** | 30.9% |
| B05 | Vindhyachal Hostel | 3,653 | 975 | 556 | 2,122 | 1,274 | **274.0** | 34.9% |
| B06 | Lecture Hall Complex | 6,379 | 2,058 | 557 | 3,764 | 2,261 | **486.0** | 35.4% |
| B07 | Academic Complex East | 2,393 | 0 | 379 | 2,014 | 1,209 | **260.0** | 50.5% |
| B08 | Textile Technology | 4,003 | 2,531 | 563 | 910 | 546 | **117.5** | 13.7% |
| B09 | Material Science | 598 | 0 | 115 | 483 | 290 | **62.3** | 48.5% |
| B10 | Central Workshop | 2,399 | 743 | 296 | 1,360 | 816 | **175.6** | 34.0% |
| | **TOTAL** | **29,661** | **8,457** | **4,006** | **17,198** | **10,328** | **2,220.6** | |

![Installable capacity per candidate roof, kWp.](reports/figures/bold/capacity.png)

**29,661 m² traced → 17,198 m² net available → 10,328 m² of panels → 2,220.6 kWp.**

**Ten untapped roofs could carry about 2.2 MWp — roughly three times the existing campus
fleet**, which is estimated at 765 kWp.

## 7.8 Two findings worth reporting

### Open footprint data is wrong, and wrong unevenly

| | OSM m² | traced m² | change |
|---|---|---|---|
| B05 Vindhyachal Hostel | 3,663 | 3,653 | **−0.3%** |
| B08 Textile Technology | 4,126 | 4,003 | −3% |
| B09 Material Science | 646 | 598 | −8% |
| B02 Block 4 | 3,287 | 2,729 | −17% |
| B04 Saptagiri House | 2,698 | 2,161 | −20% |
| B06 Lecture Hall Complex | 7,965 | 6,379 | −20% |
| B01 Block 3 | 4,501 | 3,132 | −30% |
| B07 Academic Complex East | 3,643 | 2,393 | −34% |
| B03 Dronagiri House | 3,854 | 2,214 | −43% |
| B10 Central Workshop | 7,257 | 2,399 | **−67%** |
| **all ten** | **41,639** | **29,661** | **−29%** |

Many rooftop potential studies stop at open building footprints. This measures what
stopping there costs: **29 per cent overall**. More importantly, the error runs from
0.3 per cent to 67 per cent, so **no single correction factor could fix it.** That is the
quantified argument for digitising by hand rather than scaling.

### The "40 to 50 per cent of roof" rule of thumb does not hold

The workflow note suggests retaining 40–50 per cent of a roof for panels. The measured
figures run from **13.7 per cent on B08 to 50.5 per cent on B07**.

The rule works on clean roofs. It fails badly on cluttered ones — B08 Textile Technology
has 63 per cent of its roof covered in plant. This is a second, independent reason not to
use a blanket factor.

## 7.9 Does FR-2 pass?

The specification's criterion is that usable area must be *"derived from a documented
setback and ground coverage ratio rather than an assumed percentage."*

**Yes.** The setback is 1 m and is stated. The ground coverage ratio is 0.707, computed
from the winter sun position and confirmed against PVGIS. Nothing in the chain is an
assumed percentage.

The other half of FR-2 — a segmentation model reaching IoU ≥ 0.75 against this
hand-traced ground truth — is Part 5, and has not been started.

## 7.10 Open items carried forward

**B10 Central Workshop fell 67 per cent from its OpenStreetMap outline**, the largest
correction of the ten. Either the OSM polygon wrapped a workshop yard rather than a roof,
or the trace captured only part of the roof. It is worth about 500 kWp, so it should be
confirmed before the figure is published. **This is the weakest link in the 2.2 MWp
total.**

**B06 carries two obstructions typed `solar_panel`.** B06 was selected as a candidate
precisely *because* it has no photovoltaic installation, and the Lecture Hall Complex is
not among the 29 metered locations. Either panels have been installed recently, or there
is an **unmetered array on campus** — which would mean the existing fleet is larger than
the meter records show. Both possibilities are worth raising with the Estate Office.

**One obstruction on B06 (fid 19) subtracts 1,294 m² while only 6 per cent of it lies on
that roof.** Confirmed as intended on inspection and left as drawn, but it costs B06 about
130 kWp and should be the first thing re-checked if that roof's yield later looks wrong.

**One obstruction is typed `open_air`.** Open sky is properly a hole in the roof polygon
rather than an obstruction. As drawn the area is still subtracted correctly; only the
setback around its edge is missed.

**B06 carries no courtyard ring.** The previous OSM outline had a 408 m² hole, and a
containment test against the new outline was inconclusive — 18 of 37 courtyard vertices
fell inside. It was inspected on screen and judged not to need one. If B06's yield later
looks high against its neighbours, this is the first thing to re-check.

# 8. Key findings

Three results from the completed work stand on their own, independent of the capacity
headline.

## 8.1 Four plants have stopped generating, and nobody had noticed

This is the opposite of the question the project was set. The specification frames the
work as *finding untapped roofs*; this finding asks *whether what is already installed
still works* — and the answer, in four places, for up to 23 months, is no.

It is also the most defensible claim in the project. A register that does not move has not
generated. There is no modelling assumption in it. And it is answerable entirely from data
the Institute already held, before any new panel is costed.

**It has a consequence today.** Unlike everything else in this project, which concerns
what might be built, roughly ₹1 lakh a month is being lost right now from 95 kWp standing
idle.

![Months idle per stopped plant.](reports/figures/bold/outages.png)

## 8.2 A failed acceptance criterion, diagnosed and resolved

FR-1 fails as written: the two irradiance sources disagree by 10.1 per cent against a
5 per cent tolerance. That failure is reported here rather than hidden, because what
followed is the strongest methodological work in the project.

The disagreement is not noise. It is almost entirely a winter effect, traceable to a known
weakness of ERA5 reanalysis over the Indo-Gangetic Plain. It was resolved not by assertion
but by arbitration against 792 MWh of the campus's own measured generation, using a
normalised shape comparison in which plant capacity cancels — so the test is not circular.

**Recommendation to the supervisor.** FR-1's criterion assumed the two sources would
agree. They do not, for a physical reason that can be evidenced. The criterion should be
restated as: *"where the sources disagree, the choice is justified against measured
generation"* — which has now been done.

![Share of annual sunshine by month: the two sources against measured campus generation.](reports/figures/bold/sunshine.png)

## 8.3 Open footprint data costs 29 per cent, unevenly

The 29 per cent gap between OpenStreetMap outlines and hand-traced roofs is a
methodological result, not just a correction applied in passing. Because the error ranges
from 0.3 per cent to 67 per cent across ten buildings of the same campus, it cannot be
repaired by any blanket scaling factor — which is precisely what many published rooftop
potential studies do.

![OpenStreetMap outlines against hand-traced roofs.](reports/figures/osm_vs_traced.png)

# 9. Acceptance criteria: status at mid-term

Each criterion below is implemented as a callable check in `src/btp_solar/acceptance.py`.
A part is signed off by running the check, not by asserting that it passed.

| Ref | Criterion | Module | Status |
|---|---|---|---|
| **FR-1** | PVGIS and NASA POWER agree on annual GHI within 5% | `fr1_data.py` | **FAILS — 10.1% gap.** Diagnosed as an ERA5 winter-aerosol artefact and resolved by arbitration against measured generation. Restatement of the criterion recommended (§8.2) |
| **FR-2a** | Usable area derived from a documented setback and ground coverage ratio, not an assumed percentage | `fr2_usable_area.py`, `solar_geometry.py` | **PASSES.** 1 m setback stated; GCR 0.707 derived from the winter sun and confirmed against PVGIS |
| **FR-2b** | Segmentation IoU ≥ 0.75 against manual ground truth | — | **Not started.** Part 5 |
| **FR-3** | Modelled shadow within 15% of one measured in dated imagery | `fr3_shading.py` | **Not started.** Part 6. Requires D10 with a recorded acquisition date |
| **FR-4** | Specific yield 1300–1600 kWh/kWp/yr, within 10% of PVGIS, back-tested against metered output | `fr4_generation.py` | **Not started.** Part 7. Back-test restructured to avoid circularity (§5.5, §12.3) |
| **FR-5** | Base-case loading within 15% of billed consumption | `fr5_feeder.py` | **Blocked.** Cannot be evaluated without D16 |

**Two criteria can be assessed at mid-term. One passes, one fails for a reason we can
evidence and have resolved.** Of the four outstanding, three are simply not yet reached;
only FR-5 is blocked on data.

# 10. Assumptions and decisions register

Every choice that a number depends on is recorded in `docs/decisions.md` with its date and
reasoning. The table below is the current state of the values that are not yet fully
defended — reproduced here because the report's numbers rest on them.

| Value | Setting | Basis | Status |
|---|---|---|---|
| Module tilt | 15° | Common flat-roof ballasted racking in north India; below the latitude-optimum 28° to cut wind load and row spacing | **Confirm against a real campus installation** |
| Fire setback | 1.0 m | Workflow note | **Check the applicable fire code; 1 m may be too little** |
| Packing factor | 0.85 | Allowance for walkways, inverter pads, cable trays | **Assumed, not sourced** |
| Module power density | 215 W/m² | ≈22% efficient module on glass area | Reasonable for 2026 procurement |
| Loss stack | 11.0% combined | Itemised in `config.LOSSES` | **Soiling figure for Delhi needs a citation** |
| Shading criterion | `winter_9_to_3` | No inter-row shading 09:00–15:00 on 21 December | Chosen over `winter_noon`; recorded and reversible |
| Tariff | ₹8/kWh | Provisional | **Stands until D38 arrives.** All rupee figures are indicative |
| Plant capacity | back-calculated | `kWp = kWh / (days × PSH × PR)`, median across live months | **Estimate.** Never used for the FR-4 back-test (§5.5) |
| Building heights | storeys × 3.5 m | Storey counts from survey | **Provisional.** Confirm before Part 6 |

**Losses combine multiplicatively**, as `1 − Π(1 − lᵢ)`, not by addition. Adding the
percentages overstates the total, since each stage acts only on what the previous one
passed through. The default stack sums to 11.5 per cent but combines to 11.0 per cent.

None of the values flagged above are fully defended yet. Each needs either a citation or a
measurement before the final report.

# 11. Deviations from the specification

The project has departed from the written specification in five places. Each was a
reasoned decision, recorded at the time, and each is listed here rather than left to be
discovered.

**1. The validation set is six installations, not two.** The specification reserved two
existing installations for validation. The meter data revealed 29 locations already
carrying photovoltaic panels, about 20 of them generating. Six are now carried as primary
validation, chosen for record length and for pairing with candidates. The validation set is
an order of magnitude better than planned; the untapped set is correspondingly smaller.

**2. FR-1's acceptance criterion needs restating.** It assumed the two irradiance sources
would agree within 5 per cent. They do not, for a physical reason (§6.3). The proposed
restatement is in §8.2.

**3. `buildings_without_solar.xlsx` (D13) was derived, not requested.** The meter data
names the occupied roofs; OpenStreetMap plus imagery gives the rest. This removed a
request from the list entirely.

**4. Google Open Buildings (D09) was descoped.** Its value was an independent footprint
and height; neither is needed once ten roofs are digitised by hand and heights come from
storey counts plus shadow measurement (§6.6).

**5. Candidate selection is by matched pairs, not roof size.** The specification did not
anticipate that enough near-identical instrumented buildings would exist to make
like-for-like prediction possible. Seven of the ten candidates are chosen on this basis
(§4.4).

# 12. Plan for Parts 5 to 9

## 12.1 Part 5 — Rooftop segmentation model

**Do:** Train a segmentation network on the INRIA aerial image labelling dataset, run it
over the campus imagery, and compare its output against the hand-digitised ground truth
from Part 4.

**Uses:** D10, D11, D29 · **Produces:** segmentation accuracy report
**Acceptance (FR-2b):** IoU ≥ 0.75 against manual ground truth.

**Why this part exists.** Ten roofs took roughly thirty minutes each to trace by hand; two
hundred would take a hundred hours. The model exists to make the method **scale**, not to
be novel. That is a better justification than "the specification mentions machine
learning", and it is the framing the project will defend.

**The hand-drawn version remains the official one.** If the model underperforms, that is
still a result — where it failed and why is reportable.

## 12.2 Part 6 — Shading analysis

**Do:** Extrude the footprints to a digital surface model, add parapets and tree canopy,
and run UMEP for hourly shading factors across the year. Validate against a shadow
measured in a dated satellite image.

**Uses:** D29, heights, D10 (**the dated image**) · **Produces:** D30, D31
**Acceptance (FR-3):** modelled shadow within 15 per cent of the observed one.

**Already simplified by Part 3.** The PVGIS horizon profile established that the far
horizon is flat, 0.0°–1.9° in every direction, so no distant terrain shades the campus.
All shading is local — adjacent buildings, parapets and trees.

**Two carried-forward items land here.** Building heights are provisional at storeys ×
3.5 m and must be confirmed, because a wrong floor height propagates straight into this
model. And the tree overhang deliberately excluded from the Part 4 obstruction layer must
be picked up here, not lost.

## 12.3 Part 7 — Generation modelling and validation

**Do:** Build a pvlib model chain per building — Perez transposition, explicit cell
temperature, itemised loss stack — apply the Part 6 shading factors, then back-test
against the real fleet.

**Uses:** D07 (primary irradiance), D06 (temperature), D31, D04 · **Produces:** D32, D35
**Acceptance (FR-4):** specific yield 1300–1600 kWh/kWp/yr, within 10 per cent of PVGIS,
back-tested against metered output.

**The back-test is restructured to avoid circularity.** Because plant capacity is itself
back-calculated from generation, the naive specific-yield test would pass by construction
(§5.5). Two genuinely independent checks replace it:

1. **Shape validation.** Normalise modelled and measured generation to their own annual
   totals and compare the monthly profile — December trough, April peak, July monsoon dip.
   This tests the irradiance, shading and temperature modelling without capacity appearing
   anywhere. The method is already proven: it is what arbitrated FR-1 in Part 3.
2. **Independent capacity from imagery.** Count module rows on the existing arrays in the
   satellite imagery already being digitised, and derive capacity from array area. Compare
   against the energy-derived figure. Agreement between two independent routes is real
   evidence; disagreement is itself a reportable finding.

**Still improved by D12.** If the plant schedule arrives, the direct back-test becomes
available and both checks above become corroboration rather than substitution.

## 12.4 Part 8 — Feeder impact study

**Do:** Build one 11 kV feeder in OpenDSS with transformers, cable lengths and
per-building load profiles. Run the annual time series with and without solar, and find
voltage rise, reverse power flow and hosting capacity.

**Uses:** D16, D17, D18, D19, D23, D22, D32 · **Produces:** D33, D34
**Acceptance (FR-5):** base-case loading within 15 per cent of billed consumption.

**This is the only blocked part.** D16, D17 and D18 are the sole items in the project that
cannot be derived, fetched or estimated (§13).

**If they never arrive**, the specification's own mitigation applies: build a
representative feeder from transformer ratings and map distances, and declare every
assumption. But the FR-5 calibration criterion **cannot then be tested**, and the final
report must say so plainly rather than presenting an uncalibrated model as validated.

**Method note.** D01 and D02 are *daily* totals, so they cannot supply the hourly
generation shape this part needs. The shape will be modelled with pvlib and calibrated
against the daily totals — and the report will say so explicitly.

## 12.5 Part 9 — Synthesis and report

**Do:** Produce a ranked table of untapped buildings by capacity and yield; campus-level
MWp and MWh; hosting capacity; payback and levelised cost; avoided emissions. Ensure the
code regenerates every figure from the raw data.

**Uses:** everything above, plus D38 (tariff), D36 (capital cost) and D37 (emission
factor) — the three inputs the economics cannot be written without.

# 13. Risks and blockers

## 13.1 The three true blockers

| ID | Document | Why it cannot be substituted |
|---|---|---|
| **D16** | `electricity_bills_2024_2025.xlsx` | FR-5's acceptance criterion *is* calibration against billed consumption. The meters we hold are generation meters; they say nothing about load. Without this, the criterion cannot be run at all |
| **D17** | `campus_single_line_diagram.pdf` | Which buildings sit on which feeder is not visible from imagery and not inferable from generation data |
| **D18** | `transformer_schedule.xlsx` | Transformer ratings and their served buildings cannot be derived from any source we can reach |

All three are needed by **Part 8 alone**. Every other part of the project can proceed
without them. This is the single request the project would most like the review panel's
help with.

## 13.2 Other risks

| Risk | Impact | Mitigation |
|---|---|---|
| **B10 Central Workshop area is wrong** | ~500 kWp of the 2.2 MWp headline | Re-inspect against imagery before the final figure is published (§7.10) |
| **D12 plant schedule never arrives** | FR-4 direct back-test unavailable | Already mitigated: two independent checks replace it (§12.3) |
| **Provisional building heights** | Propagates into the FR-3 shading model | Confirm floor heights during Part 6 site work |
| **Unconfirmed tariff (D38)** | All rupee figures indicative | Public DERC order gives an indicative rate; only the contracted rate needs asking |
| **Undefended design values** | Tilt, setback, packing factor unsourced | Each needs a citation or measurement before the final report (§10) |
| **Possible unmetered array on B06** | Existing fleet larger than recorded | Raise with the Estate Office (§7.10) |
| **Missing 2025 hostel meter data (D15)** | 2025 and 2024 totals not comparable | Already declared; do not read the difference as a decline |

# 14. Timeline

| Period | Work | Status |
|---|---|---|
| Weeks 1–4 | Scoping, specification, data requests | Complete (predates the repository) |
| Week 5 | Repository established; meter workbooks parsed (Part 2) | **Complete** |
| Week 5 | Part 1 — candidate list locked, 22 September 2026 | **Complete** |
| Week 5 | Part 3 — irradiance sources obtained and arbitrated | **Complete** |
| Week 5–6 | Part 4 — all ten roofs digitised, closed 23 September 2026 | **Complete** |
| — | **Mid-term review** | **This report, 24 September 2026** |
| Weeks 6–7 | Part 6 — DSM and UMEP shading (UMEP added to QGIS from week 6) | Planned |
| Weeks 7–8 | Part 7 — pvlib generation model and back-test | Planned |
| Weeks 7–9 | Part 5 — segmentation model | Planned |
| Weeks 8–9 | Part 8 — feeder study, *if D16/D17/D18 arrive* | At risk |
| Weeks 9–10 | Part 9 — synthesis, economics, final report | Planned |
| 31 October 2026 | Review period ends | — |

> **A note for the record.** The repository was created in week 5 rather than week 1 as
> the workflow asked, so weeks 1 to 4 are not represented in the commit history. This is
> recorded in `docs/decisions.md` rather than left to be inferred.

# 15. References

**Data sources**

1. NASA POWER. *Prediction of Worldwide Energy Resources*, hourly meteorological data,
   2014–2023. NASA Langley Research Center. <https://power.larc.nasa.gov/>
2. PVGIS. *Photovoltaic Geographical Information System*, Typical Meteorological Year and
   horizon profile. European Commission, Joint Research Centre.
   <https://re.jrc.ec.europa.eu/pvg_tools/>
3. OpenStreetMap contributors. Building footprints for the IIT Delhi campus bounding box,
   retrieved September 2026. <https://www.openstreetmap.org/>
4. Esri. *World Imagery* basemap, streamed via QGIS.
5. Maggiori, E. et al. *Can Semantic Labeling Methods Generalize to Any City? The INRIA
   Aerial Image Labeling Benchmark.* IGARSS, 2017. *(Part 5 training data.)*

**Standards and reference figures, to be cited in the final report**

6. Ministry of New and Renewable Energy, Government of India. Benchmark capital cost for
   grid-connected rooftop solar photovoltaic systems. *(D36 — Part 9.)*
7. Central Electricity Authority, Government of India. *CO₂ Baseline Database for the
   Indian Power Sector.* *(D37 — Part 9.)*
8. Delhi Electricity Regulatory Commission. Tariff order applicable to institutional
   consumers. *(D38 — Part 9.)*

**Software**

9. QGIS Development Team. *QGIS Geographic Information System.* Open Source Geospatial
   Foundation.
10. Holmgren, W.F., Hansen, C.W., Mikofski, M.A. *pvlib python: a python package for
    modeling solar energy systems.* Journal of Open Source Software, 2018. *(Part 7.)*
11. Lindberg, F. et al. *Urban Multi-scale Environmental Predictor (UMEP).* Environmental
    Modelling & Software, 2018. *(Part 6.)*
12. EPRI. *OpenDSS — Distribution System Simulator.* *(Part 8.)*

**Project documents**

13. `docs/BTP_Functional_Specification_Rooftop_Solar_IITD.pdf` — the specification this
    work implements.
14. `docs/Rooftop_Solar_BTP_10_Week_Workflow.pdf` — the week-by-week plan.
15. `docs/decisions.md` — the dated decision and assumption log.
16. `docs/part4_methodology.md` — the full Part 4 method.

<div class="pagebreak"></div>

# Appendix A — Per-building results

Reproduced from `data/building_register.csv`, which is the authoritative source.

| id | building | category | storeys | gross m² | obstr. m² | setback m² | net m² | module m² | kWp | usable % | obstructions |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B01 | Block 3 | academic | 4 | 3,132 | 275 | 622 | 2,235 | 1,342 | 288.6 | 42.9% | 4 |
| B02 | Block 4 | academic | 4 | 2,729 | 204 | 454 | 2,071 | 1,244 | 267.5 | 45.6% | 4 |
| B03 | Dronagiri House | hostel | 7 | 2,214 | 848 | 236 | 1,130 | 678 | 145.9 | 30.6% | — |
| B04 | Saptagiri House | hostel | 7 | 2,161 | 823 | 228 | 1,110 | 666 | 143.3 | 30.9% | — |
| B05 | Vindhyachal Hostel | hostel | 4 | 3,653 | 975 | 556 | 2,122 | 1,274 | 274.0 | 34.9% | — |
| B06 | Lecture Hall Complex | academic | 5 | 6,379 | 2,058 | 557 | 3,764 | 2,261 | 486.0 | 35.4% | — |
| B07 | Academic Complex East | academic | 6 | 2,393 | 0 | 379 | 2,014 | 1,209 | 260.0 | 50.5% | 0 |
| B08 | Textile Technology | laboratory | 4 | 4,003 | 2,531 | 563 | 910 | 546 | 117.5 | 13.7% | — |
| B09 | Material Science | laboratory | 4 | 598 | 0 | 115 | 483 | 290 | 62.3 | 48.5% | 0 |
| B10 | Central Workshop | service | 2 | 2,399 | 743 | 296 | 1,360 | 816 | 175.6 | 34.0% | — |
| | **TOTAL** | | | **29,661** | **8,457** | **4,006** | **17,198** | **10,328** | **2,220.6** | | **21** |

Constants applied throughout: ground coverage ratio 0.7066, packing factor 0.85, module
power density 215 W/m², setback 1.0 m, design sun elevation 22.32°, criterion
`winter_9_to_3`.

![The ten traced roofs and their obstructions, labelled B01–B10.](reports/figures/campus_roofs_map_slide.png)

# Appendix B — The building register and its schema

`data/building_register.csv` holds one row per building and one column per computed
number. It carries 16 rows — ten candidates (B01–B10) and six validation buildings
(V01–V06) — across 29 columns.

| Group | Columns |
|---|---|
| Identity | `building_id`, `building_name`, `category`, `role`, `selected`, `has_existing_pv`, `osm_id`, `lat`, `lon` |
| Physical | `storeys`, `height_m`, `height_source`, `footprint_source` |
| Digitising (Part 4) | `gross_roof_area_m2`, `obstruction_area_m2`, `roof_perimeter_m`, `obstruction_count`, `digitised_by`, `digitised_date`, `notes` |
| Area chain (FR-2) | `setback_area_m2`, `net_available_area_m2`, `ground_coverage_ratio`, `packing_factor`, `module_area_m2`, `installable_capacity_kwp`, `usable_fraction_of_roof` |
| Design point | `design_sun_elevation_deg`, `design_criterion` |

**The standing rule.** Every column must have an entry in `data/register_schema.yml`
naming the module that produced it and the formula behind it. `tests/test_register.py`
fails if a column appears without one. The register is CSV rather than a spreadsheet
binary so that a changed number appears as a readable diff in version control.

# Appendix C — Reproducibility

Every figure and every number in this report regenerates from the repository.

## Getting started

```bash
make setup     # uv sync --extra dev, pinned to Python 3.12
make test      # the geometry derivations and every acceptance criterion
make register  # print the building register with its provenance
```

QGIS is installed separately and is not a Python dependency of this package. The UMEP
plugin is added from inside QGIS and is required from week 6.

## Repository layout

```
data/              every data file: downloaded inputs, the meter workbooks,
                   and the products this code writes
docs/              specification, workflow, methodology, and the decision log
qgis/              the QGIS project and layer styles
src/btp_solar/     one module per functional requirement
scripts/           entry points, one per part
tests/             the derivations and every acceptance criterion
reports/           figures and the written report
```

## Which script produces which result

| Result in this report | Script |
|---|---|
| §5 Monthly generation per plant | `scripts/run_campus_meters.py` |
| §5.4 Stopped plants and lost energy | `scripts/run_outage_report.py` |
| §6.3–6.5 Irradiance source arbitration | `scripts/run_fr1_source_selection.py` |
| §7.5 The seven roof validity checks | `scripts/check_roofs.py` |
| §7.6–7.7 Area chain and register update | `scripts/run_fr2_from_gpkg.py` |
| §3 The nine-part diagram | `scripts/make_parts_diagram.py` |
| Appendix B The register, printed | `scripts/show_register.py` |

## Modules

| Ref | Module | Purpose |
|---|---|---|
| FR-1 | `fr1_data.py` | Irradiance acquisition and source comparison |
| FR-2 | `fr2_usable_area.py`, `solar_geometry.py` | The area chain; sun position and ground coverage ratio |
| FR-3 | `fr3_shading.py` | Shading (Part 6) |
| FR-4 | `fr4_generation.py` | Generation modelling (Part 7) |
| FR-5 | `fr5_feeder.py` | Feeder impact (Part 8) |
| — | `campus_meters.py` | Meter workbook parsing, capacity estimation, outage detection |
| — | `register.py`, `acceptance.py`, `config.py` | The audit trail, the executable criteria, and every tunable constant |

---

*Repository: <https://github.com/seanthesheep1/B.Tech-Project.git>*

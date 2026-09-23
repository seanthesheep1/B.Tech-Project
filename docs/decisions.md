# Decision and assumption log

Every choice that a number depends on goes here, with the date and the reason.
When the report says "we assumed X", this file is what it is quoting. Append
at the bottom; do not rewrite history.

The risk table in the specification makes this file load-bearing: three of the
four named risks are mitigated by "declare the assumption and proceed", which
only works if the assumptions are written down as they are made.

---

## 2026-09-21 — Repository initialised

Project skeleton created: module per functional requirement, the building
register as the single audit trail, and each acceptance criterion from the
specification implemented as an executable check.

Note for the record: the repository was created in week 5 rather than week 1 as
the workflow asked, so weeks 1 to 4 are not represented in the commit history.

## 2026-09-21 — Inter-row spacing criterion

`config.SHADING_CRITERION = "winter_9_to_3"`.

Rows are spaced so they do not shade each other between 09:00 and 15:00 solar
time on the winter solstice, rather than at solar noon alone. This is the
conventional design window and the stricter of the two. At the campus latitude
it gives a design sun elevation of 22.32° at 44.53° east of south, and a ground
coverage ratio of 0.707 at 15° tilt against 0.771 for the noon-only criterion —
about 8% less module area for a materially lower winter-morning loss.

To revisit: whether the six-hour window is the right trade for a campus that
draws most of its load in the middle of the day.

## 2026-09-21 — Array design values, all provisional

| Value | Setting | Basis | Status |
|-------|---------|-------|--------|
| Tilt | 15° | Common flat-roof ballasted racking in north India; below the latitude-optimum 28° to cut wind load and row spacing | **Confirm against a real campus installation** |
| Setback | 1.0 m | Workflow note | **Check the applicable fire code; 1 m may be too little** |
| Packing factor | 0.85 | Allowance for walkways, inverter pads, cable trays | **Assumed, not sourced** |
| Module power density | 215 W/m² | ≈22% efficient module on glass area | Reasonable for 2026 procurement |
| Loss stack | 11.0% combined | Itemised in `config.LOSSES`, combined multiplicatively | Soiling figure for Delhi needs a citation |

None of these are defended yet. Each needs either a citation or a measurement
before it appears in the report.

## 2026-09-21 — Losses combine multiplicatively

The itemised losses are combined as 1 − Π(1 − lᵢ), not by addition. Adding the
percentages overstates the total, since each stage acts only on what the
previous one passed through. The default stack sums to 11.5% but combines to
11.0%.

---

## Template for new entries

    ## YYYY-MM-DD — <what was decided>

    <the decision, in one or two sentences>

    Reason: <why, including what was rejected>
    Affects: <which FR, which register columns>
    Revisit if: <what would change this>

---

## 2026-09-21 — Supervisor's meter data received and parsed

Two workbooks covering Jan 2024 to Apr 2026: daily cumulative register
readings for the rooftop PV already installed on campus. 17,006 readings,
31 plants, 28 monthly sheets. Copied to `data/`, parsed by
`src/btp_solar/campus_meters.py`, monthly series written to
`data/campus_solar_monthly.csv`.

These are **generation** meters, not consumption meters. They do not answer
the load-profile question for FR-5; that data is still outstanding.

### Format handling, each of which changes the numbers

- **Meter factor.** Every column carries an MF of 1 to 80; energy is the
  register difference times that factor. The Jan–Jun 2024 sheets omit the MF
  row, but the registers run continuously into the July sheets, so the later
  factors apply throughout.
- **Column order changes between sheets.** Joined on meter number, never
  position.
- **Transcription errors.** 97 readings dropped: decimal slips (1113411.2 for
  113341.7), blanks entered as 0, and one month whose dates are text. Naive
  differencing of the raw register inflates annual generation by roughly ten
  times.
- **29490555 and 42490555 are one plant.** Last reading under the first number
  (31 Jul 2025, 155597.2) and first under the second (1 Aug 2025, 155631.2)
  differ by one ordinary day. A replaced meter would restart near zero, so
  this is a relabelling, not a second plant. Folded in `METER_ALIASES`.

### What this changes about the project

The specification assumes eight to ten candidate buildings with no PV and
**two** existing installations retained for validation. The data shows **29
locations already carrying rooftop PV**, about 20 of them generating. That is
a far stronger validation set than two, and it shrinks the untapped set.
Both the scope in section 1 and the register's `role` column need revisiting
with the supervisor before M2 is signed off.

Six plants have stopped: Central Library (last generated Jun 2025), Main /
Amaltas Guest House (May 2024), Main Building, both Vishwakarma meters, and
SIT Building (Apr 2024). Whether these are dead plants or unread meters is an
open question for the Estate Office, and either answer is a reportable result.

The whole of 2025 is missing the hostel meters: sheets Jan-25 to Dec-25 carry
only 17 of the 31 columns. The 2025 total of 540 MWh is therefore not
comparable with 2024's 955 MWh.

Capacity in kWp is **not** in this data, so specific yield — the FR-4
acceptance criterion — cannot yet be computed for any plant. That single
missing item is the highest-priority data request.

---

## 2026-09-22 — Part 1 closed: building list locked

Project team recorded as Tejas Suresh Kamble (2023EE10974) and Surbhi Rathore
(2023EE11224), supervised by Prof. Yashasvi Bansal. The specification PDF still
carries placeholders for both; the register and README are now authoritative.

### How the candidates were found

The candidate pool was **derived rather than requested**, which removes
`buildings_without_solar.xlsx` from the data request entirely. Campus building
footprints were pulled from OpenStreetMap (1,257 polygons in the campus box,
102 named), cross-referenced against the 29 locations the meter data shows
already carry PV, and the remainder surveyed on foot on 22 September 2026.

Of 30 shortlisted buildings: 3 were ruled out for sloped roofs (`4 LT 3`,
`6 LT 1`, `2A/05`), 6 were found to already carry panels (Blocks 1, 2, 5, 6 and
the Focus Incubation Centre), leaving **21 viable candidates**. Ten were
selected.

### Selection principle: matched pairs

The ten were not chosen for roof size alone. Seven of them sit in two groups
where a near-identical building already carries PV and is in our validation
set:

- **Blocks 3 and 4** against Blocks 1, 2, 5 and 6 — same design, same era, same
  orientation, four of six already instrumented.
- **Dronagiri, Saptagiri and Vindhyachal** against the thirteen hostels that
  already carry PV, of which Karakoram and Shivalik are in the validation set.

This turns the back-test from a generic plausibility check into a like-for-like
prediction, which is a materially stronger claim than the specification
originally anticipated.

Reserve list, in order: Academic Complex West, Admin Building, Mathematics
Department, RnI Park, Dogra Hall.

### Validation set widened from two to six

The specification reserves **two** existing installations. The meter data
revealed 29 locations with PV, about 20 generating, so six are now carried as
primary validation (V01–V06) chosen for record length and for pairing with the
candidates. The remaining live plants stay available as a secondary set.
`tests/test_register.py` was updated accordingly.

### Provisional values to revisit

Building heights are recorded as **storey count x 3.5 m** and flagged
`provisional` in `height_source`. Confirm the floor height during the Part 4
site visits; a wrong floor height propagates straight into the FR-3 shading
model.

`Student Activity Centre` and `Students Activity Center` are two OSM polygons
120 m apart. Neither was selected, but if either is promoted from the reserve
list, establish first whether they are one building or two.

---

## 2026-09-22 — Part 3: irradiance sources, and PVGIS unreachable

**NASA POWER (D07) obtained.** Hourly series for 28.545 N, 77.192 E, 2014 to
2023, 6.4 MB. Annual global horizontal irradiation **1744.7 kWh/m2/yr**, which
is in the expected band for Delhi.

**PVGIS (D06) could not be fetched.** `re.jrc.ec.europa.eu` resolves and
completes the TLS handshake but then closes without responding, on both the
v5_2 and v5_3 endpoints and on the plain web page. The whole host is
unreachable from this machine, not just the API. It must be downloaded through
a browser instead; the fetcher in `fr1_data.py` is left in place for when the
host is reachable again.

Until it arrives, **FR-1's acceptance criterion cannot be evaluated** - the
5 per cent agreement test needs two independent sources and we have one.

**Google Open Buildings (D09) recommended for descoping.** Its value under FR-1
was an independent footprint and height. For ten buildings we are digitising by
hand in Part 4 the footprint adds nothing, and a better independent height is
available from the storey counts already collected plus shadow length measured
in imagery during Part 6. Dropping it avoids a large download for no gain.
Heights currently stand at storey count x 3.5 m, flagged provisional.

**D36 and D37** (benchmark capital cost, grid emission factor) are Part 9
inputs and are deferred until the economics are written.

**Tracking policy for downloaded data.** `footprints_osm.json` is tracked
because OpenStreetMap is a living map and a later re-download would not
reproduce the same footprints. The irradiance files are not tracked: for a
fixed date range both APIs return identical data, so they are genuinely
reproducible.

## 2026-09-22 — PVGIS horizon profile validates the FR-2 geometry

The horizon profile for the campus point was downloaded by hand. It is **not**
the TMY that FR-1 needs, but it turned out to be worth keeping for two reasons.

**It independently confirms the solar geometry.** PVGIS computes its own solar
positions, and its winter solstice series agrees with our closed-form
derivation to within rounding:

| | ours | PVGIS |
|---|---|---|
| Elevation at solar noon, 21 Dec | 38.01 deg | 38.00 deg |
| Elevation at the 09:00 design point | 22.32 deg | 22.30 deg |
| Azimuth at the 09:00 design point | 44.53 deg | 44.50 deg |

This matters because that geometry sets the ground coverage ratio, and the GCR
sets every usable-area and installable-capacity figure in FR-2. It is now
pinned by `test_matches_pvgis_winter_solstice`.

**The far horizon is flat**, between 0.0 and 1.9 degrees in every direction. No
distant terrain shades the campus, so all shading in FR-3 is local - adjacent
buildings, parapets and trees. That simplifies Part 6 and is worth one line in
the report.

**Site elevation corrected** from an assumed 216 m to PVGIS's DEM value of
229 m in `config.SITE_ELEVATION_M`.

The TMY (D06) is still outstanding and FR-1 still cannot be evaluated.

---

## 2026-09-22 — FR-1 fails its acceptance criterion, for a real reason

Both irradiance sources are now in hand:

| Source | Period | Annual GHI |
|---|---|---|
| PVGIS TMY (ERA5) | 2005–2023 | **1930.0** kWh/m2/yr |
| NASA POWER | 2014–2023 | **1744.7** kWh/m2/yr |

The gap is **10.1 per cent** against the specification's 5 per cent tolerance,
so **FR-1 does not pass as written**. Units and fill values were checked first:
NASA POWER returns Wh/m2 per hour with no fill values in this record, and the
PVGIS TMY has a full 8,760 rows, so the gap is not an arithmetic error.

### The disagreement is seasonal, not uniform

Mean daily GHI, kWh/m2/day:

| | Jan | Apr | Jul | Oct |
|---|---|---|---|---|
| NASA POWER | 2.84 | 6.55 | 4.82 | 4.62 |
| PVGIS | 4.19 | 7.14 | 4.69 | 5.40 |

The two agree closely through the monsoon and diverge sharply in winter, where
PVGIS is up to 47 per cent higher. That is the signature of winter fog and
aerosol over the Indo-Gangetic Plain, which ERA5 reanalysis is known to
represent poorly.

### The campus meters arbitrate

Rather than choose by assertion, the fleet's own generation was used. Monthly
generation and monthly irradiance were each normalised to their annual total
and compared as seasonal **shape**, so unknown plant capacity cancels and the
test is not circular. 18 plants had a complete live 2024, totalling 792 MWh.

    total absolute shape error   NASA 0.072    PVGIS 0.109
    Jan/Apr ratio   measured 0.429   NASA 0.433   PVGIS 0.587

NASA POWER reproduces the measured seasonal shape closely; on the January to
April ratio it is almost exact while PVGIS is 37 per cent too high.

The tilt effect strengthens this rather than weakening it. Measured output is
plane-of-array on modules tilted about 15 degrees, which *raises* the winter
share relative to GHI, and summer temperature derating raises it further. The
true GHI winter share implied by the measurements is therefore lower still, so
PVGIS's winter excess is larger than the table shows.

### Decision

**NASA POWER becomes the primary irradiance source** for FR-4. PVGIS is
retained as the secondary source and its divergence carried as a declared
uncertainty band. Had PVGIS been used without checking, annual yield across the
campus would have been overstated by roughly 10 per cent.

**To raise with Prof. Bansal:** FR-1's acceptance criterion assumed the two
sources would agree. They do not, for a physical reason we can evidence. The
criterion should be restated as "where the sources disagree, the choice is
justified against measured generation" — which we have now done.

Reproduce with `scripts/run_fr1_source_selection.py`.

---

## 2026-09-22 — Four existing plants have stopped; the cost of the outages

Differencing the registers shows **four of the 31 plants have not generated for
six months or more**:

| Plant | est. kWp | Last generated | Months idle | Lost MWh |
|---|---|---|---|---|
| Main / Amaltas Guest House | 34 | May 2024 | 23 | 97.9 |
| Central Library | 38 | Jun 2025 | 10 | 47.4 |
| Main Building | 14 | Aug 2025 | 8 | 14.7 |
| Vishwakarma | 9 | Oct 2025 | 6 | 6.8 |
| | | | | **166.8** |

At a provisional ₹8/kWh that is roughly **₹13 lakh of electricity not
generated**, with about **₹1 lakh a month** still being lost from 95 kWp
standing idle.

**Why it went unnoticed.** A reading was written down every day throughout —
the register simply never moved. Collected faithfully, filed, never
differenced. The evidence was in the workbooks from the day they were handed
over.

### Honesty about the numbers

The **outages are fact**: a register that does not move has not generated.

The **rupee figures are estimates** resting on two assumptions — the
back-calculated capacity in `Plant.estimated_kwp`, and a tariff of ₹8/kWh which
is provisional until D38 arrives. They must be reported as indicative, with the
method stated. The outage count and durations need no such caveat.

### Guard against false positives

`lost_kwh` reports nothing until a plant has been idle longer than
`config.OUTAGE_MONTHS` (six), so a monsoon lull or a spell of missing readings
is not announced as a failure. `test_a_short_gap_is_not_an_outage` pins this.

### Why this matters to the project

The specification frames the work as finding untapped roofs. This is the
opposite question — whether what is already installed still works — and it is
answerable from data the Institute already holds, before any new panel is
costed. It belongs in the report as a finding in its own right, and it should
be raised with Prof. Bansal early, because unlike everything else in this
project it has a consequence today.

Reproduce with `scripts/run_outage_report.py`.

---

## 2026-09-22 — Part 4 started: preliminary areas from OSM outlines

Polygon geometry for the ten candidates was fetched from OpenStreetMap
(the Part 1 query returned centroids only) and projected to EPSG:32643 to give
a first area and perimeter for each. Written to `data/candidate_roofs.geojson`
as the starting layer for hand digitising.

Running the FR-2 area chain over these outlines, with obstructions assumed at
8 per cent until they are digitised, gives a **preliminary 4,335 kWp across
40,832 m2 of footprint** - about 5.7 times the existing campus fleet.

**This number is not yet defensible and must not be quoted.** Three reasons:

1. OSM polygons are *building* outlines, not *roof* outlines. They can include
   courtyards, overhangs and adjoining structures.
2. The 8 per cent obstruction allowance is a placeholder. Real roofs carry
   water tanks, stair rooms, lift rooms and air conditioning plant, and the
   real figure will differ per building.
3. Several polygons look wrong. **B09 Department of Material Science comes out
   at 646 m2** from a 6-node rectangle, which is implausibly small for a
   department block and suggests only part of it is mapped. B07 Academic
   Complex East (43 nodes) and B05 Vindhyachal (37 nodes) are complex shapes
   that may enclose courtyards.

Correcting these against imagery is precisely what Part 4 is for. The
preliminary figure is recorded so the effect of the manual work can be
measured: if hand digitising moves the total materially, that itself is a
result worth reporting, because it quantifies the error in the open-data
shortcut that many rooftop studies stop at.

## 2026-09-22 — B06 was the wrong building; courtyards now subtracted

**A bad polygon reached the preliminary total.** B06 Lecture Hall Complex is an
OSM *relation*, but the geometry query asked for `way(id:19120455)`. Way ids
and relation ids are separate number spaces in OSM, so the query returned a
different building that happens to carry the same number — one in Ohio, at
-82.46 E, 40.08 N. It came back with a plausible 7,158 m2 and was carried
straight into the 4,335 kWp preliminary figure.

Nothing about the number looked wrong. It was caught only when converting the
candidates to UTM for QGIS, where B06 landed at a coordinate that is not on
Earth's land surface.

`tests/test_candidate_roofs.py::test_every_polygon_is_on_the_campus` now checks
every vertex of every candidate against a campus bounding box on each run.

**The correct B06 is a multipolygon with a courtyard**: an outer ring of
8,373 m2 and an inner ring of 408 m2. The inner ring is sky, not roof, so it is
subtracted; its edge is added to the perimeter, because the fire setback
applies to a courtyard edge exactly as it does to the outer edge.

Corrected preliminary total: **4,429.5 kWp over 41,639 m2** (was 4,334.9 kWp
over 40,832 m2).

The lesson generalises to the digitising in Part 4: several of these buildings
are complex shapes and any of them may enclose a light well. `has_courtyard` is
now recorded per building so the hand digitising can confirm each one.

## 2026-09-22 — Obstruction conventions settled during digitising

Four decisions came out of digitising B01 and B02, all of which generalise to
the remaining roofs.

**Obstructions were assigned to the wrong building.** All six polygons drawn on
the two parallel blocks named the neighbouring block. The labels sit near the
gap between them, which makes it easy to pick the wrong id. Caught by testing
each polygon's centroid against each roof outline rather than by eye, and
corrected in bulk. Worth re-running that containment check after every
digitising session.

**An overhanging tree is not an obstruction.** It was drawn as one and has been
deleted. A tree canopy does not occupy roof area; it shades it. Subtracting it
here *and* modelling it in FR-3 would penalise the same square metres twice.
Overhangs belong in Part 6.

**A gap between buildings is not roof.** It was drawn as an obstruction; it is
now an inner ring of B01's polygon, as with B06's courtyard. Both treatments
subtract the area, but only the hole also adds the gap's edge to the perimeter,
so the fire setback is applied around it. Left as an obstruction the setback
there would have been missed.

**Rule of thumb.** Something standing *on* the roof - tank, stair room, lift
room, air conditioning plant - is an obstruction. Something that is *not roof
at all* - courtyard, light well, gap between blocks - is a hole. Something that
blocks *light* rather than occupying area is shading, and belongs to FR-3.

Digitised so far: B01, B02, B08, B09 corrected; B01 and B06 carry holes; four
obstructions recorded on B01 and B02. The remaining six roofs still sit on
their OSM outlines with the 8 per cent obstruction placeholder.

Current total **39,541 m2 and 4,202 kWp**, down from the 4,429 kWp preliminary
figure as the hand digitising pulls the outlines off open ground and onto the
roofs themselves.

## 2026-09-23 — All ten roofs digitised

Every candidate roof is now hand-corrected and `verified`. The campus footprint
falls from **41,639 m2 on OpenStreetMap outlines to 29,661 m2 digitised, a drop
of 29 per cent**, and installable capacity with it to 3,035 kWp.

That 29 per cent is a result in its own right. Many rooftop potential studies
stop at open building footprints; this measures what stopping there costs. The
error is also **not uniform** - B05 Vindhyachal came in within half a per cent
of its OSM outline while B10 Central Workshop fell 67 per cent - so it cannot
be corrected with a blanket factor. That is the argument for digitising rather
than scaling.

| | OSM | digitised | change |
|---|---|---|---|
| B01 Block 3 | 4,501 | 3,132 | −30% |
| B02 Block 4 | 3,287 | 2,729 | −17% |
| B03 Dronagiri House | 3,854 | 2,214 | −43% |
| B04 Saptagiri House | 2,698 | 2,161 | −20% |
| B05 Vindhyachal Hostel | 3,663 | 3,653 | −0% |
| B06 Lecture Hall Complex | 7,965 | 6,379 | −20% |
| B07 Academic Complex East | 3,643 | 2,393 | −34% |
| B08 Textile Technology | 4,126 | 4,003 | −3% |
| B09 Material Science | 646 | 598 | −8% |
| B10 Central Workshop | 7,257 | 2,399 | −67% |

**B10 needs a second look before the figure is quoted.** A 67 per cent fall on
what was the largest roof is either correct - the OSM polygon wrapping a
workshop yard rather than a roof - or an under-trace. It is worth about 500 kWp.

**B06 carries no courtyard ring.** The previous outline had a 408 m2 hole and a
containment test against the new outline was inconclusive, 18 of 37 courtyard
vertices falling inside. Inspected on screen and judged not to need one. If
B06's yield later looks high against its neighbours, this is the first thing to
re-check.

`verified`, `digitised_by` and `digitised_date` were completed for B01, B02 and
B09, which had been traced without the flags being set.

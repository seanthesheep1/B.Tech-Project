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

## 2026-09-23 — Part 4 closed: FR-2 usable area

The area chain has been run from the digitised layers and every intermediate
value written to the register. **10,328 m2 of module area across the ten
candidate roofs, giving 2,220.6 kWp.**

| | m2 |
|---|---|
| gross digitised roof | 29,661 |
| less obstructions | 8,457 |
| less 1 m setback | 4,006 |
| net available | 17,198 |
| x GCR 0.707 x packing 0.85 | **10,328 module area** |

**FR-2 acceptance: the usable area is derived, not assumed.** The ground
coverage ratio of 0.707 comes from the winter design sun - 22.32 degrees
elevation at 44.53 degrees east of south - and that geometry is confirmed
against PVGIS to within rounding. The specification's objection to "an assumed
percentage" is met.

Usable fraction ranges from **13.6 per cent of gross roof on B08 to 50.5 per
cent on B07**, against the 40 to 50 per cent rule of thumb in the workflow
note. The rule holds only for roofs with few obstructions; it is badly wrong
for cluttered ones, which is the second argument against scaling factors.

### Open items carried into Part 5

**B06 carries two obstructions typed `solar_panel`.** B06 was selected as a
candidate precisely because it has no PV, and Lecture Hall Complex is not among
the 29 metered locations. Either panels have been installed recently, or they
are unmetered. Both are worth raising with Prof. Bansal: an unmetered array
would also mean the fleet is larger than the meter data shows.

**fid 19 on B06 subtracts 1,294 m2 while only 6 per cent of it lies on that
roof.** Confirmed as intended on inspection and left as drawn, but it costs B06
about 130 kWp and should be revisited if that roof's numbers look wrong later.

**fid 18 on B06 is typed `open_air`.** Open sky is properly a hole in the roof
polygon rather than an obstruction. As drawn the area is still subtracted
correctly; only the setback around its edge is missed. Left as is.

**B07 and B09 carry no obstructions**, inspected and confirmed. They show the
two highest usable fractions, 50.5 and 48.5 per cent, which is consistent.

---

## 2026-11-16 — Part 7 opened: the generation model chain

FR-4 is implemented in `fr4_generation.py` and run by
`scripts/run_fr4_generation.py`. **The ten candidate roofs model out at
3,280 MWh/yr from 2,220.7 kWp, a specific yield of 1,477 kWh/kWp/yr.**

The FR-4 plausibility band (1300–1600) **passes**. The PVGIS cross-check
**fails at 16.4 per cent** against a 10 per cent tolerance, for the reason set
out below.

### NASA POWER hourly data is in local solar time, not UTC

The downloaded file's header says `"time_standard": "LST"`. The hourly API
defaults to local solar time at the requested longitude, where hour 12 is
solar noon, and returns UTC only when asked; our fetch did not ask.

**Read as UTC, solar noon lands at about 17:00 IST.** Annual and monthly
irradiation totals are unchanged, so nothing looks wrong — the first run of the
chain produced a plane-of-array total *below* the horizontal total, which is
physically impossible at a 15° south tilt, and a cell temperature of 102 °C
from peak irradiance arriving at the hottest hour of the afternoon.

Handled by reading the standard from the file header and converting with the
longitude offset, 77.192/15 = 5 h 09 m. That places solar noon at 12:21 IST,
which is what the longitude requires. `time-standard` is now pinned in
`fr1_data.fetch_nasa_power` so a re-download reproduces the cached file, and
`test_local_solar_time_puts_the_sun_overhead_at_midday` fails if the peak hour
ever moves off midday again.

**Part 3 is unaffected.** The FR-1 source decision compared annual and monthly
totals, which a whole-hours shift does not change. Nothing hourly existed
before this step.

### New assumptions, all in config.py

| Value | Setting | Basis | Status |
|-------|---------|-------|--------|
| Decomposition | DIRINT | NASA POWER gives global irradiance only; Perez needs beam and diffuse separately | Erbs run as the sensitivity case |
| Transposition | Perez | Specification FR-4 | — |
| Ground albedo | 0.20 | Concrete and gravel roof surround | Assumed, not measured |
| Module temp. coefficient | −0.35 %/°C | Typical mono-PERC | **Confirm against a datasheet before the final report** |
| Inverter efficiency | 0.96 | Flat conversion efficiency | Clipping stays in `LOSSES`, since inverter sizing is not chosen yet — so it is not double counted |
| Wind shear exponent | 0.14 | Power law, 10 m to 2 m | NASA reports at 2 m, PVGIS at 10 m; without this the PVGIS case runs spuriously cooler |

The loss stack is unchanged at 11.0 per cent combined, so the figure in the
mid-term report still holds.

### The decomposition barely matters at 15°, and that is worth knowing

DIRINT and Erbs put the annual diffuse fraction 2.6 points apart — 0.506
against 0.480, a 45 kWh/m² difference in diffuse irradiation — yet the
plane-of-array total differs by 0.3 kWh/m² and the specific yield by less than
0.1 per cent. A plane tilted only 15° sees nearly the whole sky, so the split
hardly affects what it collects. The uncertainty we expected to have to declare
turns out not to bind here. **It would bind at a latitude-optimum 28° tilt**,
which is the other reason the low tilt is a defensible choice.

### Ten years, not a typical year

The NASA series is 87,648 hourly rows covering 2014–2023, so every year is
modelled and the result is reported as a mean with its spread:
**1,477 kWh/kWp/yr with a standard deviation of 37, about 2.5 per cent
year-to-year.** That is a real variability band rather than a single typical
year, and it is more than the specification asked for.

A partial calendar year is dropped rather than reported: shifting from local
solar time to UTC moves a few night hours of 1 January 2014 across the
boundary, and those hours would otherwise appear as a spurious eleventh year
with almost no energy.

### PVGIS reads 17.9 per cent high on the array plane

Part 3 found PVGIS 10.1 per cent high on annual GHI, concentrated almost
entirely in winter, and chose NASA POWER because it reproduced the measured
seasonal shape of the campus fleet. **Tilt amplifies that gap to 17.9 per cent**,
because tilt gain is largest when the sun is lowest — exactly the season where
PVGIS is in excess.

So FR-4's cross-check cannot pass while the two sources disagree, and it fails
for the same root cause as FR-1 rather than for a new one. The resolution is
the one already recorded: the choice of source is justified against measured
generation. **To raise with Prof. Bansal:** FR-4's second criterion, like
FR-1's, presumes the sources agree. Had PVGIS been used unexamined, the campus
yield figure would have been 3,869 MWh/yr instead of 3,280 — overstated by
nearly 600 MWh a year.

### What this pass is not

**Shading is unity.** Every roof therefore shares one specific yield, because
tilt, azimuth and site are common to all ten; only capacity differs. Part 6
supplies the hourly factors and this script is re-run, and the register's
`shading_applied` column says which pass produced its numbers so the two cannot
be confused. The figures above are an **unshaded upper bound**.

The back-test against metered generation is the next step and is not run here.

### Unrelated, and found on the way: the test suite was running on the wrong Python

`uv run pytest` resolved to Anaconda's pytest at `/opt/anaconda3/bin/python`,
not the project environment, because the dev extra had never been installed
into `.venv`. The existing 70 tests passed anyway — they need only pyyaml and
the standard library — so this was invisible until a test imported pvlib.
Fixed by `uv sync --extra dev`, as `make setup` always intended. Anything that
reports a dependency as missing should be checked against `sys.prefix` first.

---

## 2026-11-16 — The earlier panel-detection work is brought in as validation

The `rooftop-solar-pv` project from earlier in the year is reused, for one
purpose: **measuring the capacity of the existing campus plants from imagery,
with no meter data involved.**

Every capacity figure for the existing fleet is currently back-calculated from
generation, which makes it useless for validating the generation model — the
FR-4 back-test would pass by construction. A second, independent route breaks
that circularity. Two by-products come free: a census showing whether any array
is unmetered, and a real IoU number for FR-2b.

**The BTP's scope does not change.** The detector finds installed panels, not
usable roof. The hand-traced polygons from Part 4 remain this project's
measurement of usable area, and the untapped-roof figures stand as they are.

### What that project actually contains

| | |
|---|---|
| 976 annotated tiles, 4,865 arrays | **Real**, train 771 / valid 102 / test 103, COCO polygons |
| `model_final.pth`, `Dataset.zip` | **134-byte git-LFS pointers, not files.** The weights must come from the Drive link in `Resources.txt`; there is no `.git` directory, so `git lfs pull` will not work |
| `city_tile_fetcher.py` | Sound: async, resumable, correct grid maths |
| `generate_city_heatmap()` | **Unusable.** See below |

### The annotations outline array blocks, not panels

88.9 per cent of the 4,865 annotations are four-point quadrilaterals drawn
around a whole field of modules, gaps between rows included. Confirmed by
rendering them over their tiles. So a detection's area is **land** area, and
converting it to kilowatts needs the ground coverage ratio:

    kWp = block area x GCR x 215 / 1000

which is a pleasing cross-link: the GCR derived from the winter sun in Part 4
is reused here on real arrays, and agreement with the meter-derived capacity
would partly corroborate that derivation too. **Use a GCR measured on the real
arrays**, not our design value of 0.707 — that is what we would build, not what
somebody else did, and assuming it would smuggle an assumption into a check
whose point is independence.

### Correction to an earlier reading of the model's limits

The test report shows `APl = 0.000` and this was first read as the model being
weak on campus-scale arrays. That was wrong. Worked through: a 34 kWp plant is
158 m² of module, 224 m² of block, 3,253 px² at this resolution — the COCO
**medium** band, where the model scores its best (APm 51.5). Every campus plant
from 9 to 38 kWp falls in small or medium. `APl` is computed on a single test
instance and says nothing useful.

### The 872 m bug, and why the fix is structural

The old code recovered a tile's position by recomputing the grid in a second
script. The two disagreed: the fetcher stepped longitude by
`tile/(111320·cos φ)` and numbered only tiles it kept; the heatmap function
used the latitude step for both axes and numbered every grid point. Same id,
different place — reproduced against the IIT Delhi settings at a **median
872 m, and not one tile of 268 within a tile's width of where it belonged.**
Any heatmap that function produced is geographically wrong.

The fix is not a corrected formula. **A tile's position is recorded when the
tile is created and read back thereafter**, in
`data/campus_tiles_manifest.csv`. `src/btp_solar/imagery.py` holds the geometry
and `tests/test_imagery.py` pins it, including that the two degree steps differ
by 1/cos φ and that a detection is placed from the manifest rather than from
any grid.

### The campus grid

Bounded by the ten digitised roofs plus the validation buildings rather than a
1.5 km circle: **80 tiles over 2.25 km²** against the old script's 293, at
0.2623 m/pixel and 167.9 m a side. Every roof vertex is inside the grid, and
the script fails rather than writing a manifest if that stops being true.

**Seven of the ten roofs straddle more than one tile, up to four**, so
detections must be dissolved across tile edges before any area is meaningful.

### Imagery source

Google Static Maps for the detector only, because the model was trained on it
and running it on Esri would be a domain shift. **Esri stays the source for the
Part 4 tracing and for FR-3**, which needs a recorded acquisition date that
Google does not publish. The report must say which source was used for what.

### Still blocking the census

V02, V03 and V04 — Blocks 1, 5 and 6 — carry a name in the register and no
coordinates. V01 Bharti, V05 Karakoram and V06 Shivalik were found in
`footprints_osm.json` and are in the grid.

---

## 2026-11-16 — FR-4 back-test: the model passes, and raises a question about tilt

`scripts/run_fr4_backtest.py`. Modelled and measured generation are each
normalised to their own annual total and compared month by month, so plant
capacity cancels and the circularity recorded on 2026-09-22 cannot operate.
Measured side: **18 plants live for the whole of 2024, 792 MWh** — the same set
that arbitrated FR-1 in Part 3.

**Result: total absolute deviation 0.101, so 5.0 per cent of annual energy sits
in the wrong month. PASSES** against the 0.20 tolerance.

### The tolerance is ours, not the specification's

The specification says "back-tested against metered output" without
quantifying it. `config.SHAPE_AGREEMENT_TOL = 0.20` allows a tenth of annual
energy to be misallocated across the year (the measure counts the excess and
the matching shortfall, so half of it is the energy misplaced). **This needs
Prof. Bansal's agreement before the final report leans on it**, and it is
recorded here as a choice rather than presented as a standard.

### The model matches the measured year worse than raw horizontal irradiance

    NASA POWER GHI                    0.072
    our model, tilted, after losses   0.101
    PVGIS TMY GHI                     0.109

Tilting the plane and applying the loss stack should have improved the match.
It did not, so something seasonal is modelled wrongly.

**But no single month leaves the noise.** The 18 plants disagree with each
other by ±0.028 on a monthly share, against a largest model deviation of 0.015.
Month by month the model is inside the spread of the real fleet. What makes the
gap worth pursuing is that it runs in blocks — high in Nov, Dec, Jan, low from
March to June — rather than scattering, which is the signature of a seasonal
effect rather than noise.

### The finding: the existing plants show no winter tilt gain

Share of the year falling in Nov–Feb:

| | winter share |
|---|---|
| horizontal irradiance, NASA GHI | 0.236 |
| **the measured plants** | **0.238** |
| our model at 15° tilt | 0.268 |

A south-facing tilt lifts the winter share, because tilt gain is largest when
the sun is lowest; our model duly lifts it to 0.268. **The measured fleet sits
at the horizontal figure.** The tilt gain is absent from 792 MWh of real
generation.

Two readings:

**(a) The existing arrays are mounted flat or nearly flat.** Common on Indian
institutional roofs where wind load and ballast cost dominate. If so, the 15°
design tilt is not corroborated by any campus installation — and the entry of
2026-09-21 has carried "confirm against a real campus installation" against
that value ever since. This is that confirmation, and it points the other way.

**(b) They are tilted and winter losses cancel the gain.** Fog, soiling and
inter-row shading all bite hardest in winter. Possible, but the cancellation
would have to be near-exact.

**Settle it by looking.** Panel foreshortening and shadow length in the
satellite imagery give the real tilt directly, and the census of Step 2b is
going to that imagery anyway. Measure the tilt while there.

**If (a) holds, the headline changes.** Flat modules need no inter-row spacing,
so the ground coverage ratio rises from 0.707 toward 1.0 — more kilowatts on
the same roof at a lower yield per kilowatt. That trade-off deserves a number
rather than an inherited assumption, and it would move the 2,220.6 kWp figure.

### The winter bias, and why it does not threaten the annual total

Three candidates, in the order worth testing:

1. **Shading is still unity.** Shadows are longest in December, so the months
   the model overstates are exactly the months Part 6 will cut. Most likely,
   and it is already the next step.
2. **Soiling is a flat 3 per cent all year.** Delhi's winter brings fog, dust
   and no rain to wash the modules.
3. **The beam fraction may be overstated in winter haze.** DIRINT and Erbs
   agreed to within 0.1 per cent on the annual total, but that test does not
   bind seasonally.

All three move energy between months rather than changing the total, so the
annual figure of 3,281 MWh is not in question. **Re-run this back-test after
Part 6**; if the winter gap does not close, seasonal soiling is next.

### Still outstanding

Step 2b, the independent capacity from imagery, needs the detector weights and
is not run. Until it is, the existing fleet's capacity remains a single
estimate from a single method.

The comparison is also not like-for-like on year: measured is 2024, modelled is
the 2014–2023 mean, because the NASA series ends in 2023. Interannual spread is
2.5 per cent, so this is small, but fetching 2024 would remove the caveat
entirely.

---

## 2026-11-16 — Part 6 / FR-3: the shade comes from the roof, not the neighbours

`scripts/run_fr3_shading.py`. **Campus mean annual shading loss 3.6 per cent**,
ranging from 0.5 per cent on B09 to 9.6 per cent on B04, worst in December for
most roofs.

### UMEP is not used, and why

The workflow named the UMEP plugin. It runs inside the QGIS GUI, its output
cannot be regenerated from a script, and it cannot be unit-tested — all three
against this project's standing rule that every number regenerates from raw
data through a named script. The model here is written in Python instead and
is covered by 22 tests, several checking it against derivations done by hand.

The method is a **horizon profile** per sample point: the highest obstruction
in each degree of azimuth, built once from the geometry. A point is then sunlit
whenever the sun stands above its horizon in the sun's own direction, which
turns a year of ray tracing into a year of array lookups. Diffuse light is
scaled by the sky view factor, cos² of the horizon elevation averaged over
azimuth. The approximation is that buildings are flat-topped prisms on flat
ground, which the PVGIS horizon profile supports.

### The finding: neighbouring buildings shade these roofs by 0.03 per cent

Attribution, campus mean annual loss, each caster run on its own:

| source | loss |
|---|---|
| neighbouring buildings | **0.03%** |
| the roof's own parapet | 0.54% |
| objects on the roof | **3.09%** |
| all three | 3.62% |

Shading on these roofs is almost entirely **the clutter standing on them** —
the water tanks, stair rooms and plant digitised in Part 4 — not the
surrounding campus. The reason is height: the ten candidates stand 7 to 24.5 m
and the campus around them is mostly lower, and a neighbour shorter than a roof
cannot shade it at all.

This inverts the premise the part was planned on. It also means the two roofs
with the most clutter, B03 and B04, carry nearly ten times the shading loss of
the clearest, and that the obstruction survey from Part 4 is doing more work
for FR-3 than the footprint data is.

### The assumption that worried us does not bind

**432 of 454 neighbours carry no height in OpenStreetMap** — only 1 has a
height tag and 21 have storey counts — so their height is assumed. Sweeping
that assumption:

| assumed neighbour height | campus mean annual loss |
|---|---|
| 7.0 m | 3.62% |
| 10.5 m (used) | 3.62% |
| 14.0 m | 3.63% |
| 17.5 m | 4.04% |
| 21.0 m | 4.58% |

Even putting every unknown neighbour at six storeys moves the answer by one
percentage point. **The result is robust to the weakest input in it**, which is
worth more than a tighter number resting on a guess.

### Two bugs found and fixed, both of which understated the shadow

**Holes in the horizon.** An outline is reduced to points, and if consecutive
points land more than one azimuth bin apart the horizon acquires gaps — bins
reading open sky in the middle of a solid wall, through which the sun shines.
Nothing in the output looks wrong; the shading loss simply comes out too small.
The sample spacing now scales with distance, since the azimuth step between
two points `s` apart at range `r` is `s/r`. Pinned by
`test_a_wall_leaves_no_holes_in_the_horizon`.

**Distance measured to corners, not edges.** The sampling density was chosen
from the distance between a caster's *vertices* and the roof, so a long wall
running close past the roof was judged far away by its distant corners and
sampled too coarsely — putting the holes back exactly where the wall was
closest. Now measured to the edges.

Together these two raised the campus mean from 0.2 per cent to 3.6 per cent.
A model that silently reports almost no shadow is the failure mode to watch
for here.

### Inter-row shading is deliberately not counted

The array is spaced by the ground coverage ratio derived in Part 4 precisely so
that rows do not shade each other in the design window. Counting it again here
would penalise the same geometry twice.

### FR-3 acceptance cannot be evaluated

The criterion compares a modelled shadow against one measured in **dated**
imagery, and the acquisition date of the Esri scenes used in Part 4 was never
recorded. Sun position depends on the date, so there is nothing to compare
against. `acceptance.fr3_shadow_length` is implemented and tested and needs one
dated image and one measured shadow to run. **Capture the date next time the
QGIS project is open** — this is now blocking a criterion, not just a nicety.

### Does it explain the winter bias?

Partly, on the face of it. Mean shading runs about 5 per cent in December
against 2.8 per cent in May, so applying it will pull winter output down
relative to summer — the direction the back-test asked for. Whether it closes
the whole +0.029 winter gap is answered by re-running FR-4 with these factors
and then the back-test, which is the next step and not yet done.

### Still assumed

Parapet 1.0 m and the obstruction heights by type (water tank and stair room
3.0 m, lift room 4.0 m, existing panels 1.5 m, unidentified 2.5 m). Since
objects on the roof now account for 85 per cent of the modelled loss, **these
heights are the most load-bearing assumptions in FR-3** and deserve a tape
measure on the next site visit. Tree canopy is still not modelled; the overhang
deliberately excluded from the Part 4 obstruction layer belongs here and has
not yet been added.

---

## 2026-11-16 — Part 7 pass 2, and the tilt assumption finally tested

FR-4 re-run with the FR-3 shading factors: the beam scaled hour by hour by the
fraction of each roof that can see the sun, the diffuse by the sky view factor.

**3,281 → 3,179 MWh/yr. Shading costs 102 MWh a year, 3.1 per cent.**

The roofs now differentiate, which they could not in the unshaded pass: specific
yield runs from **1,333 kWh/kWp on B04 to 1,469 on B09**, against a single 1,477
for all ten before. Every roof stays inside the FR-4 band. B03 and B04, the
cluttered hostel roofs, lose nearly 10 per cent each.

### Shading does not explain the winter bias

The back-test barely moved: shape error **0.101 → 0.097**, winter excess
+0.029 → +0.027. Shading accounts for about a fourteenth of the gap, not the
bulk of it. The first of the three candidates listed on 2026-09-22 is therefore
largely eliminated, which is worth as much as a confirmation would have been.

### Sweeping the tilt identifies the cause

Modelled seasonal shape against the measured fleet, by array tilt:

| tilt | shape error | Jan/Apr | winter share |
|---|---|---|---|
| **measured fleet** | — | **0.429** | **0.238** |
| 0° | **0.082** | 0.489 | **0.242** |
| 5° | 0.084 | 0.511 | 0.251 |
| 10° | 0.092 | 0.532 | 0.260 |
| 15° (ours) | 0.101 | 0.553 | 0.268 |
| 28° | 0.127 | 0.609 | 0.288 |

The match improves monotonically as the tilt falls, and at 0° the modelled
winter share lands on the measured figure. **The residual in the back-test is
not a fault in the model: it is that the model describes a 15° array and the
validation fleet appears to be mounted flat.** This is the confirmation the
2026-09-21 entry asked for against a real campus installation, and it
contradicts the assumption.

A residual remains even at 0° — 0.082 against raw GHI's 0.072, and a Jan/Apr
ratio of 0.489 against the measured 0.429 — so some winter over-prediction is
still unexplained. Seasonal soiling is the standing candidate: `config.LOSSES`
carries a flat 3 per cent, and Delhi's winter brings fog and dust with no rain
to wash it off.

### What tilt is worth, with row spacing counted

`scripts/run_tilt_tradeoff.py`. Tilt is not free: tilted rows shade each other
and must be spaced, so the ground coverage ratio falls as tilt rises. Over the
10 candidate roofs' 17,198 m² of net available area:

| tilt | GCR | kWp | kWh/kWp | MWh/yr | **kWh per m² of roof** |
|---|---|---|---|---|---|
| **0°** | **1.000** | **3,143** | 1,382 | **4,343** | **253** |
| 5° | 0.871 | 2,739 | 1,422 | 3,894 | 226 |
| 15° (current) | 0.707 | 2,221 | 1,477 | 3,281 | 191 |
| 28.5° | 0.586 | 1,841 | 1,501 | 2,763 | 161 |

Specific yield rises with tilt, as expected, and is the wrong measure for a
campus: the roof area is fixed, not the module count. **Per square metre of
available roof, flat wins by 32 per cent** — 42 per cent more capacity at 6 per
cent lower yield per kilowatt.

**This is not yet a recommendation to change the design.** Flat modules soil
faster and do not self-clean in rain, which the flat 3 per cent soiling figure
does not capture and Delhi would punish; mounting cost, wind load and drainage
all differ; and the FR-3 obstruction shading was computed for a 15° layout, so
a denser flat array would catch somewhat more of it. What it establishes is
that the 15° figure was never tested, that it costs about a third of the
achievable energy on a fixed roof, and that whoever installed the existing
campus arrays appears to have reached the same conclusion.

**Settle it in the imagery.** Panel foreshortening and shadow length give the
real tilt of an existing array directly, and the Step 2b census is going to
that imagery anyway.

---

## 2026-11-16 — Only one script may own a register column

Found while verifying that a lint tidy-up had changed no behaviour: running
`scripts/run_fr2_usable_area.py` after `scripts/run_fr2_from_gpkg.py` moved the
campus total from **2,220.7 kWp to 2,220.4**, and several roofs by a tenth of a
kilowatt.

Neither is wrong arithmetically. They disagree about their **input**: the gpkg
script derives the area chain from the full-precision digitised geometry, while
the older script re-derives it from the register's own already-rounded columns
and so rounds twice.

The amount is trivial. The property is not: a headline figure that depends on
which script ran last is exactly what the register exists to prevent, and it
would not have been noticed without a byte comparison.

`run_fr2_usable_area.py` now refuses to run once `roofs.gpkg` exists and says
which script owns those columns. The rule it enforces is general: **one
column, one writer.** Worth checking for the same pattern when FR-5 starts
writing, since the feeder work will touch rows the generation step also writes.

---

## 2026-11-16 — "Found clear" and "not looked at" are different facts

`check_roofs.py` applied the 8 per cent obstruction placeholder to any roof
with no obstruction polygons. B07 and B09 have none because they were walked
and found clear — recorded in this log on 2026-09-23 as "inspected and
confirmed" — so the placeholder was deducting obstructions that are not there.

The cost: **B07 read 235.3 kWp instead of 260.0 and B09 56.2 instead of 62.3**,
and the script's campus total came out 2,189.7 kWp against the register's
2,220.7. Two files disagreed about the headline figure, and the reason was that
one of them could not tell an empty survey from an absent one.

The fault was not in the arithmetic. **The distinction existed only in prose in
this log**, where no script could reach it. `roofs.gpkg` now carries
`obstructions_surveyed` per roof, the flag is propagated into the register by
the script that owns those columns, and `check_roofs.py` reports three states
rather than two:

    measured      obstructions digitised on this roof
    none found    surveyed and clear - a real zero
    PLACEHOLDER   not yet surveyed, so the capacity is provisional

The totals now agree. Pinned by three tests, including one that fails if the
register and the layer ever disagree about which roofs were surveyed.

**The general rule, which has now bitten twice in one day**: a fact that
changes a number has to live in the data, not in a sentence. The same applies
to the other standing item — `fid 19 on B06`, which `check_roofs` still reports
as a failure every run although this log accepted it on 2026-09-23 as drawn
intentionally. A check that flags an accepted finding forever teaches people to
ignore it, so that acceptance belongs in the obstruction layer too.

---

## 2026-11-16 — An accepted finding belongs in the data too

`check_roofs.py` reported `fid 19 says B06 but only 6% of it is on that roof`
as a failure on every run, although this log accepted it on 2026-09-23 as drawn
intentionally. Same fault as the obstruction placeholder, one layer down: the
decision existed in prose, so the script could not know it had been taken.

`obstructions.gpkg` now carries `overlap_reviewed` per polygon. fid 19 is
marked `yes` with the reason in its `notes` field — only 6 per cent on B06,
drawn as intended, costs that roof about 130 kWp, revisit if B06 reads low.

The check now reports three outcomes rather than two: a low overlap that has
not been reviewed is still a **FAIL**, one that has been reviewed prints as a
**note** and stays visible, and everything else is ok. **check_roofs exits 0 on
the committed layers for the first time.**

A test asserts that any polygon marked reviewed also records a reason, because
an unexplained `yes` in a column is how a real defect gets waved through six
months later. Another runs the script itself and asserts both its exit code and
its output, so a gate that silently became a no-op would fail rather than pass.

### Why this mattered more than the kilowatts

A check that reports a known, accepted finding every time teaches the person
running it to skim past the output. That is how the next real defect gets
missed — and this project has already had four that were invisible on screen
and caught only by a check: a building in Ohio, obstructions assigned to the
wrong block, holes in a shadow horizon, and a meter series read in the wrong
time standard. The value of the suite depends on its output being worth
reading, so "no problems found" has to mean it.

Both GeoPackage edits needed the same workaround: `rtree_*_update4` and
`update5` fire on **any** column change and call `ST_IsEmpty`, which plain
sqlite3 does not provide. Each was dropped, the write made, and the trigger
restored verbatim from `sqlite_master`, with `PRAGMA integrity_check`, the
feature count and the trigger count checked afterwards. Anything editing these
layers outside QGIS must do the same.

---

## 2026-11-17 — The solar alarm, and a seventh dead plant nobody had counted

`scripts/run_alarm.py`, `src/btp_solar/alarm.py`. The October pitch promised a
monitor the campus "could start using tomorrow". It now exists.

As of the end of the record, April 2026: **6 stopped, 1 collapsed, 3
underperforming, 20 generating.**

### The rule, and why it needs no capacity

Energy divided by capacity cannot be used, because capacity is itself
back-calculated from the same generation (2026-09-22) — the test would compare
a plant against itself. Instead each plant's **share of the fleet's output** is
compared against its own baseline. Weather cancels, because a dull month pulls
everyone down together, and capacity never appears. A test asserts the verdict
is unchanged when `estimated_kwp` is unavailable.

### Director's Lodge: dead since July 2024, and invisible to every earlier check

It generated 929–1,970 kWh a month until June 2024. From July 2024 it has
produced **8 to 10 kWh a month, every month, for nineteen months.**

The outage report never saw it, because `months_idle` counts months of exactly
zero and this register keeps inching forward. It is not an outage by that
definition and it is not merely underperforming either: it is at **0.9 per cent
of its baseline**. A fifth dead plant, hiding behind a creeping meter.

That needed two changes:

**A `collapsed` state**, high severity, for output below 5 per cent of baseline
sustained past the outage window. Ranking it as "medium" would have buried a
dead plant below live ones in a list sorted by severity.

**The baseline is the opening twelve months, not the all-time median.** This is
the subtler fault and it is worth recording plainly. A plant that fails early
spends most of the record dead, so its median *is* the dead level — measured
against that, Director's Lodge first came out as a mild "41 per cent of usual"
case. It was measuring itself against its own corpse. Pinned by
`test_the_baseline_is_the_opening_window_not_the_all_time_median`.

### Hindsight, computed rather than claimed

Running the alarm at each past month, using only what was known by then:

| would have fired | plant | months before the end of the record |
|---|---|---|
| 2024-07 | Block No. 5 (Near V-WS-104-107) | 21 |
| 2024-08 | Director's Lodge | 20 |
| 2024-09 | Block No. 6 (Near VI-110) | 19 |
| 2024-10 | SIT Building | 18 |
| 2024-11 | Main / Amaltas Guest House | 17 |

Amaltas alone is about 98 MWh and ₹8 lakh at the provisional tariff. A test
asserts the back-test does not peek at months that had not happened yet,
because the claim is only worth making if it was decided on what was known at
the time.

### Restraint before sensitivity

Six of the thirteen tests check that the alarm stays **quiet**: a monsoon month
that pulls the whole fleet down is weather, one poor month is not a trend, a
new plant has no baseline yet, and multiplying every reading by 37 changes
nothing. A monitor that cries wolf gets ignored, and then the next dead plant
goes unnoticed for two years exactly as before.

### What it does not distinguish

A blank month means "nothing recorded", which is a dead plant *or* an unread
meter. The 2025 band across the hostels is the known missing meter columns, not
an outage, and the dashboard caption says so. Telling those two apart needs the
Estate Office, since they are the same in the workbook and need different
people to fix.

### Addendum, same day — the dashboard, and a failure that was hidden

Running `make alarm` printed `Figure skipped: 'collapsed' is not in list`. The
figure sorted plants with a hardcoded list of statuses, and adding `collapsed`
broke it. Two things made that worse than the one-line fault it was:

**The guard swallowed it.** `_figure` is wrapped in a try/except so a figure
that will not draw cannot kill a report that has already written its data.
That is still right, but it means a broken figure degrades quietly.

**It was hidden by a redirect.** After a later edit the script was re-run as
`>/dev/null 2>&1` to check it exited cleanly. It did — with the figure broken.
Checking an exit code is not checking the output.

The fix is structural: the shades and the ordering now derive from
`alarm.SEVERITY`, so a new status cannot break the picture, and a test draws a
fleet containing every status.

**And the chart was rewritten while fixing it.** It had shaded each row by the
plant's status *today*, which showed Director's Lodge as dead across the whole
record when it ran normally for its first six months. Each month is now shaded
against that plant's own opening baseline, using the same thresholds the alarm
judges by, so the picture cannot drift from the verdict. The month a plant
falls over is now visible, which is the entire point of putting it on a page.

---

## 2026-11-17 — FR-5 proceeds without the Estate Office data

Decision by the project team: **the feeder study goes ahead on the
specification's own mitigation rather than waiting for D16, D17 and D18.**

| | | |
|---|---|---|
| D16 | electricity bills, per building | not available |
| D17 | campus single line diagram | not available |
| D18 | transformer schedule | not available |

None can be derived, fetched or estimated from anything this project can
reach. They have been the only true blockers since the plan was written on
2026-09-21.

### What this costs, precisely

**FR-5's acceptance criterion cannot be evaluated.** The criterion is that the
modelled base case reproduces billed consumption within 15 per cent, and there
are no bills to compare against. `acceptance.fr5_base_case_calibration` stays
implemented and tested; it will not be run, and the report must say so in those
words rather than leaving a reader to infer it.

Nothing else is affected. The 2,220.7 kWp, the 3,179 MWh, FR-1 through FR-4,
the alarm and the economics all stand.

### What is built instead

A representative 11 kV feeder in OpenDSS, with every input declared:

- **transformer ratings** assumed, unless rating plates are photographed on
  site, which would make them real
- **which buildings sit on the feeder** assumed from proximity on the campus
  map, since this is not visible from imagery
- **load profiles** synthesised from building category and floor area, both of
  which the register already holds for all ten candidates
- **generation** from `generation_results.csv`, which is modelled and
  back-tested, so it is the one well-founded input in the study

`fr5_feeder.FeederCase` carries a `synthetic` flag written for exactly this
case, so the output cannot be mistaken for a calibrated result.

### The method this forces, which is better than it sounds

With nothing to calibrate against, a single set of numbers would be a guess
presented as a finding. The study is therefore built as a **sensitivity
analysis**: run the feeder across the plausible range of each assumption and
report which conclusions survive all of them and which depend on a particular
guess.

"Reverse power flow occurs on a summer Sunday under every assumption we tried"
is a defensible claim with no bills at all. "Voltage reaches 1.04 pu" is not.
The report should carry only the first kind, and say that is why.

### Still worth asking in writing

Proceeding without the data does not make the request pointless. A blocker that
was escalated in writing and then mitigated per the specification reads as a
managed risk; the same gap undocumented reads as unfinished work. One email,
whatever the reply.

## 2026-11-17 — The training notebook no longer trusts the runtime's memory

A detector training run completed on a Colab T4 and produced its scores and its
prediction figures. The runtime was then recycled before the save cell ran, and
the cell failed with `NameError: name 'train_set' is not defined`. It was asking
memory for facts about a run the machine had already forgotten, and `/content`
went with it.

Two changes, both the same idea. The training cell now writes the run to
`/content/train_state.json` and pulls `panel_detector.pt` to the laptop the
moment the last epoch ends, rather than waiting for a later cell. The save cell
reads that file instead of reading variables, so it survives a restart; if
`test_iou` is missing it says to re-run the scoring cell, which reloads the
saved weights and takes under a minute, instead of implying the whole hour must
be repeated.

The register rule — a fact that changes a number lives in data, not in prose —
turns out to apply to memory as well as to prose. An hour of GPU should not
depend on a browser tab staying open.

## 2026-11-17 — The existing arrays are tilted, and ballasted, and possibly packed tight

Photographed on campus by TK. Three things are visible and one is a question.

**The arrays are tilted, not flat.** The model's 15 degree assumption is
therefore not contradicted by practice, and the flat-mounting comparison in
`run_tilt_tradeoff.py` changes character: it is no longer "the model may have
the wrong tilt" but "the campus has chosen tilt, and here is what that choice
costs in capacity and yield". That is a recommendation with an installed
counterfactual behind it, which is the stronger of the two readings.

**They are ballasted, not bolted.** Frames sit on concrete blocks with no
visible roof penetration. That matters for the feasibility argument: no
waterproofing is broken, which removes the usual objection to loading an
existing roof.

**At least one building uses elevated canopy frames** that clear the roof
clutter entirely, standing well above the parapet and the pipework. The project
models only low-mounted arrays and deducts obstructed area. A canopy recovers
that area at a higher structural cost. It is a third design option and it is
currently unmodelled.

**Row spacing looks tighter than the model assumes, and that is worth
measuring.** The ground coverage ratio in `config.py` is derived from the
winter design sun, giving 0.707 at 15 degrees. In the photographs the gap
between rows reads as smaller than that. If the installed spacing is tighter,
the fleet carries more capacity per square metre than the model allows and the
back rows self-shade in winter, which is the right shape to explain the
residual winter bias in the back-test. A photograph cannot settle it. Two
measurements can: the height of a frame's rear leg against the panel's long
edge gives the tilt, and the distance from one row's front edge to the next
gives the pitch. Until those exist this stays a hypothesis and the report
should call it one.

## 2026-11-17 — The grid emission factor, and why the combined margin

CEA's CO2 Baseline Database Version 22.0 (August 2026) gives four figures for
the Indian grid in FY 2025-26: weighted average 0.675, operating margin 0.963,
build margin 0.446, combined margin 0.705 tCO2/MWh.

The project uses **0.705**, the combined margin. ACM0002 prescribes it for a
project that displaces grid electricity, which is what a rooftop array does.
The weighted average answers a different question - the mean intensity of the
grid as it stands - and using it here would understate the result by about 4%
while appearing more conservative. Picking a number because it looks cautious,
rather than because the method calls for it, is not conservatism.

Campus potential after shading, 3,179 MWh/yr, therefore avoids about
**2,241 tCO2 a year**.

Both CEA files are in `data/` and stay untracked: they are a reproducible
download from a public source, which is the rule the rest of `data/` follows.

### The two sources that could not be downloaded

MNRE's benchmark cost was the wrong instrument. The PM-Surya Ghar guidelines
fix it at Rs 50,000/kW for the first 2 kW and Rs 45,000 for each additional kW,
and the scheme covers residential consumers and housing societies. There is no
institutional benchmark above 100 kW in it. Applying a household rate to a
2,220 kWp campus would inflate capital cost substantially.

DERC publishes no current retail tariff schedule. Its orders page carries
true-up orders for FY 2021-22 and 2022-23; the base slabs carry forward and the
real cost moves through a monthly PPAC surcharge. Third-party aggregators
quote between Rs 6.00 and Rs 8.50 per unit for non-domestic supply and
contradict each other on PPAC.

Both numbers are therefore requests to the Estate Office rather than downloads:
one recent campus electricity bill gives the tariff actually paid, and the cost
of any recent campus installation gives a capital cost from the same buyer, the
same city and the same year. Those beat any published benchmark, and if neither
arrives the rupee figures are labelled as estimates rather than quietly sourced
from a scheme that does not apply.

## 2026-11-17 — What the photographs can and cannot settle about row spacing

Roof access is not permitted, so the row pitch had to come from three handheld
photographs. Here is how far that goes, and where it stops.

**Settled.** The modules are polycrystalline, mounted landscape, and the cell
grid reads as 60-cell, so roughly 1.65 m by 0.99 m. The frames are ballasted on
concrete blocks with no roof penetration. The arrays are tilted. At least one
building uses elevated canopy frames instead, standing clear of the roof
clutter.

**Bounded, not measured.** In the near-overhead photograph the distance from
one row's leading edge to the next reads as 1.4 to 1.6 times the panel's
apparent up-slope extent. With tilt somewhere between 10 and 20 degrees that
gives a ground coverage ratio between about 0.64 and 0.74:

| pitch / projection | 10 deg | 15 deg | 20 deg |
|---|---|---|---|
| 1.40 | 0.725 | 0.739 | 0.760 |
| 1.50 | 0.677 | 0.690 | 0.709 |
| 1.60 | 0.635 | 0.647 | 0.665 |

The project assumes 0.707, which sits inside that band rather than at its edge.

**So the self-shading hypothesis is not supported.** The suggestion that the
installed rows are packed tighter than the design spacing, and therefore
self-shade in winter, came from an eyeball impression of the photographs. A
measured impression of the same photographs puts the installed spacing at
roughly what the model already assumes. The winter bias in the back-test
remains unexplained, and seasonal soiling remains the leading candidate.

**Why no single number is quoted.** Three handheld oblique photographs, no
camera calibration, and no object of known length in frame. Readings taken from
different parts of the same image disagree by more than the quantity being
measured: the two buildings photographed do not obviously share a spacing, and
attempts to recover tilt from the apparent aspect ratio of a module returned
values that are physically impossible, which is the tell that perspective is
doing more work than the measurement. Quoting 0.69 from this would be
false precision.

**What would settle it, without going on a roof.** The arrays are visible from
above in the imagery already loaded in QGIS. Measuring the span of ten rows in
one line and dividing by ten reduces the error by a factor of ten and removes
perspective entirely. That is a five-minute job on screen and it is the right
way to close this.

Until then the band stands, and it is worth about plus or minus 10% on campus
capacity - material, but not enough to move the headline.

## 2026-11-17 — The Esri imagery was captured on 23 October 2025

Queried from Esri's own metadata service at the campus point rather than read
off a screen. Recorded in `data/imagery_provenance.json`, because a fact that
an acceptance criterion depends on belongs in data.

| | |
|---|---|
| Acquisition date | **2025-10-23** |
| Sensor | WorldView-2 |
| Resolution | 0.5 m |
| Horizontal accuracy | 8.47 m |
| Product | Vivid Advanced, Vantor |
| Block | DYNAMIC_ESRI_New_Delhi_25Q4 |

**It is the same scene the roofs were traced against.** Esri replaces World
Imagery as new captures land, so today's date is not automatically the date
that was on screen in September 2026. Checked through the Wayback metadata
layers: the release live on 22 and 23 September 2026 was Wayback 2026-08-05,
and at this point it served the same block and the same capture date. So the
tracing, the obstructions and the shading model all rest on one scene.

**The 8.47 m is absolute georeferencing, not shape error.** It says the scene
may sit up to that far from its true position on the earth. It does not mean a
roof's outline is wrong by 8 m. Area, shape and the relative positions of
buildings within one block are consistent, and those are what this project
measures, so the figure does not propagate into roof area or into the shading
geometry. It would matter for aligning against an independent survey.

**The imagery is eleven months older than the foot survey.** Captured October
2025, surveyed September 2026. The survey is the newer evidence, which is the
right way round, and it explains the six buildings found carrying panels that
the open data had not recorded. Anything installed after October 2025 is
invisible to the imagery, and the PV census will inherit that limit.

### FR-3 is no longer blocked, and the missing time is recoverable

Esri records the date but not the time, and `expected_shadow_length` needs
both. The time does not have to be assumed. A shadow's **bearing** gives the
solar azimuth, which gives the hour angle for a known date and latitude; the
shadow's **length** then tests the elevation model. Bearing and length are
independent measurements of the same shadow, so fixing the time from one leaves
the other free to do the validating. No circularity.

For orientation, on day 296 the declination is -12.28 degrees, and a 1.0 m
parapet at this latitude casts:

| IST | sun elevation | shadow |
|---|---|---|
| 10:00 | 36.8 deg | 1.338 m |
| 10:30 | 41.1 deg | 1.146 m |
| 11:00 | 44.7 deg | 1.011 m |
| 11:30 | 47.3 deg | 0.922 m |

WorldView-2 is sun-synchronous with a descending node near 10:30 local, so the
capture was probably mid-morning - an expectation, not a record, and the
bearing method does not depend on it.

## 2026-11-17 — The shadow method is sound; this imagery cannot carry it

Roof access is not permitted, so the six assumed values in
`OBSTRUCTION_HEIGHTS_M` were to be measured from the shadows the objects cast
in the Esri scene. The method is implemented in `src/btp_solar/shadows.py` and
tested, the tile fetching in `src/btp_solar/basemap.py`. It does not work here,
and the reason is worth recording because it is a property of the product
rather than of the idea.

**Esri World Imagery over this campus has no usable shadows.** The scene is
Maxar "Vivid Advanced", a curated seamless basemap rather than a single raw
pass, and it is radiometrically balanced for even appearance. On 23 October at
28.5 N the sun cannot climb past 49.2 degrees, so a 24.5 m building *must* lay
down 26 m of shadow - a hundred pixels at 0.26 m. There is none. Nothing in the
scene casts anything measurable, and no amount of better estimation recovers a
signal that was processed out.

### What the attempt established on the way

Three findings survive, all of them corrections to my own first guesses.

**Sampling at one radius is wrong for a polygon that is not round.** The first
pass searched for the darkest direction at a single distance from the
centroid, which on an elongated plant-room block starts clear of the object
across the short axis and still inside it along the long one. `extent_along`
now uses the outline's support function in each direction.

**Off the roof is darker than any shadow.** The darkest direction from an
obstruction near a parapet is simply *off the roof*, into tree canopy. That
beat the real shadow on six obstructions out of twenty-one. Samples are now
confined to the roof deck.

**The sun's own geometry is a constraint, and using it is not cheating.** With
the declination south of the latitude the sun never crosses to the north, so
every shadow in the scene points northward. Unconstrained, the bearings gave a
circular concentration of 0.21, which is noise. Constrained, 0.71 - but a
consensus among features that are not shadows is still not a shadow, and the
subsequent length measurements returned zero almost everywhere, which is how
the earlier agreement was exposed as spurious. **That 0.71 is not a result and
must not be quoted as one.**

A test of genuinely scattered bearings then found a real defect:
`solve_scene_sun` checked its confidence *after* solving the geometry, and
scattered bearings average to an azimuth no sun occupies, so "these shadows do
not agree" surfaced as a crash. Confidence is now checked first.

### What replaces the measurement

A sensitivity analysis, which is the honest answer to a parameter that cannot
be measured - `make sensitivity`. The heights are scaled across the range a
surveyor would accept without going up to look, from water tanks of 1.5 m to
6.0 m, and the campus answer is reported at each:

| scale | water tank | campus shading loss | campus energy |
|---|---|---|---|
| x0.50 | 1.5 m | 1.29% | 3,139 MWh |
| x0.75 | 2.2 m | 2.17% | 3,112 MWh |
| **x1.00** | **3.0 m** | **3.05%** | **3,085 MWh** |
| x1.25 | 3.8 m | 3.87% | 3,059 MWh |
| x1.50 | 4.5 m | 4.68% | 3,035 MWh |
| x2.00 | 6.0 m | 6.08% | 2,991 MWh |

**The headline is robust and the ranking is not.** Across a fourfold range of
heights the campus energy moves by 148 MWh on about 3,100 - under 5%, and
inside the uncertainty the generation model already carries. So the untapped
potential does not depend on the guess. But the worst-affected roof runs from
3.5% to 19.0% of its own output, and the order in which roofs should be built
is sorted on exactly that. The report should state the headline plainly and
attach this band to the ranked table, not the other way round.

### What `basemap.py` is still good for

The tile service is free, needs no key, and serves the same scene the roofs
were traced against at 0.26 m per pixel - the resolution the census was
planned around. That removes the Google Maps Static API key from the census
entirely. The shadow attempt failed; the fetching it was built on did not.

## 2026-11-17 — Dust explains the winter leg of the residual, and not the total

The back-test's residual has a definite sign: the model puts more energy into
November, December and January than the fleet delivers. Shading moved the shape
error from 0.101 to 0.097 and no further. Row spacing turned out not to be the
cause. Soiling was the remaining candidate, and NASA POWER's daily rainfall for
this point says why it would be seasonal here rather than a flat derate:

| | mm/yr | days past a 6 mm wash |
|---|---|---|
| Jul | 238 | 11.5 |
| Aug | 160 | 8.6 |
| Sep | 118 | 5.8 |
| **Nov** | **3** | **0.1** |
| Dec | 8 | 0.4 |
| Feb | 15 | 0.6 |

November averages one wet day per decade. Dust accumulates from October to the
pre-monsoon showers with essentially nothing to remove it, over exactly the
months the model is too optimistic.

### The rate is swept, never fitted

Tuning a soiling rate until the back-test passes, then reporting that the
back-test passes, would be worthless: the rate absorbs whatever else is wrong.
So `scripts/run_soiling.py` sweeps the rate across the band published for
northern India and prints the whole curve. The question is falsifiable - does
an ordinary amount of dust account for the residual, or an absurd amount?

| %/dry day | annual loss | shape error | winter error |
|---|---|---|---|
| none | - | 0.0972 | 0.0327 |
| 0.10 | 2.1% | 0.0963 | 0.0288 |
| 0.30 | 5.8% | 0.0931 | 0.0200 |
| 0.50 | 8.1% | **0.0914** | 0.0139 |
| 0.80 | 10.1% | 0.0958 | **0.0116** |

### Reading it honestly

**The November-December-January over-prediction is 0.0327, a third of the total
0.0972.** At 0.30%/day - an unremarkable rate - soiling removes 39% of it; at
0.50%/day, 57%. So dust does account for most of the thing it was accused of.

**The total shape error barely moves, and that is arithmetic rather than
failure.** Both series are normalised, so energy taken out of December has to
reappear somewhere, and it lands in August and September where the model was
already too high. A real fix to winter therefore shows up as a 0.006
improvement in the total. The total is simply the wrong instrument for this
question, which is why the winter sum is now reported beside it.

**What is left is not dust.** After soiling the residual is a spring and
monsoon error of the opposite sign - the model runs low in March and June, high
in August. Dust cannot do that. That is the next thing to chase, and the report
should name it as open rather than imply the residual has been explained away.

### A costed operational finding

Because the dust is now quantified, the value of washing it off can be priced
rather than asserted. At 0.50%/day, against doing nothing:

| regime | recovers | energy | at Rs 8/kWh |
|---|---|---|---|
| wash once, February | 0.52% | 17 MWh/yr | Rs 1.3 lakh/yr |
| wash twice, December and February | 1.76% | 56 MWh/yr | Rs 4.5 lakh/yr |
| wash three times over the dry season | 2.45% | 78 MWh/yr | Rs 6.2 lakh/yr |

The tariff is still provisional, so the rupees are indicative and the energy is
not. This is the first recommendation the project can make about the plants the
Institute *already owns*, rather than about ones it might build.

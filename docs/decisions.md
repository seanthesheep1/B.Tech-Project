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

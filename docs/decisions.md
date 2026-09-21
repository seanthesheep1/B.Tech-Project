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

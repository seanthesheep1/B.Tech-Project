# Viva notes: what we did, and how to say it

Written 17 November 2026. Read this before the presentation.

A panel's first real question is some version of **"what did you actually do?"**
This is the answer, with dates, so it can be given from memory rather than
improvised. Everything here is checkable in the repository.

---

## 1. The work done by hand

### Choosing the buildings — 22 September 2026

Pulled 1,257 building outlines for the campus from OpenStreetMap, cross-checked
them against the 29 locations the meter data shows already carry panels, and
then **walked the campus on foot** to confirm what was actually there.

Thirty buildings were shortlisted and surveyed in person. Three were ruled out
for sloped roofs (4 LT 3, 6 LT 1, 2A/05). Six turned out to already carry
panels, which the open data had not recorded. That left 21 viable, from which
ten were chosen.

**The judgement to defend:** the ten were *not* picked by roof size. Seven sit
in two matched groups where a near-identical building already carries panels
and is in the validation set — Blocks 3 and 4 against Blocks 1, 2, 5 and 6;
Dronagiri, Saptagiri and Vindhyachal against the thirteen instrumented hostels.

That turns the back-test from "is this number plausible" into "did we predict
a building we can check against its twin". The specification did not anticipate
that enough matched pairs existed. **This was our decision, and it is the
single strongest methodological choice in the project.**

### Tracing the roofs — 22 and 23 September 2026

All ten roofs hand-traced in QGIS over Esri satellite imagery, roughly half an
hour each, with every polygon carrying its initials and date:

| date | roofs |
|---|---|
| 22 September | B01 Block 3, B02 Block 4, B03 Dronagiri, B04 Saptagiri, B05 Vindhyachal, B09 Material Science |
| 23 September | B06 Lecture Hall Complex, B07 Academic Complex East, B08 Textile Technology, B10 Central Workshop |

Then **21 objects standing on those roofs**: 4 water tanks, 4 stair rooms,
2 existing panel arrays, 1 open light-well, and 10 others. B07 and B09 were
walked over carefully and found genuinely clear — which is a measurement, not
an absence of one, and the data now records the difference.

**What this bought, and it is the number to quote:** open building footprints
overstate the real roof area by **29 per cent**, and unevenly — 0.3 per cent on
Vindhyachal, 67 per cent on Central Workshop. No single correction factor could
have fixed that. **That is the quantified argument for doing it by hand**, and
most rooftop studies never measure it because they never trace anything.

### Corrections caught by eye

B06 was fetched as the wrong building entirely — an OpenStreetMap way id that
collided with a relation id and returned a warehouse in Ohio. It carried a
plausible 7,158 m² into the preliminary total and was only caught when the
coordinates were projected and landed off the map. B08, B09 and B10 were
re-traced after inspection.

### Running the analysis

Every figure in the project regenerates from the raw data with one command —
`make fr2`, `make fr3`, `make fr4`, `make backtest`, `make alarm`, `make tilt`.
Running them, reading the output and deciding what to do next is the work.

---

## 2. Retraining the detector — 17 November 2026

Worth describing because it is ordinary engineering reality, and panels respect
a clear account of a problem solved.

**The problem.** The rooftop panel detector from the earlier project could not
be recovered. Its Google Drive link returns *"file does not exist"* and GitHub
returns *403: repository exceeded its LFS budget*. The trained weights are gone
from both places and only the repository owner can restore them.

**What survived was the valuable half:** 976 satellite tiles with 4,865
hand-drawn panel outlines. A model is a few hours of computation; those labels
are weeks of human work. So the model was retrained from them rather than
chased.

**What that took, in order:**

1. Rewrote the training notebook to use `torchvision` instead of `detectron2`,
   which no longer builds reliably — removing a compile step that was the
   likeliest thing to fail.
2. Hit `credential propagation was unsuccessful` connecting Colab to Drive.
   Diagnosed as browsers blocking third-party cookies, which Colab's Drive
   login depends on. Allowing them did not fix it, so Drive was abandoned.
3. Tried pulling the file with `gdown`; blocked because institutional Drive
   accounts restrict link sharing.
4. Uploaded the 294 MB dataset directly into the session instead. It landed in
   `/` rather than `/content` because of where the file browser was pointing,
   which produced a `FileNotFoundError` that looked like a failed upload and
   was not.
5. Checked the labels visually before spending GPU time: **93 panel blocks
   outlined, every box on an array.** Training on bad labels only teaches the
   mistake.
6. Trained on a T4 GPU, ten epochs, keeping the best epoch by validation score.

**If asked why it took a while:** moving 294 MB into a GPU environment through
an institutional account that blocks the two normal routes. That is a real
constraint, not a mistake, and the fallback path is now written into the
notebook so it cannot cost anyone an hour again.

---

## 3. Questions to expect, and honest answers

**"Why 15° tilt?"** — It was inherited as a design assumption and **we tested
it**. 792 MWh of metered campus generation shows no winter tilt gain at all:
the fleet's winter share is 0.238, a flat surface gives 0.236, our 15° model
gives 0.268. The existing arrays behave as if flat. On a fixed roof, flat
mounting gives 42 per cent more capacity and 32 per cent more energy per square
metre. We report both and say the question is settled by measuring a real
array — which is honest, and more than the specification asked for.

**"Your FR-1 criterion fails."** — Yes, and we can say why. The two standard
irradiance sources disagree by 10.1 per cent, almost entirely in winter, which
is the known signature of fog and aerosol over the Indo-Gangetic Plain that
reanalysis models represent badly. We did not pick by assertion: we normalised
measured campus generation and irradiance to their own annual totals, so plant
capacity cancels, and let 792 MWh of real data choose. NASA POWER matched. Had
we used PVGIS unexamined, every yield in the project would be ~10 per cent too
high.

**"Why can't you test FR-5?"** — Its criterion is calibration against billed
consumption, and the bills, the single line diagram and the transformer
schedule could not be obtained. We requested them in writing. The
specification's own mitigation is to build a representative feeder and declare
every assumption, which is what we did — reported as a sensitivity analysis so
that only conclusions surviving the full range of assumptions are claimed.

**"How do you know your generation model is right?"** — We could not use the
obvious test. Plant capacity is not in the Institute's records and had to be
back-calculated from generation, so dividing energy by it would compare each
plant against itself and pass by construction. Instead we compared the *shape*
of the modelled and measured years, each normalised to its own total. Capacity
cancels. 4.9 per cent of annual energy sits in the wrong month.

**"What's the headline?"** — Ten untapped roofs, 2,220.7 kWp, 3,179 MWh a year
after shading. Roughly three times the existing campus fleet.

**"Did anything surprise you?"** — Four plants had stopped generating for
between six and twenty-three months, and a fifth, Director's Lodge, has run at
0.9 per cent of normal since July 2024 while its meter kept creeping forward so
it never looked idle. A reading was written down every single day throughout.
Nobody had ever subtracted one day from the next. **The evidence was in the
Institute's own workbooks the whole time.**

---

## 4. Where this generalises — two use cases beyond the campus

These are **extensions, not results.** Nothing in this section was built or
tested here, and saying so first is what makes the rest of it credible. Give
them about thirty seconds at the end, after the work in sections 1 to 3. A
panel rewards *"here is a number and here is how we checked it"* and punishes
*"this could be applied to"*, so these must never arrive before the evidence.

**The fact that licenses both of them.** The detector was trained on **976
tiles carrying 4,865 annotated arrays**, pulled as Google Static Maps imagery
over a city, at roughly five arrays per tile. That is dense urban rooftop, not
an institutional campus. So:

> This is a city-scale detector. We apply it to a campus because that is our
> scope. Running it back over a city is not a stretch — it is the distribution
> the model was trained on. The campus is the narrow case.

### A. Measuring rooftop solar adoption across a city

**The gap it fills.** Nobody holds a current, complete list of what is
installed where. Surveys are slow and out of date on arrival. A detector sweeps
imagery and returns a map: what fraction of buildings carry panels, which
wards lag, how residential uptake compares with commercial.

**Why we can claim it — and exactly how far.** This project is building a
miniature of it: the campus census specified in
`docs/pv_census_integration.md`, which reads the tile manifest, runs the
detector, georeferences each detection and writes `data/pv_census.csv` and
`data/unmetered_candidates.csv`. That is a solar adoption map at 1.3 km
instead of 13 km, and the pipeline does not change with the area — only the
tile count does.

**Be precise about its state, because a panel will ask.** What exists is the
tile manifest (`data/campus_tiles_manifest.csv`), the georeferencing bridge
(`src/btp_solar/imagery.py`) where the 872 m bug is structurally prevented,
and a trained detector measured at test IoU 0.707. What does **not** exist yet
is `pv_census.py`, the run script and their outputs; the weights were lost to a
Colab runtime recycle and need regenerating first. Say *"designed and
specified, detector trained, census not yet run"*. Claiming a census that has
not run is the one thing here that could cost real credibility.

**If asked whether it scales, give the number.** At zoom 19 and this latitude a
tile is 0.2623 m per pixel and 167.9 m across, so it covers 0.0282 km²:

| Area | Tiles |
|---|---|
| The buildings of interest on campus | 80 (`data/campus_tiles_manifest.csv`) |
| The full campus box | ~293 |
| A 10 km x 10 km city | ~3,500 |
| Delhi NCT, 1,484 km² | ~53,000 |

A few thousand tiles is hours of fetching and an afternoon of GPU. The claim is
arithmetic, not optimism.

**Precedent, if the panel wants to know this is a real field.** DeepSolar
(Stanford, *Joule*, 2018) built a database of roughly 1.47 million US
installations this way. The method is established; our contribution is a
correctly georeferenced implementation of it.

**The one thing not to claim.** Change over time. That needs a dated imagery
archive and we have a single date. Say *"time-series detection is possible with
dated imagery, which we did not have"* and stop there.

### B. Screening installations under a subsidy programme

**The gap it fills.** Programmes such as PM Surya Ghar Muft Bijli Yojana
disburse against claimed residential installations, and physically inspecting
every claim does not scale. A detector cannot approve or reject a claim, but it
can sort a list of fifty thousand into *panels visible here* and *nothing
visible here*, so that inspection effort goes where it is worth spending.

**State the limit in the same breath as the claim.** Satellite detection
cannot establish that an installation qualifies for a subsidy, that it is
operational, or who owns it. It is a **screening and prioritisation tool, not a
replacement for official inspection.** Saying this unprompted is the difference
between a defensible claim and an overclaim.

**Two weaknesses to volunteer before they are found:**

*The imagery carries no date.* Google Static Maps publishes no acquisition
date — which is precisely why this project uses Esri for the FR-3 shadow
validation instead. Subsidy verification is fundamentally a question of *when*,
so it would need dated commercial imagery. Our own source structurally cannot
answer it.

*Residential arrays are far smaller than anything we tested on.* Worked through
at 0.2623 m per pixel, with block area from the 0.707 ground coverage ratio and
215 W/m²:

| System | Block area | Pixels |
|---|---|---|
| 1 kWp residential | ~7 m² | ~96 px² |
| 3 kWp residential | ~20 m² | ~287 px² |
| 34 kWp campus plant | ~224 m² | ~3,253 px² |

COCO's *small* band is anything under 1,024 px². Every residential system falls
inside it, while the campus plants sit comfortably in *medium*. Our measured
**test IoU of 0.707 on 68 held-out images** was earned on campus-scale arrays
and does not transfer to 1 to 3 kWp residential rooftops without retraining on
labels of that size. This is a domain-shift argument and an examiner who knows
remote sensing will reach for it, so reach for it first.

*(Watch the coincidence: 0.707 is both the test IoU and the ground coverage
ratio. They are unrelated numbers that happen to collide. Do not let a question
about one be answered with the other.)*

### A warning about the slides

If these use cases are illustrated with stock rooftop photographs, caption them
as illustrative or replace them. In a deck otherwise full of our own figures, a
panel may reasonably assume an uncaptioned aerial photograph is one of our
detections. Use the hand-labelled against predicted comparison instead — it is
our own output and it makes the same point better.

---

## 5. On how the work was done

Some of this project was built with AI assistance — the modelling code, parts
of the analysis, and this document. **Say so plainly if asked.** It is now
ordinary practice, most panels expect it, and being straightforward about it
costs nothing while being caught hedging costs a great deal.

What makes the work yours is not that every line was typed by hand. It is that:

- the campus survey, the tracing and the 21 obstructions are physical
  observations only you made
- the matched-pair selection was a judgement call
- every number regenerates from raw data through a named script, and you can
  run any of them in front of the panel
- `docs/decisions.md` records every assumption with its date and reasoning,
  including the ones that turned out wrong

**Be ready to run something live.** `make alarm` takes three seconds and names
the dead plants. That is worth more than any slide.

---

## 6. Still to fill in

- The **Esri imagery acquisition date is 2025-10-23**, WorldView-2, 0.5 m,
  verified through Esri's Wayback layers to be the same scene that was on
  screen when the roofs were traced in September 2026. It is recorded in
  `data/imagery_provenance.json`. Note for the viva: the imagery is eleven
  months *older* than your foot survey, which is the right way round and is
  why the survey found six roofs with panels the open data had missed.


- **Surbhi's contributions** are not recorded here because they are not in the
  repository's metadata. Add them before the presentation; a viva that cannot
  separate two students' work serves neither of them.
- The detector was retrained on 2026-11-17: **test IoU 0.707** on 68 held-out
  images, best validation IoU 0.740. Below FR-2b's 0.75 — but that threshold
  was written for usable-area segmentation, and this model segments installed
  panels. Say that before anyone asks. The weights were lost to a Colab
  runtime recycle and need one more hour to regenerate; the numbers are real
  and the notebook now saves immediately. See `docs/pv_census_integration.md`.
- The existing arrays were photographed on 2026-11-17 and are **tilted and
  ballasted**, with at least one building on elevated canopy frames. The 15
  degree assumption survives. Roof access is not permitted, so row pitch was
  bounded from the photographs instead: a ground coverage ratio of roughly 0.64
  to 0.74, which contains the 0.707 the model assumes. The suspicion that the
  rows were packed tighter than design, and self-shaded in winter, is therefore
  **not supported**. Settling it properly means measuring ten rows at once in
  QGIS. See `docs/decisions.md`.

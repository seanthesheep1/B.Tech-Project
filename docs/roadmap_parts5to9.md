# Roadmap: finishing the project

*Rewritten 2026-11-17. The first version was written before Steps 1 to 4
existed and before the tilt and shading findings; it described a plan that was
partly done and partly overtaken, which is the same hazard this project has
fixed three times in the data.*

---

## 1. Where the project stands

| Part | State |
|---|---|
| 1 Building list | closed |
| 2 Existing fleet | closed, and now extended by the alarm |
| 3 Irradiance | closed |
| 4 Digitising and usable area | closed |
| 6 Shading | **closed** |
| 7 Generation and back-test | **closed** |
| 5 Segmentation | data ready, model must be retrained |
| 8 Feeder | blocked |
| 9 Synthesis | needs three public documents |

**Headline: 2,220.7 kWp over ten roofs, 3,179 MWh a year after shading.**
154 tests pass.

### Acceptance

| Ref | Criterion | Status |
|---|---|---|
| FR-1 | Two irradiance sources agree within 5% | **FAILS**, 10.1%, diagnosed and arbitrated against measured generation |
| FR-2a | Usable area derived, not assumed | **PASSES** |
| FR-2b | Segmentation IoU ≥ 0.75 | not reached |
| FR-3 | Shadow within 15% of a measured one | **cannot run** — no dated image |
| FR-4a | Specific yield 1300–1600 | **PASSES**, 1,432 |
| FR-4b | Within 10% of PVGIS | **FAILS**, 19.5%, same root cause as FR-1 |
| FR-4c | Back-tested against metered output | **PASSES**, 0.097 |
| FR-5 | Base case within 15% of billed | blocked |

Two of the three failures are the same fact: the specification assumed two data
sources would agree about Delhi's winter, and they do not, for a physical
reason this project can evidence. That is a finding, not a gap — but it has to
be **put to the panel as a proposed restatement**, not left for them to spot.

---

## 2. What is left, in the order worth doing it

### A. Retrain the panel detector — *waiting on you, then ~1 day*

The original weights are gone: the Drive link is dead and GitHub returns
*403, repository exceeded its LFS budget*. The training data survived.

`notebooks/train_panel_detector.ipynb` is written and its data pipeline, model
construction, a real training step and the IoU scorer have all been run against
the actual images. It uses torchvision rather than detectron2, so there is
nothing to compile. `/Users/tejaskamble/Downloads/panel_training_data.zip`
(294 MB, 976 images) is ready to upload.

**Produces** `panel_detector.pt` plus a card recording what it scored.

### B. The census — *1.5 days, after A*

Fetch the 80 campus tiles already planned in `campus_tiles_manifest.csv`, run
the detector, dissolve detections across tile edges, attribute them to
buildings, and convert area to kilowatts using the Part 4 ground coverage
ratio.

**Answers three open questions at once:** an independent capacity for the
existing fleet with no meter data in it, whether any array is unmetered
(B06 carries two `solar_panel` obstructions on a building chosen for having
none), and **whether the existing arrays are flat** — see §3.

**Needs from you:** a Google Maps Static API key, and coordinates for Blocks 1,
5 and 6, which carry a name in the register and nothing else.

### C. Economics and the ranked table — *1 day*

Needs three public downloads: MNRE benchmark cost, CEA emission factor, DERC
tariff. Produces cost, payback, levelised cost and avoided CO₂ per roof, the
deployment order, and the campus heat map. **This is the step that answers
"so what?"**, and it is cheap once the documents are in hand.

### D. Seasonal soiling — *0.5 days*

The back-test's winter excess survived the shading model: 0.101 to 0.097 only.
`config.LOSSES` carries a flat 3% soiling all year, and Delhi's winter brings
fog and dust with no rain to wash it off. Make soiling monthly and re-run the
back-test.

### E. Segmentation IoU, FR-2b — *0.5 days, after A*

Score the retrained model on campus imagery against hand-traced arrays.
**State plainly what it measures.** The criterion was written for segmenting
usable roof area; this model segments installed panels. Reporting it as FR-2b
without that sentence invites the one question there is no good answer to.

### F. Feeder, FR-5 — *2 days, synthetic by decision*

**Decided 2026-11-17: this runs without D16, D17 and D18.** They are not
coming, and the specification's own mitigation applies.

Build one representative 11 kV feeder in OpenDSS. Transformer ratings assumed
(or real, if rating plates get photographed on site); feeder membership assumed
from proximity on the campus map; load profiles synthesised from the building
category and floor area already in the register; generation from
`generation_results.csv`, which is the one input here that is modelled and
back-tested.

**Built as a sensitivity analysis, not a single answer.** With nothing to
calibrate against, one set of numbers would be a guess dressed as a finding.
Run the plausible range of each assumption and report only what survives all of
them — "reverse power flow occurs on a summer Sunday under every assumption"
rather than "voltage reaches 1.04 pu".

`FeederCase.synthetic` marks the output. **FR-5's criterion will not be run**,
and the report says that in those words.

### G. The Solar Map — *1 day, after C*

One self-contained HTML file. Click a roof: capacity, annual energy, shading
loss, payback, CO₂. Existing plants coloured by alarm status, so "find" and
"protect" appear on one screen.

### H. Final report, deck, defence brief — *2 days*

---

## 3. The open question that could move the headline

**Are the existing campus arrays flat or tilted?**

The project assumes 15°. 792 MWh of metered generation shows **no winter tilt
gain at all** — the fleet's winter share is 0.238 against 0.236 for a
horizontal surface and 0.268 for our model. Sweeping the tilt, the match to
measured improves monotonically as tilt falls to zero.

If they are flat, flat is better on a fixed roof:

| tilt | GCR | kWp | kWh per m² of roof |
|---|---|---|---|
| 0° | 1.000 | 3,143 | **253** |
| 15° (current) | 0.707 | 2,221 | 191 |

**42% more capacity, 32% more energy per square metre.** Specific yield is the
wrong measure here, because the roof area is fixed and the module count is not.

Settled by looking at one roof, or by measuring panel foreshortening in the
census imagery. Until then the 15° figures stand and the alternative is
reported beside them.

---

## 4. Things only you can do

Revised 2026-11-17. Most of this table has emptied, and not because the work
was dropped: Esri's World Imagery tile service turns out to be reachable
without a key, at 0.26 m per pixel, and it serves the very scene the roofs were
traced against. Anything that was waiting on a roof visit or on a paid imagery
key is now a desk job.

| | Unblocks | State |
|---|---|---|
| Ask Prof. Bansal to confirm the 0.20 back-test tolerance, and the FR-1/FR-4 restatement | our criterion, not the specification's | **open - only you** |
| Locate Blocks 1, 5 and 6 (V02/V03/V04 carry no coordinates) | the census cross-check | **open - only you**, low priority while the census is cut |
| Email the Estate Office: D16/D17/D18, plus one campus bill and one installed cost | nothing is blocked; upgrades two estimates to measurements | optional |
| Record the Esri imagery acquisition date | FR-3 | **done 2026-11-17** - 2025-10-23, in `data/imagery_provenance.json` |
| Look at one existing array: flat or tilted? | the tilt argument | **done** - tilted, ballasted, photographed |
| Get a Google Maps Static API key | the census | **not needed** - Esri tiles are free, keyless, and already our scene |
| Download MNRE, CEA and DERC documents | the economics | CEA **done** and in `data/`; MNRE is residential-only; DERC publishes no current schedule |
| Measure obstruction heights on two roofs | FR-3's most load-bearing assumption | **moved to me** - roof access is not permitted, so heights come from shadow lengths on the dated imagery |
| Confirm one floor height | every building height derives from it | **moved to me** - same shadow method |
| Re-check B10 Central Workshop | ~500 kWp of the headline | **moved to me** - re-inspection against imagery is a desk job |

### Why the shadow method replaces the tape measure

`OBSTRUCTION_HEIGHTS_M` is currently six assumed numbers - 3.0 m for a water
tank, 3.0 for a stair room, 4.0 for a lift room, and so on - and roof clutter
is about 85% of the modelled shading loss. So those six numbers carry more of
FR-3 than anything else in the model, and none of them was measured.

With a known acquisition date and a known latitude, an object's height follows
from the length of its shadow. The 21 obstructions already carry coordinates in
`obstructions.gpkg`, the imagery is 0.26 m per pixel, and a 3 m tank on 23
October casts between 3.0 and 4.0 m depending on the hour - ten to fifteen
pixels, which is measurable. The sun's position at capture is fixed from the
shadows' bearing rather than assumed, as recorded in `docs/decisions.md`.

That turns the weakest assumption in FR-3 into a measurement, without anyone
setting foot on a roof.

**Attribution.** The imagery is Esri World Imagery and the report must say so.
The project already streams the same service into QGIS, so fetching a bounded
set of tiles over the ten candidate roofs is the same use by another route, not
a new one.

---

## 5. If everything optional is cut

The unblocked work — soiling, economics once the PDFs arrive, the map, the
report — is about **five days**. That ends with a validated energy model, a
shading analysis, a costed and ranked deployment plan, a working monitor, and
six acceptance criteria each either passed or failed for a stated reason.

Parts B, E and F make it a strong project rather than a complete one.

---
lang: en-GB
---

# Mid-term Review — Defence Brief

**Rooftop Solar Potential Mapping of the IIT Delhi Campus**\
Tejas Suresh Kamble (2023EE10974) · Surbhi Rathore (2023EE11224)\
Supervisor: Prof. Yashasvi Bansal · Department of Electrical Engineering, IIT Delhi

*Companion to the mid-term review report. Everything here is checked against the
repository; the derivations in Part 1 were re-computed from first principles and reproduce
the reported values exactly.*

<div class="pagebreak"></div>

# Part 1 — The six derivations you must be able to do on a whiteboard

If a panelist asks "where does that number come from?", the answer must be a derivation,
not a citation. These are the six.

## 1.1 Ground coverage ratio — the 0.707

**This is the single most likely question in the whole viva**, because it is the number
the specification explicitly demanded be derived rather than assumed, and every capacity
figure rests on it.

**The physical setup.** Modules of slope length `L` are mounted at tilt `β` in rows. Each
row stands `L·sin β` tall and casts a shadow behind it. If rows are packed too close, the
back row sits in the shadow of the one in front.

**The derivation.**

1. A row of slope length `L` at tilt `β` occupies a horizontal depth of `L·cos β`.
2. Its top edge is at height `h = L·sin β`.
3. A point at height `h` casts a ground shadow of length `h / tan α`, where `α` is the
   solar elevation.
4. That shadow runs along the sun's ground azimuth. Only the component **perpendicular to
   the rows** matters, which introduces `cos γ`, where `γ` is the solar azimuth measured
   from the row normal (i.e. from south, for south-facing rows).
5. So the pitch — the row-to-row spacing measured perpendicular to the rows — must satisfy:

```
pitch  ≥  L·cos β  +  L·sin β · cos γ / tan α

pitch / L  =  cos β  +  sin β · cos γ / tan α

GCR = module area / land area = L / pitch
```

**The numbers**, at tilt β = 15°, design sun α = 22.32°, γ = 44.53°:

```
pitch/L = cos 15° + sin 15° × cos 44.53° / tan 22.32°
        = 0.96593 + 0.25882 × 0.71274 / 0.41046
        = 0.96593 + 0.44939
        = 1.41532

GCR     = 1 / 1.41532 = 0.7066
```

**Why the design point is 09:00 on 21 December.** The rule adopted is that no row shades
the next between 09:00 and 15:00 solar time on the winter solstice — the shortest day,
when the sun is lowest and shadows longest, across the conventional six-hour design
window. 09:00 is the worst moment inside that window, so satisfying it satisfies the whole
window.

**Be ready for: "why not solar noon only?"** That is the laxer criterion. At noon on
21 December the sun is at 38.01° and directly south, giving GCR 0.771 — about 9 per cent
more capacity (2,419 kWp instead of 2,221). We chose the stricter criterion because
noon-only spacing shades the array every winter morning and afternoon. The choice is
recorded in `docs/decisions.md` and is reversible with one setting in `config.py`.

## 1.2 Solar position — the 22.32° and 44.53°

You must be able to get these from the standard equations, because if you cannot, the
0.707 looks like it came from software you do not understand.

```
Declination at the solstice:   δ = −23.44°
Hour angle at 09:00 solar:     ω = 15° × (9 − 12) = −45°
Latitude:                      φ = 28.545° N

Elevation:   sin α = sin φ · sin δ + cos φ · cos δ · cos ω
                   = (0.47784)(−0.39779) + (0.87845)(0.91748)(0.70711)
                   = −0.19008 + 0.56995 = 0.37987
             α = 22.32°

Azimuth from south:
             cos γ = (sin α · sin φ − sin δ) / (cos α · cos φ)
                   = (0.37987 × 0.47784 + 0.39779) / (0.92506 × 0.87845)
                   = 0.57932 / 0.81271 = 0.71283
             γ = 44.53° east of south

Solar noon:  α = 90° − |φ − δ| = 90° − (28.545 + 23.44) = 38.01°
```

**PVGIS computes these independently and gets 22.30°, 44.50° and 38.00°.** Agreement to
within rounding. That is an external confirmation of the one number everything depends on
— use it.

## 1.3 The area chain

```
gross traced roof area            29,661 m²
  − obstructions                 −  8,457 m²   tanks, stair rooms, plant (21 polygons)
  − 1 m setback strip            −  4,007 m²   ≈ perimeter (4,038 m) × 1 m
  = net available area             17,198 m²
  × 0.707  ground coverage ratio                inter-row spacing
  × 0.85   packing factor                       walkways, inverter pads, cable trays
  = module area                    10,328 m²
  × 215 W/m²                                    module power per unit glass area
  = installable capacity            2,220.6 kWp
```

**Sanity check you should offer before being asked:** the setback area divided by the
total perimeter is 0.992 m, which confirms the 1 m strip was actually applied and not
approximated.

## 1.4 Capacity back-calculation — and why it is circular

The meter workbooks contain **no installed capacity**. Capacity per plant is therefore
estimated:

```
kWp = monthly kWh / (days × peak sun hours × performance ratio)
```

taken as the **median across all live months**, so one odd month cannot move it. Fleet
total ≈ **765 kWp**, interquartile range 575–938 kWp.

**Now the trap.** If you then compute specific yield as `kWh / kWp`, you get:

```
kWh / [ kWh / (days × PSH × PR) ]  =  days × PSH × PR
```

— a constant, identical for every plant, independent of the data. With our constants
(annual POA 1,978 kWh/m² on a 15° plane, PR 0.78) that constant is **1,543 kWh/kWp/yr**.
The FR-4 acceptance band is 1,300–1,600. **The test would pass by construction and prove
nothing.**

This is why the FR-4 back-test was restructured (§1.5 and §12.3 of the report). Being able
to explain this unprompted is one of the strongest things you can do in the viva — it
shows you understood a failure mode before it bit you.

## 1.5 The shape test — why it is *not* circular

Used twice: to arbitrate between irradiance sources in Part 3, and as the restructured
FR-4 back-test in Part 7.

**The method.** Take the 18 plants with a complete live 2024 (792 MWh). For each month,
compute that month's share of the plant's own annual total. Do the same for each
irradiance dataset. Compare the two twelve-element shape vectors.

**Why capacity cancels.** If plant output in month *m* is `kWp × f(m)`, then the share is:

```
share(m) = kWp·f(m) / Σ kWp·f(i)  =  f(m) / Σ f(i)
```

The `kWp` divides out exactly. The comparison depends only on **seasonality**, which is a
property of the irradiance data, not of the plant. So an unknown, estimated capacity
cannot contaminate the result.

**Results.**

```
total absolute shape error over 12 months:   NASA 0.072    PVGIS 0.109
January-to-April ratio:  measured 0.429   NASA 0.433   PVGIS 0.587
```

## 1.6 Losses combine multiplicatively

```
combined = 1 − Π (1 − lᵢ)     not     Σ lᵢ
```

Each stage acts only on what the previous stage passed through, so adding percentages
overstates the total. Our itemised stack — soiling 3.0%, mismatch 2.0%, DC wiring 1.5%,
AC wiring 1.0%, inverter clipping 0.5%, availability 2.0%, light-induced degradation 1.5%
— **sums to 11.5% but combines to 11.0%.**

<div class="pagebreak"></div>

# Part 2 — Concepts you must be fluent in

A panelist will probe whether you understand the quantities or merely transcribed them.

## 2.1 Irradiance and energy

| Term | What it means | Why it matters here |
|---|---|---|
| **GHI** | Global Horizontal Irradiance — total solar power on a horizontal surface | What both our data sources report; the basis of the FR-1 comparison |
| **DNI / DHI** | Direct Normal / Diffuse Horizontal | Needed for transposition to a tilted plane in Part 7 |
| **POA** | Plane-of-array irradiance — what actually strikes a tilted module | Not the same as GHI. Computed in Part 7 by Perez transposition |
| **PSH** | Peak sun hours — daily irradiation expressed as hours at 1 kW/m² | Used only in the capacity back-calculation |
| **kWp** | Capacity at standard test conditions (1000 W/m², 25 °C, AM1.5) | A *rating*, not an output |
| **kWh** | Energy actually produced | What the meters record |
| **Specific yield** | kWh per kWp per year | The FR-4 criterion: 1,300–1,600 for Delhi |
| **Capacity factor** | Average output ÷ rated output | ≈ specific yield ÷ 8,760 |
| **PR** | Performance ratio — actual output ÷ theoretical output at POA | Bundles all losses; we use 0.78 |

**Expect: "why is GHI not enough?"** Because modules are tilted. A 15° south-facing plane
at Delhi receives about 1,978 kWh/m²/yr against 1,745 GHI — the tilt gains roughly
13 per cent, and gains disproportionately in winter, when the sun is low.

## 2.2 Irradiance data sources

| | PVGIS TMY | NASA POWER |
|---|---|---|
| Origin | **ERA5 reanalysis** — a physical model of the atmosphere, reconstructed from assimilated observations | **Satellite radiometry** — observed top-of-atmosphere radiance converted to surface irradiance |
| Period | Typical months selected from 2005–2023 | Actual hourly record, 2014–2023 |
| Annual GHI here | 1,930.0 kWh/m²/yr | 1,744.7 kWh/m²/yr |
| Known weakness | Aerosol and fog over the Indo-Gangetic Plain | Coarser spatial resolution |

**A TMY is not a real year.** It is assembled from the most typical individual months
across a long record, so it represents a "normal" year. It is the right input for annual
energy estimation and the wrong input for studying extremes.

## 2.3 Metering

- **Cumulative register.** These meters report a running total, not an interval value.
  Energy is the **difference** between consecutive readings. A register that does not
  change means no generation.
- **Meter factor (MF).** A multiplier, 1 to 80 here, applied to the register difference
  to get kWh. It reflects the CT/PT ratio. Get it wrong and the energy is wrong by that
  factor.
- **Generation meter vs consumption meter.** Ours are generation meters. They tell you
  what the PV produced and nothing about what the building consumed — which is precisely
  why FR-5 is blocked.

## 2.4 Geospatial

- **EPSG:4326** — latitude/longitude, units of degrees. **EPSG:32643** — UTM zone 43 N,
  units of metres. All area and length work is done in 32643. Computing an area in
  degrees produces a number wrong by roughly four orders of magnitude.
- **Obstruction vs hole vs shading** — the taxonomy that governed the digitising:
  - Something standing **on** the roof (tank, stair room, plant) → an **obstruction**, subtracted.
  - Something that is **not roof at all** (courtyard, light well, gap between blocks) → a
    **hole** in the polygon. Subtracts the area *and* adds its edge to the perimeter, so
    the setback is applied around it.
  - Something that blocks **light** rather than occupying area (tree canopy, adjacent
    building) → **shading**, belongs to FR-3. Counting it here as well would penalise the
    same square metres twice.
- **IoU** (Part 5) — intersection over union of predicted and true roof polygons. 1.0 is
  perfect; the FR-2 threshold is 0.75.

## 2.5 Network concepts (Part 8 — be able to define these even though it is not built)

- **Voltage rise** — injecting power at the end of a feeder raises local voltage; too much
  breaches the statutory band.
- **Reverse power flow** — generation exceeding local load pushes power back through the
  transformer, which affects protection settings and tap changers.
- **Hosting capacity** — the maximum distributed generation a feeder can accept before a
  limit (voltage, thermal, protection) is violated. It is the headline output of Part 8.

<div class="pagebreak"></div>

# Part 3 — Numbers to know cold

| | |
|---|---|
| Candidate buildings | **10** (from 30 shortlisted, 21 viable) |
| Validation buildings | **6** (spec assumed 2) |
| Existing PV locations on campus | **29 locations, 31 meters** |
| Gross traced roof area | **29,661 m²** |
| Module area | **10,328 m²** |
| **Installable capacity** | **2,220.6 kWp ≈ 2.2 MWp** |
| Existing fleet, estimated | **765 kWp** (IQR 575–938) |
| Ratio | new potential ≈ **3×** existing |
| Ground coverage ratio | **0.7066** at 15° tilt |
| Design sun | **22.32° elevation, 44.53° E of S**, 09:00, 21 Dec |
| Setback | **1.0 m**, costing 4,007 m² |
| Packing factor | **0.85** |
| Module power density | **215 W/m²** |
| Meter readings parsed | **17,006**, of which **97** dropped |
| PVGIS GHI | **1,930.0 kWh/m²/yr** |
| NASA POWER GHI | **1,744.7 kWh/m²/yr** |
| Disagreement | **10.1%** against a 5% tolerance |
| Shape error | NASA **0.072**, PVGIS **0.109** |
| Plants stopped | **6 meters at 5 locations**; 4 with a quantified loss |
| Energy never generated | **166.8 MWh ≈ ₹13.3 lakh** |
| Still being lost | **≈ ₹0.97 lakh/month from 95 kWp idle** |
| OSM vs traced | **41,639 → 29,661 m², −29%** (range −0.3% to −67%) |
| Usable fraction range | **13.7% (B08) to 50.5% (B07)** |
| Combined loss stack | **11.0%** (sums to 11.5%) |
| Horizon | flat, **0.0°–1.9°** — no distant terrain shading |
| Site | 28.545° N, 77.192° E, **229 m** elevation |

**Forward estimate, if asked what 2.2 MWp would actually generate:** at a specific yield of
1,300–1,600 kWh/kWp/yr, roughly **2.9 to 3.6 GWh/year**. Say clearly that this is an
arithmetic projection, not a Part 7 result — the modelled figure will be lower once
shading is applied.

<div class="pagebreak"></div>

# Part 4 — Anticipated questions and answers

## A. Scope and method

**"Why only ten buildings?"**
The specification asked for eight to ten candidates. We derived a pool of 21 viable
buildings and selected ten on a matched-pair principle, holding five in a ranked reserve.
The constraint is not ambition, it is that hand-digitising takes about thirty minutes a
roof and the measurement had to be defensible. Part 5 exists to lift that limit.

**"How did you decide which buildings already have solar?"**
From the Institute's own generation-meter data — 29 locations appear in the meter records.
That is evidence, not observation. It also means the candidate list did not require a
request to the Estate Office; we derived it.

**"Did you physically inspect every building?"**
Not every one. Some were inspected on site; others were assessed from high-resolution
satellite imagery against the same four criteria — flat roof, existing panels, storey
count, visible obstructions. The report says so. Where imagery was the basis, the roof was
subsequently traced from imagery anyway, so the assessment and the measurement rest on the
same evidence.

**"What is a matched pair and why does it matter?"**
Seven of the ten candidates sit beside a near-identical building that already carries PV
and is in our validation set — Blocks 3 and 4 against Blocks 1, 2, 5, 6; three hostels
against the thirteen that already have panels. It converts the FR-4 back-test from a
generic plausibility check into a like-for-like prediction: the model can be asked to
predict Block 3 from Block 1, same design, same era, same orientation. That is a stronger
claim than the specification anticipated.

## B. The 2.2 MWp figure

**"How confident are you in 2.2 MWp?"**
The areas are hand-measured, the chain is auditable, and every intermediate value is in
the register. The weakest link is **B10 Central Workshop**, which fell 67 per cent from
its open-data outline and is worth about 500 kWp — we have flagged it for re-checking
before publication. Excluding B10 entirely takes the total to 2,041 kWp, so the finding
survives even in the worst case.

**"Your packing factor of 0.85 — where is that from?"**
It is an assumption, and the report says so. It covers walkways, inverter pads and cable
trays. It moves the headline by ±6 per cent across a plausible 0.80–0.90 range. It is one
of five values in the assumptions register that still need either a citation or a
measurement before the final report.

**"Is 1 m the correct fire setback?"**
It comes from the workflow note and we have flagged it as needing checking against the
applicable code — it may well be too little. It is the single most sensitive assumption in
the chain: at 1.5 m the total falls to 1,956 kWp, −11.8 per cent. We would rather be told
the correct figure than defend this one.

**"Why 15° tilt and not the latitude optimum of about 28°?"**
Flat-roof ballasted racking: lower tilt means lower wind uplift, less ballast, no roof
penetration, and much tighter row spacing. At our design sun the GCR is 0.707 at 15° but
only 0.589 at 28° — **17 per cent more module area on the same roof.** The trade-off is
that each module at 28° intercepts more annual irradiation. Which effect wins is a Part 7
question we have not yet answered; we have stated the assumption and quantified the area
side of the trade.

**"Your usable fractions range from 14% to 50%. Isn't that suspicious?"**
It is the finding. The 40–50 per cent rule of thumb holds only for clean roofs. B08
Textile Technology has 63 per cent of its roof covered in plant, so it lands at 13.7 per
cent; B07 and B09 have no obstructions at all and land near 50 per cent. A blanket factor
would have been wrong on both.

**"How do you know your tracing is accurate? You have no ground truth."**
Three answers. First, seven automated checks run after every session — and each one exists
because that exact error happened to us and was invisible on screen. Second, the traced
areas are consistent with storey counts and building types. Third, **Part 5 is the
independent check**: a segmentation model trained on INRIA and compared at IoU ≥ 0.75
against this hand-traced truth. We would also accept that an independent second trace by a
third person would quantify the subjectivity, and we have not done that.

## C. The FR-1 failure

**"Your FR-1 test failed. Isn't that a problem?"**
It failed as written, and we report it rather than hide it. The two sources disagree by
10.1 per cent against a 5 per cent tolerance. What matters is what followed: we verified it
was not our own error, localised the disagreement to winter, identified a documented
physical cause, and then resolved it against measured data. **A failed criterion that you
diagnosed and resolved is worth more than one that passed unexamined.**

**"You are claiming PVGIS is wrong. That is a widely used tool."**
We are not claiming PVGIS is wrong in general. We are claiming that *this* product — its
TMY for *this* location, which derives from ERA5 reanalysis — under-represents winter fog
and aerosol over the Indo-Gangetic Plain, which is a documented weakness of reanalysis in
this region. And we did not assert it: we tested both datasets against 792 MWh of measured
campus generation, and NASA matched the observed seasonality far better.

**"Could something other than irradiance explain the seasonal shape you measured?"**
Yes, and this is the right question. Four candidates:
- **Outages** — controlled for: only the 18 plants with a *complete live* 2024 were used.
- **Tilt** — measured output is plane-of-array on ~15° modules, which *raises* the winter
  share relative to GHI. This makes PVGIS's winter excess *larger* than our table shows,
  so it strengthens our conclusion.
- **Temperature derating** — reduces summer output, again raising the winter share.
  Strengthens the conclusion.
- **Soiling** — this is the one that cuts the other way. Delhi's winter dust would depress
  winter generation and could partly mimic the effect we attribute to irradiance. We have
  not quantified it. However, to explain the gap by soiling alone, January output would
  have to be depressed by about 27 per cent relative to April, which is far beyond typical
  soiling losses. So soiling may account for part of the difference but cannot account for
  it.

**"What would have happened if you had just used PVGIS?"**
Every yield figure in the project would have been about 10 per cent too high, and we would
never have known.

## D. The outage finding

**"How do you know those plants are actually dead rather than unread?"**
We do not, and that distinction is itself the question we are putting to the Estate Office
— **either answer is a reportable result.** What is certain is that the register did not
move: the same value written down daily for up to 23 months. If the meter was simply
unread, the recorded values would not have continued to be entered identically.

**"Is the ₹13 lakh figure solid?"**
The **outages are fact** — a register that does not move has not generated, and there is
no model in that claim. The **rupee figure is an estimate**, resting on a back-calculated
capacity and a provisional ₹8/kWh tariff. Say "roughly" out loud. Both caveats are on the
slide and in the report.

**"Why did nobody notice?"**
Because a reading was written down every single day throughout. The data was collected
faithfully and filed. Nobody had subtracted one day from the next. The evidence was in the
workbooks from the day they were handed over.

**"You said six plants, then four. Which is it?"**
Both, at different granularities. **Six meters, at five locations** — Vishwakarma carries
two meters. **Four of those locations carry a quantified loss.** The fifth is the SIT
Building, which last generated in April 2024 but has produced only 248 kWh in its entire
record — too little to back-calculate a capacity from, so no rupee figure can honestly be
attached. A plant that has generated 248 kWh in total is a finding in itself.

## E. Capacity and circularity

**"Where does 765 kWp come from if it is not in the data?"**
It is back-calculated from monthly energy, median across live months. The workbooks contain
no nameplate capacity — we searched all 28 sheets, every cell, the raw XML, cell comments
and hidden sheets. The supervisor agreed we may proceed on estimates. It is labelled an
estimate everywhere it appears.

**"Then how can you validate your generation model against it?"**
We cannot, and we say so. Specific yield computed from a capacity that was itself derived
from energy collapses to `days × PSH × PR` — about 1,543 kWh/kWp/yr with our constants —
identical for every plant. The test would pass by construction. That is why the FR-4
back-test is restructured into two genuinely independent checks: **normalised shape
validation**, and **capacity measured independently from module rows counted in satellite
imagery.**

**Trap to avoid.** If you divide 2024's 955 MWh by 765 kWp you get 1,249 kWh/kWp/yr, which
looks like a tidy cross-check against the 1,300–1,600 band. **Do not offer this as
validation** — it is contaminated by exactly the circularity above. If a panelist computes
it and offers it to you, say so.

## F. The remaining parts

**"Why is machine learning in this project at all?"**
To make the method scale. Ten roofs took about thirty minutes each to trace; two hundred
would take a hundred hours. That is the real reason, and it is a better answer than
"because the specification mentions it". Note also that it is **one part of nine** — the
project is not an ML project, and the hand-traced layer remains the official measurement.
If the model underperforms, that is still a reportable result.

**"What happens if the model does not reach IoU 0.75?"**
Nothing in the capacity figures changes, because they come from the hand-traced layer. We
report where the model failed and why — small roofs, cluttered roofs, buildings whose edges
are ambiguous in imagery — which is useful information about the limits of the automated
approach.

**"What if the Estate Office never provides D16, D17 and D18?"**
The specification's own mitigation applies: build a representative feeder from transformer
ratings and map distances, and declare every assumption. But we would then have to state
plainly that **FR-5's calibration criterion cannot be tested** — we will not present an
uncalibrated model as validated. This is the one thing we would genuinely like the panel's
help with.

**"Your meter data is daily. How will you model an hourly feeder?"**
We cannot get the hourly shape from daily totals. The shape will be modelled with pvlib
and calibrated against the daily totals, and the report will say so explicitly rather than
implying the hourly profile is measured.

## G. Economics and impact

**"What is 2.2 MWp actually worth?"**
We have not computed it yet — the economics are Part 9 and depend on three inputs we have
deliberately deferred: MNRE/CERC benchmark capital cost, the CEA grid emission factor, and
the campus tariff. What we can say arithmetically is that 2.2 MWp at 1,300–1,600
kWh/kWp/yr is roughly 2.9–3.6 GWh a year, before shading losses are applied.

**"Is the roof structurally capable of carrying panels?"**
Outside our scope and we do not claim otherwise. Ballasted racking at 15° was chosen partly
because it avoids roof penetration and keeps loads low, but a structural assessment per
building would be required before installation. Worth stating as a limitation.

## H. Probing and hostile questions

**"This looks like a lot of GIS clicking. Where is the engineering?"**
The engineering is in four places: the closed-form derivation of inter-row spacing from
solar geometry and its external validation; the non-circular arbitration between two
irradiance datasets using measured plant data; the diagnosis of a systematic bias in a
standard tool; and the detection of four failed plants from raw register data. The tracing
is the measurement, not the contribution.

**"Everything rests on assumptions you admit are unsourced."**
Some values are provisional and we have listed every one of them with its status, which is
more than most studies do. More usefully, we have quantified how much each one moves the
answer — see the sensitivity table overleaf. The headline survives every single-parameter
perturbation we tested, within a band of roughly −17 to +12 per cent.

**"Why should we believe hand-tracing over published open data?"**
Because we measured the difference rather than assuming it. Open footprints were wrong by
29 per cent on average and, critically, the error ranged from 0.3 per cent to 67 per cent
across ten buildings on one campus — so no correction factor could have fixed it. That is
a quantified argument, and it is one of the project's transferable results.

**"What would you do differently?"**
Three things. Start the repository in week 1 rather than week 5. Record the survey method
per building at the time rather than reconstructing it. And have a second person
independently re-trace two or three roofs to quantify the subjectivity in the measurement.

<div class="pagebreak"></div>

# Part 5 — Sensitivity of the headline figure

Computed directly from the register. Useful when a panelist challenges any single
assumption: you can answer with a number instead of a shrug.

| Change | Capacity | vs 2,220.6 kWp |
|---|---|---|
| Setback 1.5 m (stricter fire code) | 1,956 kWp | **−11.8%** |
| Setback 0.5 m | 2,477 kWp | +11.8% |
| Packing factor 0.80 | 2,086 kWp | −5.9% |
| Packing factor 0.90 | 2,347 kWp | +5.9% |
| Module density 200 W/m² | 2,062 kWp | −7.0% |
| Module density 230 W/m² | 2,371 kWp | +7.0% |
| Tilt 28° (GCR 0.589) | 1,847 kWp | **−16.7%** |
| Winter-noon criterion (GCR 0.771) | 2,419 kWp | +9.1% |
| B10 Central Workshop excluded entirely | 2,041 kWp | −7.9% |

**The message to deliver:** no single assumption moves the headline by more than about
17 per cent, and the conclusion — *the untapped roofs could carry roughly three times the
existing fleet* — holds across all of them.

<div class="pagebreak"></div>

# Part 6 — Weaknesses: say them before you are asked

Volunteering these is far stronger than conceding them under pressure. Each one already
appears in the report.

1. **B10 Central Workshop, −67 per cent from its OSM outline.** The largest correction and
   the weakest measurement, worth about 500 kWp. Needs re-checking before publication.
2. **B06 carries two obstructions typed `solar_panel`.** It was selected *because* it has
   no PV and it is not among the 29 metered locations. Either panels went up recently or
   there is an **unmetered array on campus** — in which case the existing fleet is larger
   than the records show. Worth raising with the Estate Office.
3. **One obstruction on B06 (fid 19) subtracts 1,294 m² while only 6 per cent of it lies
   on that roof.** Confirmed as intended but it costs B06 about 130 kWp.
4. **Five design values are not yet defended** — tilt, setback, packing factor, module
   density, and the soiling component of the loss stack. Each needs a citation or a
   measurement.
5. **Building heights are provisional** at storeys × 3.5 m, and feed directly into the
   FR-3 shading model.
6. **The tariff is provisional** at ₹8/kWh, so every rupee figure is indicative.
7. **The survey was partly desk-based**, and the per-building split was not recorded at the
   time.
8. **FR-5 cannot be tested** without three documents that cannot be derived.
9. **2025 is not comparable with 2024** — all 13 hostel meters are missing from every 2025
   sheet, so the 540 MWh figure is not a decline from 955 MWh.

<div class="pagebreak"></div>

# Part 7 — Three traps

**1. Do not quote 1,249 kWh/kWp/yr as a validation of the generation model.** It is 2024
generation divided by a capacity that was itself derived from generation. It is
circular. If challenged on fleet performance, talk about seasonal *shape*, not yield.

**2. Do not say "the two sources agree".** They do not, by 10.1 per cent. The strength of
the work is the diagnosis and the arbitration, not an agreement that does not exist.

**3. Do not present ₹13 lakh without its caveat in the same sentence.** "Roughly ₹13 lakh,
on an estimated plant capacity and a provisional tariff — the outages themselves are
certain." If an examiner has to extract the caveat from you, it looks like concealment; if
it is already in your own sentence, it looks like rigour.

# Part 8 — What to ask the panel

A mid-term review is also an opportunity. Three asks, in priority order:

1. **Help obtaining D16, D17 and D18** — the consumption bills, the single-line diagram
   and the transformer schedule. These are the only three items in the entire project that
   cannot be derived, fetched or estimated, and Part 8 cannot be validated without them.
2. **Agreement to restate FR-1's acceptance criterion** to *"where the sources disagree,
   the choice is justified against measured generation"* — which we have now done.
3. **A decision on the four stopped plants.** This is not a project matter; roughly ₹1 lakh
   a month is being lost today, and the Institute can act on it immediately.

Also worth raising: **D12**, the plant schedule with installed kWp, which would convert the
FR-4 back-test from a reconstructed check into a direct one.

---

# One-minute summary, if you are asked to open

> We set out to find how much more rooftop solar the campus could carry. We measured ten
> untapped roofs by hand and derived — rather than assumed — every subtraction from gross
> roof to installed panel, arriving at 2.2 MWp, about three times what the campus already
> has. Along the way three things came out of the Institute's own data that nobody had
> looked for: four solar plants that stopped generating up to 23 months ago and are still
> costing about a lakh a month; a 10 per cent disagreement between the two standard
> sunshine datasets, which we resolved against measured campus generation and which would
> otherwise have inflated every figure we produce; and a 29 per cent error in the free map
> data that most studies of this kind rely on. Four of nine parts are complete. One of the
> remaining five is blocked, on three documents only the Estate Office can give us.

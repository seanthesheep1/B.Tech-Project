# Demo runbook

What to run in front of Prof. Bansal, in what order, and what to say while it
runs. Timings are measured on this laptop, not estimated.

Everything here works **offline**. The Esri tiles are cached and every other
input is on disk, so campus wifi cannot embarrass you.

---

## Ten minutes before

```
make demo
```

Takes about 35 seconds and writes `notebooks/walkthrough.run.ipynb` with every
output embedded. Open it and leave it open in a second window. It is the
fallback if anything live misbehaves, and the thing to hand over afterwards.

Also open `reports/figures/solar_map.png` full screen in a third window.

Do not run `make demo` for the first time in the room.

---

## The five-minute run

Four commands. Run them in this order; the story builds.

### 1. The alarm — lead with this

```
make alarm
```

**19 seconds.** It is slow because it is parsing the Estate Office's own Excel
workbooks from scratch, which is worth saying out loud while it runs — it is
reading the Institute's raw data, not a cleaned copy we prepared.

> "This takes no model at all. It reads the Estate Office meter workbooks and
> asks which plants have stopped."

Then point at two things in the output:

- **Director's Lodge**, at 0.9% of its baseline for 19 months. Explain *why* it
  was invisible: its meter still creeps a few kWh a month, so it never reads as
  idle, and its all-time median is the dead level. The baseline is therefore
  the median of a plant's **first twelve months**, not its whole record.
- **The retrospective list at the bottom.** Thirteen alarms that would have
  fired, the earliest 21 months before the end of the record. The last line is
  the argument: *the data to do this was in the workbooks the whole time.*

And the validation that is easy to miss: **two of those plants are healthy
today.** Block No. 5 and Block No. 6 fired in 2024 and now read "generating as
usual". So the alarm catches real outages that were later fixed — not just
corpses. A detector that only flags permanently dead plants could be a trivial
"has it produced recently" check. This is doing something harder.

If asked about the ₹13 lakh: the tariff is a placeholder, so treat the rupees
as indicative. **The outages are not an estimate.** A register that does not
move has not generated.

Also be ready for: *"you say six stopped, but two show zero loss."* Correct —
those two appear never to have produced meaningfully. The honest framing is
four genuine failures carrying the 167 MWh, plus two that look never
commissioned, plus the Director's Lodge collapse.

### 2. The back-test — the validation

```
make backtest
```

**Under a second.**

> "The model has no fitted parameters, so the entire 28-month record of 18
> metered plants is a test set it has never seen."

Then the point that does the work:

> "We could not compare kWh per kWp. The only capacity figures for those plants
> were back-calculated from the generation they would be validating, so that
> ratio collapses to the assumed constant and passes whatever the model does.
> It is a check that cannot fail, which is worse than no check. So we compare
> **shape** — both series normalised to their own annual total. Capacity
> cancels out completely."

Result: shape error **0.097** against a 0.20 tolerance, so about **4.9% of
annual energy sits in the wrong month**.

Say the caveat before anyone asks: the model describes ten *candidate* roofs
and the meters are on eighteen *different* buildings. Some of that 0.097 is
that mismatch, not model error.

### 3. Soiling — the parameter we refused to fit

```
make soiling
```

**Half a second.** This is the one that shows methodological care.

> "November averages three millimetres of rain and one wet day per decade, so
> dust builds from October to the monsoon with nothing to remove it — over
> exactly the months the model runs high."

Then the part worth making explicit:

> "We could have tuned the soiling rate until the back-test passed and then
> reported that the back-test passed. That rate would have absorbed whatever
> else was wrong. So we sweep it, print the whole curve, and the model uses a
> different, stated value — 0.30% a day from the literature, not the 0.50% the
> sweep finds. The sweep is a diagnostic. The constant is the input. They are
> different numbers in different files, on purpose."

And the honest close: dust explains most of the winter leg and the total shape
error barely moves, because both series are normalised so energy removed from
December reappears in August. What remains is a spring and monsoon error of the
opposite sign, which dust cannot cause. **That is still open.**

### 4. The map — finish on the picture

```
make map
```

**Under a second**, then open the PNG.

Two panels, same ground. Left is how much is there, right is what it costs.
Darker is more in both — good on the left, bad on the right.

- **B06**, the Lecture Hall Complex: biggest at 663 MWh *and* among the
  cheapest at ₹3.49/kWh.
- **B03 and B04**: pale on the left, dark on the right. Small and expensive,
  because they carry 9.4% and 9.6% shading against a 3.05% campus mean.

> "That is the shading model and the economics agreeing with each other, in a
> form you can see from across the room."

---

## If there is time: two more

```
make sensitivity
```

**7 seconds.** Six obstruction heights were never measured and carry 85% of the
shading loss. Rather than assert them harder, this shows what they cost: across
a fourfold range the campus energy moves under 5%, but the worst roof swings
from 3.5% to 19%. **The headline is robust and the ranking is not.**

```
make audit
```

**Half a second.** Every stage, its inputs, its outputs, and whether any output
is older than an input feeding it. Currently 10 current, 0 stale. Answers
"how do you know these numbers are current" in one command.

---

## The three questions to be ready for

**"What is the accuracy?"**

There is no single number, and say so. The detector scores IoU 0.707 on 68
held-out images. The generation model's *seasonal shape* is right to 4.9%
against data it never saw. The **absolute** energy figure is **not validated**,
because no plant with a trustworthy independently-known capacity was available
to compare against. One properly documented installation would fix that.

That answer is much harder to attack than a confident percentage.

**"Is the project finished?"**

No, and the gaps are written down rather than buried:

- FR-1 fails its 5% criterion — the two irradiance sources disagree by 10.1%.
  The failure was then *used*: measured generation arbitrated between them and
  NASA won, 0.072 against PVGIS's 0.109.
- FR-5, the feeder study, was not built. The network data was requested in
  writing and never arrived.
- The spring and monsoon residual is unexplained.
- Six obstruction heights are assumed, bounded by `make sensitivity`.
- The detector weights need one hour of GPU to regenerate.

**"How much of this did you do yourself?"**

Answer plainly. The survey, the tracing and the obstructions are observations
only you made. The matched-pair selection — choosing candidate roofs that sit
beside instrumented twins so the model could be validated at all — was your
judgement and is not in the specification. Every number regenerates from a
named command you can run in front of them. `docs/decisions.md` records every
assumption with its reasoning, including the ones that turned out wrong.

Some of the implementation was done with AI assistance. If asked, say so
plainly; it is ordinary practice and being straightforward costs nothing.

---

## What not to claim

- Do not call 2,906 MWh/yr validated. Its *shape* is validated; its level is not.
- Do not quote the IoU 0.707 against the 0.75 threshold without saying the
  threshold was written for a different task — usable roof area, not installed
  panels. And that the model found real arrays the annotator missed, which IoU
  counts *against* it, so the score is a floor.
- Do not present the map as a build order. Grid connection, occupancy and who
  pays are not modelled. The per-roof figures are published; the ordering is
  for whoever owns those constraints.
- Do not say the back-test residual is explained. Most of the winter leg is.
  The rest is not.

---

## If something fails live

Switch to `notebooks/walkthrough.run.ipynb`, which has every output already
embedded, and carry on. Then say what broke and why — a student who can
diagnose their own tooling in the room is making a better impression than one
whose demo merely worked.

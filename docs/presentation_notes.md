# Mid-term review deck — slide-by-slide notes

For `reports/BTP_midterm_review_bold.pptx`. Ten slides, about ten minutes, for a
department panel that does not know the project.

Every number on every slide traces back to `data/building_register.csv`,
`data/roofs.gpkg` or the Estate Office workbooks. Where a figure rests on an
assumption, that is said on the slide itself.

---

## Design system

| | |
|---|---|
| **Amber** `#D97706` | the project's primary — solar, and the "done / headline" colour |
| **Blue** `#1D6FA3` | secondary — data we collected, supporting facts |
| **Crimson** `#B02418` | losses and subtractions; the outage slide's field |
| **Ink** `#14110F` | near-black fields |
| **Cream** `#FBF7F0` | light fields |
| **Headlines** | Arial Bold, 40–80 pt |
| **Body** | Calibri, 12–19 pt |

The three chart colours pass all six colourblind checks (lightness band, chroma
floor, CVD separation, normal-vision floor, contrast). Three other candidate
palettes were tested and rejected.

**The device is the colour block.** Every slide is either a full colour field or
a composition of solid rectangles. No gradients, no drop shadows, no icons, no
accent stripes.

---

## Slide 1 — Title

**Layout.** Ink field. A solid amber block covers the left third, carrying the
IIT Delhi logo (recoloured white) and the words `ROOFTOP / SOLAR / POTENTIAL`
stacked. The right two-thirds carry the rest of the title on the dark.

**Text.**
- Left block: `ROOFTOP SOLAR POTENTIAL`
- Right: `Mapping of the IIT Delhi Campus`
- `B.Tech Project · Mid-term Review`
- Three name rows, each with a small colour chip: Tejas Suresh Kamble
  (2023EE10974), Surbhi Rathore (2023EE11224), Prof. Yashasvi Bansal (Supervisor)
- `DEPARTMENT OF ELECTRICAL ENGINEERING`

**Why.** Splitting the title across the colour boundary makes the first slide
read as designed rather than as a template. The colour chips beside the names
introduce the amber / blue / crimson system before any data appears, so by
slide 6 the audience already reads amber as "the project's own number".

---

## Slide 2 — The problem

**Layout.** Deep-blue field. Large white statement top-left, four numbered
objectives below, and a solid amber block down the right carrying a pull-quote.

**Text.**
- `Many flat roofs on campus carry no panels.`
- `Nobody has measured what they could generate.`
- Objectives, numbered 1–4: find the roofs still unused · measure what is
  genuinely usable · estimate the electricity · check the grid can absorb it
- Amber block: *"Along the way we found something in the Institute's own data
  that nobody had noticed."*

**Why.** The panel does not know the project, so the problem has to be stated in
one sentence they can hold. The four objectives map exactly onto FR-2, FR-3 and
FR-5 of the specification, in plain words.

The pull-quote is a deliberate hook. The strongest thing in the deck arrives on
slide 6; without a promise here the audience has no reason to wait for it. The
first objective's number badge is amber while the rest are dark — a quiet signal
that step one is where the surprise came from.

---

## Slide 3 — The data

**Layout.** Cream field, two large facing panels: amber for what was given to
us, blue for what we collected.

**Text.**
- Amber panel: `GIVEN TO US` · **31** solar meters, read every day ·
  `January 2024 — April 2026` · 17,000 daily readings across two spreadsheets ·
  97 typing errors found and corrected
- Blue panel: `COLLECTED BY US` · Sunshine records (NASA POWER · PVGIS) ·
  Building outlines (OpenStreetMap) · Satellite imagery (Esri World Imagery) ·
  Sun angles (for panel row spacing)

**Why.** An examiner's first question about any data-driven project is *where
did the data come from*. Answering it before the findings removes the doubt
early. The two-panel split makes the distinction visible at a glance: half the
project rests on Institute records, half on public sources.

**The 97 typing errors line is doing real work.** It says, without labouring
it, that the data was not taken on trust. Decimal-point slips, blanks entered as
zero, and one month whose dates were stored as text. Differencing the raw
register without repairing those inflates annual generation about tenfold.

---

## Slide 4 — Nine parts, four complete

**Layout.** Cream field, a 5 × 2 grid of cards. Parts 1–4 solid amber, parts 5–9
pale grey. Each card: number, title, one-line description. A small legend below.

**Text.** 1 Choose the buildings · 2 Read the meter data · 3 Collect sunshine
data · 4 Measure the roofs · 5 Machine learning · 6 Shadows · 7 Calculate
electricity · 8 Grid impact · 9 Report and costs.

**Why.** This is the slide that tells the panel *how much of the project is
done*. Four amber cards against five grey ones answers that in one glance, which
matters at a mid-term review where progress is the thing being assessed.

Nine cards also lets the panel see that the machine-learning component is one
part of nine rather than the centrepiece — which is the honest weighting and
heads off the assumption that this is an ML project.

---

## Slide 5 — Part 1 · Choosing the buildings

**Layout.** The campus map runs full-bleed down the right. A solid amber panel
covers the left third.

**Figure.** `campus_roofs_map_slide.png` — the QGIS view with all ten traced
roofs outlined in red and their obstructions in orange, labelled B01–B10. The
QGIS toolbars and panels are cropped away so it reads as a figure, not a
screenshot. The crop was computed by locating the red outline pixels and
matching the panel's aspect ratio exactly, so no building is clipped.

**Text.** `PART 1` · `Choosing the buildings` · downloaded every campus building
outline · removed the 29 roofs that already have panels · checked the rest on
foot · **10** buildings selected · 3 hostels · 4 academic · 2 labs · 1 workshop

**Why.** The panel has no mental picture of the campus, and a list of building
names means nothing to them. The map does the work a paragraph cannot.

The important claim here is that **the list is evidence-based**. The 29 roofs
with existing panels were identified from the meter data, not by walking around
hoping to spot them — which is why the candidate list can be defended rather
than merely asserted.

---

## Slide 6 — Part 2 · The finding

**Layout.** Deep crimson field. Headline top-left, the outage chart below it
drawn on the same crimson so it belongs to the slide, and a solid amber block
on the right carrying the money figure.

**Figure.** `bold/outages.png` — horizontal bars, months idle per plant, with
the longest outage in a stronger amber.

**Text.**
- `Four plants have stopped generating.`
- Amaltas Guest House 23 months · Central Library 10 · Main Building 8 ·
  Vishwakarma 6
- Amber block: **₹13 LAKH** of electricity never generated · ₹1 lakh still lost
  every month
- *"The readings were written down every single day throughout. Nobody had
  subtracted one day from the next."*
- Footnote: rupee figures estimated from plant size and a provisional tariff;
  the outages themselves are certain

**Why this is the centre of the deck.** Every other rooftop-solar project asks
*how much could we add*. This slide asks *does what we already have still work* —
and the answer was no, in four places, for up to 23 months, in data the
Institute had been collecting daily the whole time.

It is also the most defensible thing in the deck. A register that does not move
has not generated; there is no modelling assumption in that claim.

**The footnote is not optional.** The outage count and durations are fact. The
₹13 lakh rests on a back-calculated plant capacity and an unconfirmed tariff.
Say "roughly" out loud. If an examiner asks how you know the capacity, the
caveat should already be in your own sentence rather than extracted from you.

---

## Slide 7 — Part 3 · Sunshine data

**Layout.** Cream field. A solid blue stat panel on the left, the chart on the
right.

**Figure.** `bold/sunshine.png` — three lines, share of the year's sunshine by
month: PVGIS in crimson, NASA in blue, measured campus generation in amber.

**Text.**
- **10%** disagreement between the two sunshine sources — almost all of it in winter
- `We settled it with the campus's own meters.`
- Real generation tracks NASA almost exactly.
- Caption: trusting the standard tool would have made every figure about 10% too high

**Why.** FR-1 of the specification requires the two irradiance sources to agree
within 5 per cent. **They do not — the gap is 10.1 per cent, so FR-1 fails as
written.** That is on the slide, not hidden.

What rescues it is the explanation. The disagreement is not noise; it is almost
entirely in winter, where PVGIS claims up to 47 per cent more January sun. The
cause is Indo-Gangetic winter fog and aerosol, which the ERA5 reanalysis behind
PVGIS represents poorly.

And the arbitration is the strongest methodological moment in the project: the
campus's own 792 MWh of measured generation was used to decide which source to
trust. Monthly generation and monthly irradiance were each normalised to their
own annual total, so unknown plant capacity cancels out and the test is not
circular. NASA matched the measured seasonal shape almost exactly; PVGIS was
37 per cent out on the January-to-April ratio.

**A failed acceptance test that you diagnosed and resolved is worth more to an
examiner than one that passed unexamined.** Present it that way.

---

## Slide 8 — Part 4 · Measuring the roofs

**Layout.** Cream field. `2.2 MWp` at 80 pt in amber across the top with the
explanation beside it. Below, two charts side by side under coloured rules.

**Figures.**
- `bold/area_chain.png` — waterfall: 29,661 roof traced → −8,457 obstructions →
  −4,007 setback → 17,198 net available → −6,871 row spacing and walkways →
  **10,328 m² panel area**
- `bold/capacity.png` — kWp per building, ranked: Lecture Hall Complex 486 down
  to Material Science 62

**Text.** `2.2 MWp could be installed across the ten roofs — about three times
the solar the campus already has.` Section labels: `FROM ROOF TO PANELS` and
`WHAT EACH ROOF COULD CARRY`.

**Why.** This is the project's headline result and the slide an examiner will
grade hardest, so it shows the method rather than asserting the number. The
waterfall makes every subtraction visible and auditable.

**The number that matters underneath it is 0.707** — the ground coverage ratio.
The specification explicitly forbids assuming a usable percentage, so it is
derived from the winter sun: no panel row shades the next between 9 am and 3 pm
on 21 December, when the sun at IIT Delhi sits 22.32° above the horizon at
44.53° east of south. Those angles were checked against PVGIS's own solar
position calculation and agree to within rounding.

Two further findings sit behind this slide and are worth having ready:

- **The free map outlines were wrong by 29 per cent**, and unevenly — from
  −0.3 per cent on Vindhyachal to −67 per cent on Central Workshop. No single
  correction factor could have fixed that, which is the argument for hand
  digitising rather than scaling.
- **The 40–50 per cent rule of thumb does not hold.** Usable fraction runs from
  13.7 per cent on Textile Technology, whose roof is 63 per cent covered in
  plant, to 50.5 per cent on Academic Complex East.

---

## Slide 9 — Parts 5 to 9

**Layout.** Ink field. Five columns, each headed by a colour block carrying its
number, then the part name, then one line of description.

**Text.** 5 Machine learning — train a model to find roofs automatically, so the
method scales from 10 buildings to all 200 · 6 Shadows · 7 Electricity ·
8 Grid impact (waiting on three Estate Office documents) · 9 Report and costs.

**Why.** A mid-term review is assessed partly on whether the remaining plan is
credible. Five equal columns say the rest of the project is mapped, not vague.

**The machine-learning line is deliberately framed as scaling, not novelty.**
Ten roofs took roughly thirty minutes each to trace by hand; two hundred would
take a hundred hours. That is the real reason to train a model, and it is a
better answer than "because the specification mentions ML".

**Part 8 names its blocker in public.** Three documents — the consumption bills,
the single-line diagram and the transformer schedule — are the only things in
the whole project that cannot be derived, fetched or estimated. Saying so on the
slide invites the panel to help rather than leaving it as an excuse later.

---

## Slide 10 — Thank you

**Layout.** Full amber field. Logo, large `Thank you`, and three ink blocks
carrying the headline numbers.

**Text.** `Thank you` · `Questions welcome` · **4** plants found stopped ·
**10** roofs measured · **2.2 MWp** untapped potential

**Why.** The three numbers stay on screen through the question period, which
means the panel is looking at your strongest facts while they decide what to
ask. The amber field closes the loop with the title slide's block.

---

## Questions to expect, and the short answers

**"How do you know the plants are actually dead?"**
The meter register did not move. Not a model — a reading that stayed identical
for 23 months while being written down daily.

**"Why is your FR-1 test failing?"**
Because the two sources genuinely disagree, by 10 per cent, almost all of it in
winter smog. We resolved it against measured campus generation rather than
picking one.

**"Where does 0.707 come from?"**
Row spacing so no panel shades the next between 9 am and 3 pm on 21 December.
Derived, and cross-checked against PVGIS.

**"How confident are you in 2.2 MWp?"**
The areas are hand-measured and the chain is auditable. The weakest link is
Central Workshop, which fell 67 per cent from its open-data outline and is worth
re-checking — about 500 kWp of the total.

**"Is the ₹13 lakh solid?"**
The outages are. The rupee figure rests on an estimated plant capacity and an
unconfirmed tariff, so treat it as indicative.

**"What about the panels on the Lecture Hall Complex?"**
Two obstructions there were recorded as solar panels, but the building is not
among the 29 metered locations. Either recently installed or unmetered — worth
the Estate Office confirming, because an unmetered array means the existing
fleet is larger than the records show.

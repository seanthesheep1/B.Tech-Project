# Mid-term review deck — slide-by-slide notes

For `reports/BTP_midterm_review_bold.pptx`. Ten slides, about ten minutes, for a
department panel that does not know the project.

Every number on every slide traces back to `data/building_register.csv`,
`data/roofs.gpkg` or the Estate Office workbooks. Where a figure rests on an
assumption, that is said on the slide itself.

---

## Slide 1 — Title

**What is on it.** The project title, split across the slide. The IIT Delhi
logo. Both names with entry numbers, the supervisor, and the department.

**Text.**
- `ROOFTOP SOLAR POTENTIAL`
- `Mapping of the IIT Delhi Campus`
- `B.Tech Project · Mid-term Review`
- Tejas Suresh Kamble (2023EE10974) · Surbhi Rathore (2023EE11224) ·
  Prof. Yashasvi Bansal (Supervisor)
- `DEPARTMENT OF ELECTRICAL ENGINEERING`

**Context.** Nothing to argue here — it exists so the panel knows who is
speaking and under whose supervision before the content starts.

---

## Slide 2 — The problem

**What is on it.** A two-line statement of the problem, four numbered
objectives, and a pull-quote panel on the right.

**Text.**
- `Many flat roofs on campus carry no panels.`
- `Nobody has measured what they could generate.`
- Objectives 1–4: find the roofs still unused · measure what is genuinely
  usable · estimate the electricity · check the grid can absorb it
- Pull-quote: *"Along the way we found something in the Institute's own data
  that nobody had noticed."*

**Context.** The panel does not know the project, so the problem has to fit in
one sentence they can hold. The four objectives map directly onto FR-2, FR-3 and
FR-5 of the specification, restated in plain words.

The pull-quote is a deliberate hook. The strongest material in the deck arrives
on slide 6; without a promise here the audience has no reason to wait for it.

---

## Slide 3 — The data

**What is on it.** Two facing panels — what the Estate Office gave us, and what
we collected ourselves.

**Text.**
- Given to us: **31** solar meters, read every day · `January 2024 — April 2026`
  · 17,000 daily readings across two spreadsheets · 97 typing errors found and
  corrected
- Collected by us: Sunshine records (NASA POWER · PVGIS) · Building outlines
  (OpenStreetMap) · Satellite imagery (Esri World Imagery) · Sun angles (for
  panel row spacing)

**Context.** An examiner's first question about any data-driven project is
*where did the data come from*. Answering it before the findings removes the
doubt early, and the split shows that half the project rests on Institute
records and half on public sources.

**The "97 typing errors" line is doing real work.** It says, without labouring
it, that the data was not taken on trust. Decimal-point slips, blanks entered as
zero, and one month whose dates were stored as text. Differencing the raw
register without repairing those inflates annual generation about tenfold.

---

## Slide 4 — Nine parts, four complete

**What is on it.** A 5 × 2 grid of cards, one per part. The first four are
marked complete; the remaining five are marked as still to do. Each card carries
its number, its name, and a one-line description.

**Text.** 1 Choose the buildings · 2 Read the meter data · 3 Collect sunshine
data · 4 Measure the roofs · 5 Machine learning · 6 Shadows · 7 Calculate
electricity · 8 Grid impact · 9 Report and costs.

**Context.** This is the slide that tells the panel *how much of the project is
done*, which is the thing a mid-term review is assessing. Four complete against
five outstanding answers it at a glance.

Showing all nine also makes clear that the machine-learning component is one
part of nine rather than the centrepiece — the honest weighting, and it heads
off the assumption that this is an ML project.

---

## Slide 5 — Part 1 · Choosing the buildings

**What is on it.** The campus map running full height down the right, with a
text panel on the left.

**Figure.** `campus_roofs_map_slide.png` — the QGIS view with all ten traced
roofs outlined and their obstructions marked, labelled B01–B10. The QGIS
toolbars and side panels are cropped away so it reads as a figure rather than a
screenshot. The crop was computed by locating the outline pixels and matching
the panel's aspect ratio exactly, so no building is clipped.

**Text.** `Choosing the buildings` · downloaded every campus building outline ·
removed the 29 roofs that already have panels · checked the rest on foot ·
**10** buildings selected · 3 hostels · 4 academic · 2 labs · 1 workshop

**Context.** The panel has no mental picture of the campus, and a list of
building names means nothing to them. The map does work a paragraph cannot.

The claim that matters is that **the list is evidence-based**. The 29 roofs with
existing panels were identified from the meter data, not by walking around
hoping to spot them — which is why the candidate list can be defended rather
than merely asserted.

---

## Slide 6 — Part 2 · The finding

**What is on it.** The headline, a bar chart of how long each stopped plant has
been idle, and a panel carrying the money figure.

**Figure.** `bold/outages.png` — horizontal bars, months idle per plant.

**Text.**
- `Four plants have stopped generating.`
- Amaltas Guest House 23 months · Central Library 10 · Main Building 8 ·
  Vishwakarma 6
- **₹13 lakh** of electricity never generated · ₹1 lakh still lost every month
- *"The readings were written down every single day throughout. Nobody had
  subtracted one day from the next."*
- Footnote: rupee figures estimated from plant size and a provisional tariff;
  the outages themselves are certain

**Context — this is the centre of the deck.** Every other rooftop-solar project
asks *how much could we add*. This slide asks *does what we already have still
work* — and the answer was no, in four places, for up to 23 months, in data the
Institute had been collecting daily the whole time.

It is also the most defensible thing in the deck. A register that does not move
has not generated; there is no modelling assumption in that claim.

**The footnote is not optional.** The outage count and durations are fact. The
₹13 lakh rests on a back-calculated plant capacity and an unconfirmed tariff.
Say "roughly" out loud. If an examiner asks how you know the capacity, the
caveat should already be in your own sentence rather than extracted from you.

---

## Slide 7 — Part 3 · Sunshine data

**What is on it.** A panel stating the disagreement, and a chart comparing the
two sunshine sources against measured campus generation.

**Figure.** `bold/sunshine.png` — three lines, share of the year's sunshine by
month: PVGIS, NASA POWER, and measured campus generation.

**Text.**
- **10%** disagreement between the two sunshine sources — almost all of it in winter
- `We settled it with the campus's own meters.`
- Real generation tracks NASA almost exactly.
- Caption: trusting the standard tool would have made every figure about 10% too high

**Context.** FR-1 of the specification requires the two irradiance sources to
agree within 5 per cent. **They do not — the gap is 10.1 per cent, so FR-1 fails
as written.** That is on the slide, not hidden.

What rescues it is the explanation. The disagreement is not noise; it is almost
entirely in winter, where PVGIS claims up to 47 per cent more January sun. The
cause is Indo-Gangetic winter fog and aerosol, which the ERA5 reanalysis behind
PVGIS represents poorly.

The arbitration is the strongest methodological moment in the project. The
campus's own 792 MWh of measured generation decided which source to trust:
monthly generation and monthly irradiance were each normalised to their own
annual total, so unknown plant capacity cancels out and the test is not
circular. NASA matched the measured seasonal shape almost exactly; PVGIS was
37 per cent out on the January-to-April ratio.

**A failed acceptance test that you diagnosed and resolved is worth more to an
examiner than one that passed unexamined.** Present it that way.

---

## Slide 8 — Part 4 · Measuring the roofs

**What is on it.** The headline capacity figure across the top, and two charts
below it.

**Figures.**
- `bold/area_chain.png` — waterfall: 29,661 roof traced → −8,457 obstructions →
  −4,007 setback → 17,198 net available → −6,871 row spacing and walkways →
  **10,328 m² panel area**
- `bold/capacity.png` — kWp per building, ranked: Lecture Hall Complex 486 down
  to Material Science 62

**Text.** `2.2 MWp could be installed across the ten roofs — about three times
the solar the campus already has.` Section labels: `FROM ROOF TO PANELS` and
`WHAT EACH ROOF COULD CARRY`.

**Context.** This is the project's headline result and the slide an examiner
will grade hardest, so it shows the method rather than asserting the number. The
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

**What is on it.** Five columns, one per remaining part, each with its number,
name and a one-line description.

**Text.** 5 Machine learning — train a model to find roofs automatically, so the
method scales from 10 buildings to all 200 · 6 Shadows · 7 Electricity ·
8 Grid impact (waiting on three Estate Office documents) · 9 Report and costs.

**Context.** A mid-term review is assessed partly on whether the remaining plan
is credible. Five equal columns say the rest of the project is mapped, not
vague.

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

**What is on it.** `Thank you`, `Questions welcome`, and the three headline
numbers: **4** plants found stopped · **10** roofs measured · **2.2 MWp**
untapped potential.

**Context.** The three numbers stay on screen through the question period, so
the panel is looking at your strongest facts while deciding what to ask.

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

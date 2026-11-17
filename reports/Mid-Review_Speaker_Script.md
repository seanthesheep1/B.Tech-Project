# Mid-Review — Speaker Script
**Deck:** Mid-Review PPT Draft 2.pptx · 10 slides · target 13–14 minutes
**Speaking notes:** plain language, short sentences. *[italics]* = what to do, not what to say.

---

## Slide 1 — Title *(~55 sec)*

Good morning. I am Tejas, and this is Surbhi. Our project is on rooftop solar for the IIT Delhi campus, under Prof. Yashasvi Bansal.

The question we are trying to answer is a simple one. The campus has hundreds of roofs. Some of them already have solar panels on them. Nobody can tell you how much more the campus could put up, or which roof to start with.

*[point to the strip of photos along the bottom]* These five pictures are our own work. Each one is a campus roof that we traced by hand. There are ten of them in total, and you will see them again later.

In the next fifteen minutes I will cover four things: why this project exists, what data we are working from, how the work is split up, and what we have finished so far.

---

## Slide 2 — Why this project *(~85 sec)*

Start with the situation today. The Institute buys almost all of its electricity from the grid, and it pays for every unit.

Meanwhile the roofs sit there doing nothing. They are the biggest thing the Institute owns that is not being used.

Now, the usual way people answer this question is a shortcut. They say: assume forty per cent of every roof is usable, multiply by the total roof area of the campus, and print a number. *[pause]* That is not a measurement. That is a guess wearing the clothes of a measurement. And somebody is expected to spend crores on the strength of it.

So our aim is different. We want a building-by-building answer, where every step behind the number is written down and can be checked by someone else.

*[point to the three boxes]* Three questions fall out of that.

Which roofs? Because not every roof is worth it — some are full of water tanks and plant rooms, some are in shade, and some already have panels.

How much power? A number that survives questioning, with every assumption named.

And can the network take it? Because solar only helps if the campus wiring can actually absorb what the roofs make.

---

## Slide 3 — Three kinds of data *(~80 sec)*

Before any of that, a fair question: where is your data coming from? Everything we use falls into three buckets.

*[point to box one]* First, what was given to us. Our supervisor handed us two workbooks. They hold daily meter readings from the solar plants that are already on campus, going back more than two years.

One caution here, and it matters later. These are *generation* records. They tell us what the existing panels *make*. They do not tell us what the buildings *use*. Those are two different things.

*[point to box two]* Second, what we fetched ourselves. Satellite pictures of the campus, building outlines from OpenStreetMap, and two separate records of how much sunlight Delhi gets. All of it is public and free. For each one we logged the date we downloaded it and the exact query we used, so any number can be traced back to its source.

*[point to box three]* Third, what we produce ourselves. A cleaned month-by-month record of every existing plant. The shortlist of ten buildings. The roof outlines we traced. And one register — a single sheet with one row per building and one column per value we compute, each with its formula sitting next to it. That register is our audit trail.

*[point to the red line at the bottom]* Two things are still to come from the Estate Office: the electricity bills, and the campus network diagram. We have deliberately arranged the work so that nothing waits on them until the very end.

---

## Slide 4 — The project in nine parts *(~65 sec)*

Here is the whole project on one slide. Nine parts. Each part makes something that the next part needs.

*[run your finger across the first four]* The first four are done. Choose the buildings. Read the meter records of the plants already installed. Gather the sunlight and map data. Measure the roofs.

*[point to five through nine]* Five remain. Teach a machine to find roofs, so the method works past ten buildings. Model the shadows. Turn sunlight into units of electricity per year. Test the network. Then rank everything and write it up.

One thing about the order is deliberate, and I want to flag it. *[point to part 8]* The only part that needs data we do not have — the Estate Office data — sits at the end. So if that data is slow to arrive, everything else has already been done.

---

## Slide 5 — Part 1: Choosing the buildings *(~90 sec)*

Part one. Which buildings do we study?

We started from the campus map. We removed every roof that the meter records show already has panels. Then we walked the campus and checked what was left with our own eyes, because a map can be out of date and a roof cannot.

We picked ten. Academic blocks, hostels, labs, and a workshop — a mix, so that whatever we find is not true only of one kind of building.

Now the part I would like you to notice. *[point to the map]* Most of these ten were chosen in pairs. Each building we picked sits next to a near-identical building that *already* has solar on it, and that neighbour is metered.

Why does that help? Take Blocks 3 and 4. They have no solar. But Blocks 1, 2, 5 and 6 are the same design, same age, same direction, and they do have panels. So when we predict what Block 3 would generate, we do not have to ask you to take our word for it. We can check our prediction against the twin standing next door. The same holds for the hostels.

One surprise along the way: many more roofs already have panels than the project brief assumed. That means less spare roof than we expected — but it gives us a much bigger set of real installations to test our work against.

---

## Slide 6 — Part 2: What the existing plants are doing *(~110 sec)*

Part two. We read those two workbooks — over two years of daily readings, all entered by hand.

Most of this part was not analysis. It was repair. Decimal points in the wrong place. Columns that move position from one sheet to the next. A meter that gets renumbered halfway through the record. If you take the file at face value, the campus appears to generate about ten times what it really does.

Once cleaned, we get a proper month-by-month record of every plant on campus. That becomes our yardstick later — when our model predicts a number, we compare it against what these real plants actually produced.

But something else came out of this, which we were not looking for. *[pause, then point to the quote]* Several plants have not generated anything for months. And for every one of those days, a reading was still being written into the workbook.

*[read the quote out]* "The readings were taken faithfully every day. The meter simply never moved."

Let me be careful about what I am claiming. A meter reading that does not change means no generation — that part is simply fact, and it was sitting in the files from the day we received them. What we estimate is the cost: roughly one lakh rupees a month of electricity the Institute is paying for instead of making. That figure rests on an assumed capacity and an assumed tariff, so we call it indicative. The outages themselves are not in doubt.

We would like to ask the Estate Office one question about this: are those plants dead, or is nobody reading them? Either answer is useful.

---

## Slide 7 — Part 3: How much sun does the campus get? *(~95 sec)*

Part three. Sunlight. This one input sits underneath everything else — every later number scales with it. So we did not take one source. We took two independent ones.

They disagreed. *[point to the chart]* And look at *where* they disagree. It is almost entirely in winter. That is when fog and haze sit over north India, and haze is genuinely hard to judge from a satellite. So the disagreement has a physical reason behind it.

Now we had to choose between them. We could have picked the more famous one. Instead we let the campus decide.

*[point to the gold line]* This gold line is not a model at all. It is what the panels already on our roofs actually produced, month by month. It is the campus's own evidence.

The NASA record follows that real pattern closely. The other one does not. So we use NASA, and we can say exactly why.

If we had taken the other source without checking, we would have overstated the campus's solar potential by roughly ten per cent.

I should add one honest note. Our own project plan said these two sources should agree within five per cent. They do not. We think the plan's criterion was wrong rather than the data, because the disagreement is explainable and we have a defensible way of choosing. But that is something we would like your view on.

---

## Slide 8 — Part 4: Measuring the roofs, by hand *(~100 sec)*

Part four, and this is the heart of what we have done so far.

*[point to the formula]* Read this line and the whole part is clear. Usable roof equals the roof area, minus what is standing on it, minus a strip around the edge, minus the gaps between rows of panels.

Take those one at a time. *[point to the QGIS image]* We traced every one of the ten roofs by hand over satellite imagery, and marked everything standing on them — water tanks, stair rooms, lift machine rooms, air-conditioning plant. None of that can hold a panel.

Then a clear strip around the edge, because fire access has to be kept.

Then the gaps between rows. Panels cannot be packed tight, because the front row will shadow the row behind it. We calculated that spacing from where the sun actually sits over Delhi on a winter morning. We did not assume it.

One thing we learnt here. The free map outlines we started from were far too generous — and wrong by *different amounts* on different buildings. So no single correction factor would have saved them. There was no shortcut.

And here is the payoff. *[slow down]* The usable share of a roof turns out to range from about one-seventh to about one-half, depending on how cluttered it is. That is the exact variation a blanket "forty per cent" hides. This is why we refused the shortcut on slide two.

It is also our argument for what comes next — this took the better part of a week for ten roofs, and the campus has hundreds.

---

## Slide 9 — The road from here *(~105 sec)*

Five parts remain. The next one is the one that makes all this scale.

*[point to part 5]* Hand-tracing does not scale. So we teach a machine to do the tracing.

We will train a U-Net. That is a neural network built for one specific job: drawing an outline around an object in an image. We start it from an encoder already trained on millions of photographs, so it begins already knowing something about edges and texture instead of starting blank.

It learns on the INRIA dataset — a public set of aerial city photographs where every building is already outlined — and then we run it over our campus imagery.

And our ten hand-traced roofs become the exam paper. The model has to match what we drew by hand before we trust it anywhere else. If it falls short of that, we report it as a result. We are not going to hide it.

*[point down the list]* Part six is shading — build the campus in three dimensions and follow the shadows of buildings and trees across the year. Part seven turns sunlight and shading into units per year, and back-tests that against the plants already running. Part eight is the network study — the one part that genuinely waits on Estate Office data. If it does not arrive, we will build a representative feeder and state every assumption openly.

Part nine pulls it together. *[point to the bottom line]* By the end of the review period: a ranked shortlist of roofs, a campus-wide figure for what they could generate, and the evidence behind both.

---

## Slide 10 — Thank you *(~20 sec)*

That is where we are. Thank you.

We are happy to take questions. Two things we would especially like to discuss: the idle plants, which we would like to raise with the Estate Office, and the plan for the machine learning in part five.

---

## Timing summary

| Slide | Topic | Time |
|---|---|---|
| 1 | Title | 0:55 |
| 2 | Why this project | 1:25 |
| 3 | Three kinds of data | 1:20 |
| 4 | Nine parts | 1:05 |
| 5 | Part 1 — Buildings | 1:30 |
| 6 | Part 2 — Existing plants | 1:50 |
| 7 | Part 3 — Sunlight | 1:35 |
| 8 | Part 4 — Measuring roofs | 1:40 |
| 9 | Road from here | 1:45 |
| 10 | Thank you | 0:20 |
| | **Total** | **~13:25** |

**If you are running short on time:** cut the paragraph on map outlines in slide 8, and the INRIA sentence in slide 9. That saves about a minute without losing an argument.

**If you have extra time:** expand the idle-plants finding on slide 6 — it is the one result with a consequence today, and it invites questions.

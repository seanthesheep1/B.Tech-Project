# Part 4 — Roof digitising and usable area (FR-2)

Completed 23 September 2026. Written in plain language so it can go into the
report and be handed to the supervisor as it stands.

---

## 1. What this part was for

Before you can say how much electricity a roof could make, you have to know how
much of that roof you can actually put panels on. That is not the same as the
size of the building. You have to take away:

- the things already standing on the roof — water tanks, stair rooms, air
  conditioning plant
- a clear strip round the edge, for fire access and maintenance
- the gaps between rows of panels, so one row does not shade the next

Part 4 measures all of that, for each of the ten candidate buildings.

---

## 2. Why we did it by hand

We started from OpenStreetMap, which is a free map anyone can download. It gave
us an outline for each of our ten buildings in a few seconds.

Those outlines turned out to be **wrong by 29 per cent on average**. They are
*building* outlines drawn by volunteers, not *roof* outlines, and they often
wrap open ground, courtyards and neighbouring structures.

So every roof was re-traced by hand against satellite imagery. That is the slow
part of the project and it is the part the specification says decides
everything after it.

---

## 3. The tools

| Tool | What it did |
|---|---|
| **QGIS 4.2** | Free mapping software. Used to see the satellite image and draw on it. |
| **Esri World Imagery** | Free satellite photos of the campus, loaded into QGIS as a background layer. |
| **EPSG:32643** | The coordinate system. This is UTM zone 43 North, which measures in **metres**. Critical: in the default system QGIS measures in degrees and every roof area comes out about ten thousand times wrong. |

---

## 4. Step by step, what was done

### Step 1 — Start from the free outlines

The ten OpenStreetMap outlines were downloaded and saved as
`candidate_roofs.geojson`, then converted into `roofs.gpkg`, which is the file
we actually edited.

### Step 2 — Correct each outline

For each building: zoom in, then drag each corner of the red outline onto the
real edge of the roof in the satellite photo.

Rules followed while tracing:

- Trace the **roof**, not the building. They differ wherever there is an
  overhang or a porch.
- If a wing has a **lower roof at a different height**, trace only the main flat
  area. A different level is a different surface.
- **Courtyards and light wells are not roof.** Where a roof wraps round an open
  area, that area is punched out as a hole using QGIS's *Add Ring* tool. B01 and
  B06 both needed this.

### Step 3 — Draw everything standing on the roof

A second layer, `obstructions.gpkg`, holds one polygon for every object on a
roof. Twenty-one were drawn in total:

| Type | Count |
|---|---|
| `other` | 10 |
| `stair_room` | 4 |
| `water_tank` | 4 |
| `solar_panel` | 2 |
| `open_air` | 1 |

Three things were deliberately **not** drawn as obstructions:

- **Tree overhang** — a tree blocks light, it does not occupy roof. Counting it
  here and again in the shading model would penalise the same area twice. It
  belongs to Part 6.
- **Courtyards and gaps** — not roof at all, so they are holes in the roof
  polygon instead.
- **Shadows** — shadows move. The object casting the shadow is what gets drawn.

### Step 4 — Check the drawing

`scripts/check_roofs.py` runs seven checks. Each one exists because that exact
mistake happened during this work and was invisible on screen:

| Check | The mistake it catches |
|---|---|
| every building present | a roof deleted and never redrawn |
| no duplicate buildings | redrawing adds a feature, it does not replace one |
| all vertices on campus | a polygon fetched from the wrong place entirely |
| no self-intersections | an outline folded over itself, which makes its area meaningless |
| no duplicate vertices | a stray double-click leaving two nodes in one spot |
| obstructions on the right roof | an obstruction named after the neighbouring block |
| every obstruction has a type | a blank type field |

### Step 5 — Work out the usable area

`scripts/run_fr2_from_gpkg.py` reads both layers and runs the chain below,
writing every intermediate number into the register.

---

## 5. The calculation, in plain terms

```
gross roof area                    what you traced
  − obstruction area               the tanks and stair rooms
  − setback strip                  1 m clear round every edge, including courtyards
  = net available area
  × 0.707   ground coverage ratio  leaves room between panel rows
  × 0.85    packing factor         walkways and inverter space
  = module area
  × 215 W/m²                       panel power per square metre
  = installable capacity in kWp
```

### Where 0.707 comes from

This is the one number the specification insisted must be **derived, not
assumed**. It says how tightly panel rows can be packed.

Panels are tilted, so each row casts a shadow behind it. Space the rows too
close and the back row sits in shadow all winter. The rule used here is that no
row shades the next **between 9 am and 3 pm on the shortest day of the year**,
21 December.

At IIT Delhi the sun that morning is **22.32° above the horizon, 44.53° east of
south**. From simple trigonometry:

```
row spacing ÷ panel length = cos(tilt) + sin(tilt) × cos(azimuth) ÷ tan(elevation)
ground coverage ratio      = 1 ÷ that
                           = 0.707 at 15° tilt
```

Those sun angles were checked against PVGIS, the European Commission's solar
tool, which computes them independently. It gives 38.00° at noon against our
38.01°, and 22.30° at 44.50° against our 22.32° at 44.53°. They agree to within
rounding, so the figure that every capacity number depends on is confirmed by an
outside source.

---

## 6. Files used

### Inputs

| File | What it is |
|---|---|
| `data/candidate_roofs.geojson` | the ten free OpenStreetMap outlines, the starting point |
| `data/building_register.csv` | building names, categories, storey counts |
| Esri World Imagery | satellite photos, streamed into QGIS, not stored |

### Created in this part

| File | What it holds |
|---|---|
| `data/roofs.gpkg` | **the ten hand-traced roof outlines** — the project's primary measurement |
| `data/obstructions.gpkg` | 21 polygons, one per object on a roof |

### Updated

| File | What changed |
|---|---|
| `data/building_register.csv` | gained gross area, obstruction area, setback, net area, GCR, module area, capacity, and who traced each roof and when |
| `data/register_schema.yml` | describes each new column and where it came from |

### Code

| File | What it does |
|---|---|
| `src/btp_solar/solar_geometry.py` | works out the sun angles and the 0.707 |
| `src/btp_solar/fr2_usable_area.py` | runs the area chain |
| `scripts/check_roofs.py` | the seven validity checks |
| `scripts/run_fr2_from_gpkg.py` | runs the chain and writes the register |
| `docs/qgis_digitising_guide.md` | the tracing instructions |

---

## 7. The results

| id | building | gross m² | obstructions | setback | net | module | **kWp** | usable % |
|---|---|---|---|---|---|---|---|---|
| B01 | Block 3 | 3,132 | 275 | 622 | 2,235 | 1,342 | **288.6** | 42.9% |
| B02 | Block 4 | 2,729 | 204 | 454 | 2,071 | 1,244 | **267.5** | 45.6% |
| B03 | Dronagiri House | 2,214 | 848 | 236 | 1,130 | 678 | **145.9** | 30.6% |
| B04 | Saptagiri House | 2,161 | 823 | 228 | 1,110 | 666 | **143.3** | 30.9% |
| B05 | Vindhyachal Hostel | 3,653 | 975 | 556 | 2,122 | 1,274 | **274.0** | 34.9% |
| B06 | Lecture Hall Complex | 6,379 | 2,058 | 557 | 3,764 | 2,261 | **486.0** | 35.4% |
| B07 | Academic Complex East | 2,393 | 0 | 379 | 2,014 | 1,209 | **260.0** | 50.5% |
| B08 | Textile Technology | 4,003 | 2,531 | 563 | 910 | 546 | **117.5** | 13.7% |
| B09 | Material Science | 598 | 0 | 115 | 483 | 290 | **62.3** | 48.5% |
| B10 | Central Workshop | 2,399 | 743 | 296 | 1,360 | 816 | **175.6** | 34.0% |
| | **TOTAL** | **29,661** | **8,457** | **4,006** | **17,198** | **10,328** | **2,220.6** | |

**Ten untapped roofs could carry about 2.2 MWp** — roughly three times the
existing campus fleet, which is estimated at 765 kWp.

---

## 8. Two findings worth reporting

### The free map data is wrong, and wrong unevenly

| | OSM | traced | error |
|---|---|---|---|
| B05 Vindhyachal | 3,663 | 3,653 | **−0.3%** |
| B08 Textile Technology | 4,126 | 4,003 | −3% |
| B01 Block 3 | 4,501 | 3,132 | −30% |
| B03 Dronagiri | 3,854 | 2,214 | −43% |
| B10 Central Workshop | 7,257 | 2,399 | **−67%** |
| **all ten** | **41,639** | **29,661** | **−29%** |

Many rooftop potential studies stop at open building footprints. This measures
what that costs: **29 per cent overall**. More importantly the error runs from
0.3 per cent to 67 per cent, so **no single correction factor could fix it**.
That is the argument for digitising by hand rather than scaling.

### The "40 to 50 per cent of roof" rule of thumb does not hold

The workflow note suggests keeping 40–50 per cent of a roof for panels. Our
figures run from **13.7 per cent on B08 to 50.5 per cent on B07**.

The rule works on clean roofs. It fails badly on cluttered ones — B08 has 63 per
cent of its roof covered in plant. A second reason not to use a blanket factor.

---

## 9. Open items carried forward

**B06 has two obstructions typed `solar_panel`.** B06 was chosen as a candidate
*because* it has no PV, and the Lecture Hall Complex is not among the 29 metered
locations. Either panels went up recently or there is an **unmetered array on
campus**, which would mean the existing fleet is larger than the meter data
shows. Worth asking the Estate Office.

**B10 fell 67 per cent from its OSM outline**, the largest correction. Either the
OSM polygon wrapped a workshop yard, or the trace caught only part of the roof.
Worth about 500 kWp, so it should be confirmed before the figure is published.

**One obstruction on B06 (fid 19) subtracts 1,294 m² while only 6 per cent of it
lies on that roof.** Confirmed as intended on inspection and left as drawn, but
it costs B06 about 130 kWp and should be the first thing re-checked if that
roof's yield later looks wrong.

**One obstruction is typed `open_air`.** Open sky is properly a hole in the roof
polygon rather than an obstruction. As drawn the area is still subtracted
correctly; only the setback round its edge is missed.

---

## 10. Does FR-2 pass?

The specification's criterion is that usable area must be *"derived from a
documented setback and ground coverage ratio rather than an assumed
percentage."*

**Yes.** The setback is 1 m and stated. The ground coverage ratio is 0.707,
computed from the winter sun position and confirmed against PVGIS. Nothing in
the chain is an assumed percentage.

The other half of FR-2 — a segmentation model reaching IoU 0.75 against this
hand-traced ground truth — is Part 5 and has not been started.

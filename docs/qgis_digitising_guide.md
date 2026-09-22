# QGIS digitising guide (Part 4)

Two people can work on this at once — split the buildings between you, each
save your own file, and we merge them. Agree who takes which before you start
so nobody digitises the same roof twice.

**What you are producing:** for each of the ten candidate buildings, one
corrected roof outline and one polygon for every object sitting on that roof.
That is all. Everything downstream is computed from these two things.

---

## Before you start

| | |
|---|---|
| Software | QGIS (free, qgis.org) |
| Starting file | `data/candidate_roofs.geojson` — ten outlines from OpenStreetMap |
| Second layer | `data/obstructions_template.geojson` — empty, you draw into it |
| Time | roughly 20–30 minutes per building |

---

## 1. Set the project CRS — do this first

**Project → Properties → CRS**, search `32643`, choose
**WGS 84 / UTM zone 43N**.

This is not a preference, it is the difference between a right answer and a
meaningless one. In the default EPSG:4326 QGIS measures area in *degrees*, and
a roof comes out roughly ten thousand times wrong. If a roof ever reports an
area like `0.0000004`, this is why.

Check it: the bottom-right of the QGIS window should read `EPSG:32643`.

---

## 2. Add the satellite imagery

Browser panel → right-click **XYZ Tiles** → **New Connection**

- Name: `Esri Satellite`
- URL: `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`

Double-click the new entry to add it to the map.

If the imagery looks blurry at high zoom, that is the limit of the free tiles.
Zoom out one step and work there rather than guessing at a blurred edge.

---

## 3. Load the roofs and make them visible

Drag `candidate_roofs.geojson` onto the map.

Right-click the layer → **Properties → Symbology**:

- **Fill style:** No Brush
- **Stroke colour:** bright red
- **Stroke width:** 0.6 mm

You need to see the roof through the polygon. A filled polygon hides exactly
the thing you are trying to trace.

Then **Properties → Labels → Single Labels → Value: `building_id`** so you can
tell B01 from B02 without clicking.

---

## 4. Correct each roof outline

Select the layer, click the **pencil** icon (Toggle Editing), then use the
**Vertex Tool**.

Drag each corner onto the real roof edge. Double-click an edge to add a vertex
where the OSM shape is too simple; select a vertex and press Delete to remove
one where it is too complex.

### What counts as the roof

- Trace the **roof**, not the building. They differ wherever there is an
  overhang, a canopy or a porch.
- If a wing has a **lower roof at a different height**, trace only the main
  flat area. A separate level is a separate surface and cannot share one
  inter-row spacing.
- **Exclude courtyards and light wells.** An OSM polygon often wraps straight
  across them. If sky reaches the ground, it is not roof.
- Sloped sections are out of scope — this study is flat roofs only.

### Record who did it

With the layer in edit mode, open the attribute table and fill in, for each
building you finish:

| Field | Value |
|---|---|
| `verified` | `yes` |
| `digitised_by` | your initials |
| `digitised_date` | `2026-09-22` format |

A polygon with `verified` still `no` is treated as untouched OSM data and will
be reported as such.

**Save often** — the save icon inside the edit toolbar, not just Ctrl+S.

---

## 5. Draw the obstructions

This is the slow part and the part that decides the answer. Load
`data/obstructions_template.geojson`, toggle editing, and use **Add Polygon**.

Draw one polygon around **every object standing on the roof**:

- water tanks
- stair rooms and lift machine rooms
- air conditioning plant, chillers, ducting
- solar water heaters
- vents, masts, any structure

For each polygon fill in:

| Field | Value |
|---|---|
| `building_id` | `B01` … `B10` — must match the register exactly |
| `obstruction_type` | `water_tank`, `stair_room`, `lift_room`, `ac_plant`, `solar_water_heater`, `parapet_structure`, `other` |

### Judgement calls

- **Draw the object's footprint, not its shadow.** Shadows move; Part 6 models
  them separately from the heights.
- **A cluster of small units can be one polygon** if you would not walk between
  them anyway.
- **When unsure, include it.** Overstating obstructions understates capacity,
  which is the safer direction for a feasibility study.
- **Note anything ambiguous** rather than guessing — imagery resolution is a
  named risk in the specification, and two or three roofs are meant to be
  ground-truthed on foot.

---

## 6. Save as a GeoPackage

**Layer → Save As…**

- Format: **GeoPackage**
- File name: `data/roofs.gpkg`
- Layer name: `roofs`
- CRS: **EPSG:32643**

Repeat for the obstructions layer into the *same* `roofs.gpkg`, with layer
name `obstructions`.

GeoPackage rather than GeoJSON because it holds both layers in one file and
stores the CRS properly.

---

## 7. Sanity check before you hand it over

- Does every roof have `verified = yes`?
- Does every obstruction have a `building_id` that exists in the register?
- Do the areas look sane? A 40 m × 30 m block is about 1,200 m². If something
  reads 0.5 or 400,000, the CRS is wrong.
- **B09 Department of Material Science** comes out of OSM at 646 m², which is
  implausibly small for a department block. Check whether only part of it is
  mapped, and extend the outline if so.

---

## What happens next

The area chain runs automatically from your file:

    gross roof area
      − obstruction footprint
      − 1 m setback strip around the edge
      = net available area
      × 0.707   ground coverage ratio, derived from the winter sun
      × 0.85    packing factor for walkways and inverters
      = module area → installable kWp

Those numbers go into `data/building_register.csv`, FR-2 can be signed off, and
Parts 6 and 7 unlock.

The preliminary figure from the uncorrected OSM outlines is **4,335 kWp**. How
far your hand digitising moves that is itself a result worth reporting: it
measures the error in the open-data shortcut that many rooftop studies stop at.

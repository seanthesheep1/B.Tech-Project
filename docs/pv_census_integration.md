# Using the panel detector inside this project

The BTP's scope is unchanged: find the untapped roofs, size them, model their
generation, and test what the network can absorb. The Mask R-CNN panel
detector from the earlier `rooftop-solar-pv` work does not replace any of that.
It is brought in to do one job this project cannot otherwise do well:

> **Measure the capacity of the plants that already exist, from imagery, with
> no meter data involved.**

That matters because every capacity figure for the existing fleet is currently
back-calculated from generation, which makes it useless for validating the
generation model — the FR-4 back-test would pass by construction. A second,
independent route to the same number breaks that circularity. It is roadmap
Step 2b, and the detector does it better than the hand-tracing that step
originally planned.

Two by-products come free: a campus-wide census that shows whether any array is
unmetered, and a real IoU number for FR-2b.

---

## 1. What is reused, and what is rebuilt

| From the old project | Verdict |
|---|---|
| `train/`, `valid/`, `test/` — 976 annotated tiles | **Reuse as is.** The expensive part, already done |
| The trained Mask R-CNN | **Gone.** Both sources are dead - see §7. Retrain from the data, which we hold |
| `city_tile_fetcher.py` — the downloader | **Reuse, adapted.** Good code: async, resumable, correct grid maths |
| `city_tile_plotter.py` | Reference only — its grid logic is the correct one |
| `generate_city_heatmap()` in the notebook | **Do not reuse.** Its tile-to-coordinate map is wrong by a median of 872 m |
| `script.py` — the train/val/test split | Already applied; no need to re-run |
| `Code_Shapefile_Image_gen` | Superseded by the fetcher |

---

## 2. The design decision that matters

The old code recovers a tile's position by **recomputing the grid** in a second
script and trusting the index to line up. It did not line up: the fetcher steps
longitude by `tile/(111320·cos φ)` and increments the index only for tiles it
keeps, while the heatmap function used the latitude step for both axes and
incremented on every grid point. Different grid, different numbering, and every
detection landed a median of 872 m from where it belonged — on a campus 1.3 km
across, that is a different building every time.

**The fix is not a corrected formula. It is to stop recomputing.** Each tile's
position is written down once, when it is downloaded, into a manifest that
travels with the images:

    data/campus_tiles_manifest.csv
    tile_id, centre_lat, centre_lon, min_lat, min_lon, max_lat, max_lon,
    zoom, size_px, metres_per_pixel, fetched_date

Everything downstream reads the manifest. Nothing recomputes a coordinate from
an index. This is the register rule applied to imagery: a number whose
provenance is not written down at the time is a number that gets argued about.

---

## 3. The capacity derivation

The annotations outline **whole array blocks, including the gaps between rows** —
88.9% of them are four-point quadrilaterals drawn around a field of modules,
not around individual panels. So a detection's area is *land* area, not module
area, and converting it to kilowatts needs the ground coverage ratio:

    A_block   detected block area, m², measured in EPSG:32643
    module slope area = A_block × GCR
    capacity kWp      = A_block × GCR × 215 / 1000

This is a pleasing cross-link: **the GCR this project derived from the winter
sun in Part 4 gets reused here, on real arrays**, and if the resulting capacity
agrees with the meter-derived figure then the GCR derivation is partly
corroborated too.

One caution. `config.GCR` of 0.707 is *our design value*, for arrays we would
build. The existing campus arrays were laid out by somebody else and may be
packed tighter or looser. So measure the real row pitch on one or two known
arrays in the imagery and use **that** GCR for the existing fleet, recording it
separately. Assuming our design value would quietly smuggle an assumption into
what is supposed to be an independent check.

Sanity target: a 34 kWp plant should come out around 224 m² of detected block.

---

## 4. Which imagery, and why not Esri

Use **Google Static Maps**, through the adapted fetcher, for the detector only.

The model was trained on Google Static Maps satellite tiles. Running it on
Esri World Imagery is a domain shift — different sensor, processing and colour
balance — and the accepted way to lose accuracy for no reason. Stay in the
distribution the model was trained on.

**Esri stays the source for everything else**: the Part 4 hand-tracing already
done, and the FR-3 shadow validation, which needs an image with a known
acquisition date. Google Static Maps publishes no acquisition date, so it can
never serve FR-3.

The report must say plainly that two imagery sources were used and what each
was used for. Check Google's terms on derived datasets before the final report
cites it.

At zoom 19 and this latitude a tile is **0.2623 m/pixel, 167.9 m across**, and
the campus needs roughly **293 tiles** — a few minutes and a trivial amount of
API credit.

---

## 5. What gets built

Four new pieces, following the existing layout of one module per job.

### `src/btp_solar/imagery.py` — the bridge

Pure geometry, no network and no model, so it is fully unit-testable.

    metres_per_pixel(lat, zoom)
    tile_grid(bounds, zoom, size_px) -> list[TileSpec]
    write_manifest(tiles, path) / read_manifest(path)
    pixel_to_world(tile, x, y)          -> lat, lon
    mask_to_polygon(tile, contour)      -> polygon in EPSG:32643

This is where the 872 m bug is structurally prevented, and where the tests go.

### `scripts/fetch_campus_tiles.py`

`city_tile_fetcher.py` with three changes: bounds taken from `roofs.gpkg` plus
the validation buildings rather than a 1.5 km circle; the manifest written as
tiles are fetched; and the API key read from the environment, never committed.

    uv run python scripts/fetch_campus_tiles.py

Writes `data/campus_tiles/` (git-ignored — licensed imagery) and
`data/campus_tiles_manifest.csv` (committed — it is provenance).

### `src/btp_solar/pv_census.py`

    detect(tiles)                    run the model, return masks per tile
    to_polygons(detections, manifest) georeference into EPSG:32643
    dissolve(polygons)               merge detections split by tile edges
    attribute(polygons, roofs)       assign each array to a building
    capacity_from_area(area, gcr)    the derivation in section 3

`dissolve` is not optional. Campus buildings span **up to six tiles** — Block 3
is 256 m long against a 168 m tile — so one array routinely arrives as several
partial detections that must be merged before its area means anything.

### `scripts/run_pv_census.py`

    uv run python scripts/run_pv_census.py

Writes `data/pv_census.csv`, fills `array_area_m2` and
`capacity_from_imagery_kwp` for the validation rows, and prints the comparison
against `Plant.estimated_kwp`.

---

## 6. What it produces

| Output | What it is for |
|---|---|
| `data/pv_census.csv` | Every array found on campus: location, area, estimated kWp, building if attributable |
| register `array_area_m2`, `capacity_from_imagery_kwp` | Step 2b, the independent capacity for V01–V06 |
| `reports/figures/capacity_two_ways.png` | Imagery-derived against meter-derived capacity, per plant — the validation figure |
| `data/unmetered_candidates.csv` | Arrays found where no meter exists |
| `data/segmentation_iou.csv` | FR-2b: IoU against hand-traced arrays on campus imagery |

---

## 7. Three things to settle first

**The validation buildings have no coordinates.** V01–V06 carry a name and
nothing else — no lat, lon or `osm_id` — so there is currently nothing to point
the detector at. Three are already in `footprints_osm.json`: Bharti School
(way 272261119), Karakoram (way 358870962) and Shivalik (way 358699046, with
four wing polygons). Blocks 1, 5 and 6 need locating, and B01/B02 are Blocks 3
and 4 at OSM ways 44408522 and 44408521, so their neighbours should be close by.

**The trained weights no longer exist anywhere we can reach.** Checked
2026-11-17, both routes dead:

- The Google Drive link in `Resources.txt` returns *"Sorry, the file you have
  requested does not exist."*
- GitHub's LFS API returns **403: "This repository exceeded its LFS budget."**
  `model_final.pth` is only ever a 134-byte pointer, and the object behind it
  cannot be served.

Only the repository's owner can restore either, and that is outside this
project's control.

**What we do hold is better: the training set.** 976 annotated tiles across
`train/valid/test`, 299 MB, with their COCO polygons, plus the training cell in
`detectron2_pipeline.ipynb`. The expensive, irreplaceable part survived; only
the cheap, reproducible part was lost.

So the model is **retrained rather than downloaded**, on a free Colab GPU. That
is the better outcome for this project regardless: a model trained here is
reproducible from data we have, which is the standing rule, and "we trained it"
is a stronger claim in a viva than "we used weights from a link that has since
gone dead".

**One risk to plan for.** The notebook builds detectron2 from source, which was
fine in August 2025 but is fragile against current Colab torch versions. If it
will not build, the fallback is torchvision's own Mask R-CNN
(`maskrcnn_resnet50_fpn`), which needs no exotic install and reads the same
COCO annotations. Budget an afternoon for the first option, and switch rather
than fight it.

**Check it on a plant we know** — Karakoram or Shivalik — before trusting
anything campus-wide. Compare detected block area against the meter-derived
capacity for that one plant, by hand. If they disagree badly, find out why
before running the census.

---

## 8. Effort

| Task | Time |
|---|---|
| Pull weights, locate V01–V06 | 1 hour |
| `imagery.py` with its tests | half a day |
| Adapt the fetcher, fetch 293 tiles | 2 hours |
| `pv_census.py`: inference, dissolve, attribute | half a day |
| Measure the real GCR on two arrays | 1 hour |
| Validate on Karakoram and Shivalik | 2 hours |
| Census run, figures, register, decisions entry | half a day |

**About two and a half days**, against the one day Step 2b was going to cost by
hand — but it covers all 29 plants instead of six, answers the unmetered-array
question, and gives FR-2b a real number.

---

## 9. Where this appears in the report

As **validation and census**, not as the headline.

The project measures untapped roof: 2,220.6 kWp and 3,281 MWh/yr. The detector
is how we checked the existing fleet's capacity without using the meter data we
were trying to validate against, and how we established whether the fleet is
larger than the records show.

For FR-2b, state it plainly: this model segments **installed panels**, not
usable roof area. It gives a measured IoU on campus imagery for the task it was
trained on. Segmenting free roof area is future work, and the hand-traced
polygons from Part 4 remain this project's official measurement of usable area.

Claiming otherwise invites exactly one question in the viva, and there is no
good answer to it.

---

## 10. The retraining run, 2026-11-17

The original weights were unrecoverable: the project's Drive link returned
"file does not exist" and GitHub LFS returned 403. The annotations survived,
so the detector was retrained from them on a Colab T4.

| | |
|---|---|
| Architecture | torchvision `maskrcnn_resnet50_fpn`, COCO-pretrained, two heads replaced |
| Classes | background, solarpv |
| Best validation IoU | **0.740**, at epoch 6 |
| **Test IoU** | **0.707**, on 68 held-out images |
| IoU definition | all instances merged per image, then averaged over images |
| FR-2b threshold | 0.75 — not met, short by 0.043 |

Two things have to be said alongside that number, and both are in the project's
favour rather than against it.

**The threshold is for a different task.** FR-2b's 0.75 was written for
segmenting *usable roof area*. This model segments *installed panels*. Quoting
0.707 against 0.75 compares two different problems; the honest statement is
that the detector scores 0.707 at panel segmentation on campus imagery, and
that usable-area segmentation remains future work. Part 4's hand-traced
polygons are this project's measurement of usable area, and they are not in
question.

**The score is a floor.** On the held-out hostel-block tile the model found the
three arrays that were labelled by hand and two more along the bottom edge that
the annotator had missed, at confidence 0.98. IoU penalises those as false
positives. Where the model is right and the label is wrong, the metric moves
down. The prediction figures should go in the report beside the number for
exactly this reason.

### What the run did not finish

Training was scheduled for 10 epochs and the Colab runtime was recycled during
epoch 7, taking `/content` and the saved weights with it. The checkpoint logic
kept the best epoch rather than the last, so 0.740/0.707 is the score of a
genuine kept model, not of a half-trained one — and the learning rate had
already decayed twice by then (StepLR, step 3, gamma 0.1), with the best epoch
falling immediately after the second decay. The remaining epochs ran at a fiftieth
of the opening rate and would not be expected to move the number much. That is
a reasonable expectation, not a measurement, and the report should not claim
more than that.

**The weights themselves are gone and must be regenerated** before the census
can run. The notebook now downloads the checkpoint the moment training ends
(see `docs/decisions.md`, 2026-11-17), so a second run cannot be lost the same
way. The census is blocked on the Google Maps Static API key in any case, so
the two should be done in one sitting.

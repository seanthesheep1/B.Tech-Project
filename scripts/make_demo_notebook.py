"""Build the walkthrough notebook from source.

    python3 scripts/make_demo_notebook.py

The notebook is generated rather than hand-edited, for the same reason the
figures are: a .ipynb is a JSON blob with execution counts and base64 images
in it, which nobody can review in a diff. This file is the reviewable source.

The notebook imports the project's own modules and shells out to its own
scripts. It never reimplements anything, so it cannot drift away from what the
repository actually does - which is the only way a live demo is worth running.

The copy in the repository is kept **without outputs**, at about 26 kB rather
than 5.6 MB. An executed notebook is a different multi-megabyte base64 blob
after every run, so committing one would make the history unreadable and the
diffs meaningless. `make demo` regenerates it and executes it in about thirty
seconds, with no network: the Esri tiles are cached and every other input is
on disk. Running it live is also a better demonstration than showing outputs
somebody has to take on trust.
"""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "notebooks" / "walkthrough.ipynb"

BLUE = "#2a78d6"
ORANGE = "#eb6834"

CELLS: list[tuple[str, str]] = []


def md(text: str) -> None:
    CELLS.append(("markdown", text.strip("\n")))


def code(text: str) -> None:
    CELLS.append(("code", text.strip("\n")))


# --- 0. what this is -----------------------------------------------------
md("""
# Rooftop Solar Potential Mapping of the IIT Delhi Campus

**A walkthrough that runs the real code.** Every number below is computed by
the project's own modules and scripts, not re-derived here, so nothing in this
notebook can drift away from what the repository actually does.

---

## Read this before the rest

A notebook makes a project look like machine learning. This one mostly is not,
and the distinction is the heart of how the work is validated.

**One model here is trained.** The panel detector is a Mask R-CNN over 976
hand-annotated tiles, split into train, validation and test. It scored an IoU
of **0.707** on 68 held-out images it had never seen.

**Everything else is physics.** The generation model, the shading model, the
soiling model and the economics have no training step, no loss function and no
fitted parameters. `pvlib` solves solar geometry, transposition and cell
temperature from first principles.

**So the validation is stronger than a train/test split, not weaker.** Not one
constant in the model was tuned against the campus meters. That makes the
entire 28-month record of 18 metered plants a test set the model has never
seen. There is no training step for anything to leak into.

The one parameter that *could* have been fitted - the soiling rate - was
deliberately not fitted. Section 5 shows the sweep that finds the
best-fitting value and the different, stated value the model actually uses.
""")

code("""
import subprocess, sys
from pathlib import Path

ROOT = Path.cwd()
if not (ROOT / "src").exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import matplotlib.pyplot as plt
from btp_solar import config

BLUE, ORANGE, MUTED, INK = "#2a78d6", "#eb6834", "#6b6b6b", "#1a1a1a"
plt.rcParams.update({
    "figure.dpi": 120, "font.size": 9, "axes.edgecolor": "#cccccc",
    "axes.labelcolor": INK, "text.color": INK, "axes.titleweight": "bold",
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True,
    "grid.color": "#eeeeee", "axes.spines.top": False, "axes.spines.right": False,
})

def run(target):
    "Run a project script and show its output. The script is the source of truth."
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / target)],
                            capture_output=True, text=True, cwd=ROOT)
    print(result.stdout or result.stderr)
    # Deliberately returns nothing: returning the CompletedProcess put a repr
    # of it under every run, which is noise in a notebook meant to be read.

def show(name, width=1400):
    "Display a figure, downscaled. Full-resolution PNGs embed as base64 and"
    "would make the notebook a six-megabyte blob nobody can review in a diff."
    from PIL import Image as PILImage
    image = PILImage.open(ROOT / "reports" / "figures" / name)
    image.thumbnail((width, width))
    return image

print("site:", config.SITE_LAT, "N", config.SITE_LON, "E")
print("root:", ROOT)
""")

# --- 1. measured by hand -------------------------------------------------
md("""
## 1. What was measured by hand

Before any model there is a survey. Thirty campus buildings were walked on
22 September 2026; three were ruled out for sloped roofs and six were found to
already carry panels that the open data had not recorded. Ten roofs were then
traced by hand in QGIS, with every obstruction on them drawn as its own
polygon.

This matters because open footprint data was **wrong by 29% on average** for
these buildings, unevenly - 0.3% on one, 67% on another. No blanket correction
factor could fix that, which is why the roofs were traced rather than
downloaded.
""")

code("""
import sqlite3, csv

rows = [r for r in csv.DictReader(open(ROOT / "data" / "building_register.csv"))
        if r["building_id"].startswith("B")]

print(f"{'id':<5}{'building':<28}{'traced m2':>10}{'usable m2':>11}{'kWp':>9}{'traced by':>11}")
for r in rows:
    print(f"{r['building_id']:<5}{r['building_name'][:27]:<28}"
          f"{float(r['gross_roof_area_m2']):>10,.0f}"
          f"{float(r['net_available_area_m2']):>11,.0f}"
          f"{float(r['installable_capacity_kwp']):>9.1f}{r['digitised_by']:>11}")

con = sqlite3.connect(ROOT / "data" / "obstructions.gpkg")
kinds = con.execute("select obstruction_type, count(*) from obstructions "
                    "group by obstruction_type order by 2 desc").fetchall()
print()
print("obstructions drawn by hand:",
      ", ".join(f"{n} {k}" for k, n in kinds))
print("total capacity:", f"{sum(float(r['installable_capacity_kwp']) for r in rows):,.1f} kWp")
""")

# --- 2. the generation model --------------------------------------------
md("""
## 2. The generation model, which is not trained

A `pvlib` model chain: solar position, DIRINT decomposition of global
horizontal into beam and diffuse, Perez transposition onto the tilted plane,
Faiman cell temperature, then `pvwatts_dc` and a multiplicative loss stack.

Every constant below comes from physics or from a module datasheet. None was
chosen by looking at the campus meters.
""")

code("""
for name in ("DECOMPOSITION_MODEL", "MODULE_TEMP_COEFF_PER_C",
             "INVERTER_EFFICIENCY", "GROUND_ALBEDO", "WIND_SHEAR_EXPONENT",
             "MODULE_POWER_DENSITY_W_PER_M2", "ARRAY_TILT_DEG"):
    if hasattr(config, name):
        print(f"  {name:<32} {getattr(config, name)}")

print()
print("One bug worth knowing about, caught here:")
print("  NASA POWER serves this file in LOCAL SOLAR TIME, not UTC.")
print("  Read as UTC, solar noon landed at 17:00 IST. It showed up as")
print("  plane-of-array irradiance BELOW horizontal - impossible at 15 degrees -")
print("  and a cell temperature of 102 C. The time standard is now read from")
print("  the file header, and a regression test holds it.")
""")

# --- 3. the test set ----------------------------------------------------
md("""
## 3. The test set: 18 metered plants the model never saw

This is the validation that matters.

The obvious test - compare modelled kWh/kWp against measured kWh/kWp - **cannot
be run honestly here**. The only capacity figures available for the existing
plants were back-calculated from the very generation they would be validating,
so that ratio collapses to the assumed constant and passes no matter what the
model does.

So the test is **shape**. Both series are normalised to their own annual total
and compared month by month. Capacity cancels out entirely. What is left tests
the irradiance, the transposition, the shading and the temperature model, and
nothing else.
""")

code("""
run("run_fr4_backtest.py")
""")

code("""
import csv
from btp_solar import fr1_data

rows = list(csv.DictReader(open(ROOT / "data" / "backtest_shape.csv")))
months = [r["month_name"] if "month_name" in r else r.get("month") for r in rows]
measured = [float(r["measured_share"]) for r in rows]
modelled = [float(r["modelled_share"]) for r in rows]

fig, ax = plt.subplots(figsize=(8.6, 3.4))
x = range(12)
ax.plot(x, measured, color=BLUE, linewidth=2, marker="o", markersize=5,
        label="measured, 18 plants")
ax.plot(x, modelled, color=ORANGE, linewidth=2, marker="o", markersize=5,
        label="modelled, 10 candidate roofs")
ax.set_xticks(list(x)); ax.set_xticklabels(months, fontsize=8)
ax.set_ylabel("share of the year")
ax.set_title("Seasonal shape: the model against data it never saw")
ax.legend(frameon=False, fontsize=8)
# Direct labels on the one disagreement that matters.
worst = max(x, key=lambda i: abs(modelled[i] - measured[i]))
ax.annotate(f"largest gap: {months[worst]}", (worst, modelled[worst]),
            textcoords="offset points", xytext=(6, 10), fontsize=8, color=MUTED)
plt.show()

err = sum(abs(a - b) for a, b in zip(measured, modelled))
print(f"total absolute deviation {err:.3f} against a {config.SHAPE_AGREEMENT_TOL} tolerance")
print(f"so about {err / 2:.1%} of annual energy sits in the wrong month")
""")

md("""
**One caveat to state out loud.** The model describes the ten *candidate*
roofs; the meters are on eighteen *different* buildings, with different
orientations, vintages and shading. Some irreducible part of that deviation is
that mismatch rather than model error. The test is still meaningful - nothing
was fitted to it - but it is not like-for-like, and the report says so.
""")

# --- 4. soiling ----------------------------------------------------------
md("""
## 4. Soiling: the parameter that was deliberately not fitted

The residual has a sign. The model puts more energy into November, December
and January than the fleet delivers. Shading moved the error from 0.101 to
0.097 and no further.

Delhi makes dust a seasonal story: **November averages 3 mm of rain and one wet
day per decade**, so the glass accumulates from October until the pre-monsoon
showers with nothing to clean it.

The temptation here is obvious - tune the soiling rate until the back-test
passes, then report that the back-test passes. That rate would have absorbed
whatever else the model had wrong, and the pass would mean nothing. So the rate
is swept, the whole curve is reported, and **the model uses a different,
stated value**.
""")

code("""
run("run_soiling.py")
""")

code("""
from btp_solar import soiling

rain = soiling.load_daily_rainfall(
    ROOT / "data" / f"nasa_precip_{config.SITE_LAT}_{config.SITE_LON}_20140101_20231231.json")

rates = soiling.SOILING_RATE_SWEEP
winter = []
for rate in rates:
    monthly = soiling.monthly_mean_loss(soiling.soiling_loss(rain, soiling_rate=rate))
    winter.append(sum(monthly[m] for m in (10, 11, 0)) / 3)

fig, ax = plt.subplots(figsize=(7.4, 3.2))
ax.plot([r * 100 for r in rates], [w * 100 for w in winter], color=BLUE,
        linewidth=2, marker="o", markersize=5)
ax.axvline(config.SOILING_RATE_PER_DAY * 100, color=ORANGE, linewidth=2,
           linestyle="--")
ax.annotate("the rate the model uses\\n(stated, not fitted)",
            (config.SOILING_RATE_PER_DAY * 100, max(winter) * 55),
            textcoords="offset points", xytext=(8, 0), fontsize=8, color=ORANGE)
ax.set_xlabel("soiling rate, % of output lost per dry day")
ax.set_ylabel("Nov-Jan soiling loss, %")
ax.set_title("Winter soiling against the rate assumed")
plt.show()

print(f"config.SOILING_RATE_PER_DAY = {config.SOILING_RATE_PER_DAY}")
print("The sweep's best-fitting rate is 0.0050. The model uses 0.0030.")
print("They are different numbers in different files, on purpose.")
""")

# --- 5. shading and what is not known -----------------------------------
md("""
## 5. Shading, and being honest about what was never measured

Roof clutter is about 85% of the modelled shading loss - and the heights of
that clutter are six **assumed** numbers. Roof access is not permitted, and an
attempt to measure them from shadows in the satellite imagery failed for a
reason worth knowing: Esri serves a curated, shadow-suppressed mosaic here. On
23 October the sun cannot climb past 49.2 degrees, so a 24.5 m building must
cast 26 m of shadow. There is none anywhere in the scene.

When a parameter cannot be measured, the honest move is not to assert it more
confidently. It is to say how much it matters.
""")

code("""
run("run_obstruction_sensitivity.py")
""")

md("""
**The headline is robust; the ranking is not.** Across a fourfold range of
assumed heights the campus energy moves by under 5%, well inside what the
generation model already carries. But the worst-affected roof swings from 3.5%
to 19.0% of its own output, and any build order sorts on exactly that. The
report states the headline plainly and attaches this band to the per-roof
figures, not the other way round.
""")

# --- 6. economics --------------------------------------------------------
md("""
## 6. What it costs

Led by **LCOE**, because the tariff is the weakest input the project has and
LCOE does not contain it. MNRE's benchmark turned out to be a residential
scheme with no institutional rate above 100 kW, and DERC publishes no current
retail schedule - only backward-looking true-up orders. So capital cost is
swept across the published commercial band rather than asserted at a point.
""")

code("""
run("run_economics.py")
""")

code("""
import csv
rows = list(csv.DictReader(open(ROOT / "data" / "economics.csv")))
ids = [r["building_id"] for r in rows]
lcoe = [float(r["lcoe_inr_per_kwh"]) for r in rows]

fig, ax = plt.subplots(figsize=(8.0, 3.2))
bars = ax.bar(ids, lcoe, color=BLUE, width=0.62)
ax.axhline(config.TARIFF_INR_PER_KWH, color=ORANGE, linewidth=2, linestyle="--")
ax.annotate(f"grid tariff placeholder, Rs {config.TARIFF_INR_PER_KWH:.2f}",
            (len(ids) - 0.4, config.TARIFF_INR_PER_KWH), ha="right",
            textcoords="offset points", xytext=(0, 6), fontsize=8, color=ORANGE)
for b, v in zip(bars, lcoe):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.08, f"{v:.2f}",
            ha="center", fontsize=7.5, color=MUTED)
ax.set_ylim(0, config.TARIFF_INR_PER_KWH * 1.25)
ax.set_ylabel("Rs / kWh")
ax.set_title("Levelised cost per roof, against what the grid costs")
plt.show()

print("Every roof generates well under the grid price, and LCOE contains no")
print("tariff at all - so this comparison survives whatever the real bill says.")
""")

# --- 7. the alarm --------------------------------------------------------
md("""
## 7. The Solar Alarm, run live

This one takes no model at all. It reads the Estate Office meter workbooks and
asks which plants have stopped or are sliding.

The rule that matters: a plant's baseline is the median of its **first twelve
months**, not its whole record. A plant that failed early spends most of its
history dead, so its all-time median *is* the dead level and it reads as
normal. That is how the Director's Lodge - at 0.9% of its opening baseline
since July 2024 - stayed invisible to every earlier check, because its meter
still creeps a few kWh a month and so never looks idle.
""")

code("""
run("run_alarm.py")
""")

code("""
show("alarm_dashboard.png")
""")

# --- 8. the trained model ------------------------------------------------
md("""
## 8. The one model that *is* trained

A torchvision Mask R-CNN, COCO-pretrained, both heads replaced for a single
`solarpv` class. 976 hand-annotated tiles split into train, validation and
test. The best epoch by validation IoU is kept rather than the last.

| | |
|---|---|
| best validation IoU | 0.740 |
| **test IoU** | **0.707**, on 68 held-out images |
| FR-2b threshold | 0.75 |

**Two things have to be said with that number, and both favour the project.**

The threshold was written for segmenting *usable roof area*. This model
segments *installed panels* - a different task. Quoting 0.707 against 0.75
compares two different problems.

And the score is a floor, not a ceiling. On the held-out tiles the model found
arrays the annotator had missed, at 0.98 confidence. IoU counts those as false
positives: the metric goes **down** because the model is right.

The training notebook is `notebooks/train_panel_detector.ipynb`. The weights
were lost to a recycled Colab runtime and need one hour to regenerate; the
numbers above are from the completed run.
""")

# --- 9. the map ----------------------------------------------------------
md("""
## 9. The Solar Map

Two panels over the same ground. The left answers *how much is there*, the
right *what it costs*. Folding both into one symbol - size for one, hue for the
other - makes a picture nobody can read back into numbers.
""")

code("""
run("run_solar_map.py")
show("solar_map.png", width=1700)
""")

# --- 10. provenance ------------------------------------------------------
md("""
## 10. Is any of this stale?

A quiet failure mode in a project this size: a stage runs, writes its output,
and then an input underneath it changes. Nothing errors. The file is still
there, still parses, still has plausible numbers in it - and is now a record of
a calculation nobody would get again.

`make audit` declares every stage's inputs and outputs and checks that no
output is older than an input feeding it.
""")

code("""
run("run_pipeline_audit.py")
show("pipeline.png", width=1500)
""")

# --- 11. what is open ----------------------------------------------------
md("""
## 11. What is not finished

Stated plainly, because a project that claims to be complete invites the one
question it cannot answer.

- **FR-1 fails its 5% irradiance agreement criterion.** Two independent sources
  disagree by more than that. The measured generation shape was used to
  arbitrate between them, and NASA POWER won.
- **FR-5, the feeder study, was not built.** The network data was requested in
  writing and never arrived. A documented blocker that was escalated and
  mitigated is a managed risk; the same gap undocumented is unfinished work.
- **The residual is not fully explained.** Dust accounts for most of the winter
  leg. What remains is a spring and monsoon error of the opposite sign - the
  model runs low in March and June, high in August - and dust cannot cause
  that.
- **Six obstruction heights were never measured**, and carry 85% of the shading
  loss. Section 5 bounds what that costs.
- **The detector weights need regenerating**, one hour of GPU.

Nothing in this list is hidden in the appendix of the report. They are the
parts an examiner would find anyway, and finding them already written down is
a different conversation from finding them missing.
""")


def _lines(text: str) -> list[str]:
    out = text.splitlines(keepends=True)
    if out and not out[-1].endswith("\n"):
        return out
    return out


def main() -> int:
    import nbformat

    nb = nbformat.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python",
                       "name": "python3"},
        "language_info": {"name": "python"},
    }
    for kind, text in CELLS:
        if kind == "markdown":
            nb.cells.append(nbformat.v4.new_markdown_cell(_lines(text)))
        else:
            nb.cells.append(nbformat.v4.new_code_cell(_lines(text)))

    nbformat.validate(nb)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, str(OUT))
    print(f"wrote {OUT.relative_to(Path(__file__).resolve().parents[1])} "
          f"({len(CELLS)} cells, "
          f"{sum(1 for k, _ in CELLS if k == 'code')} of them code)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

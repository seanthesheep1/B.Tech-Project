"""What goes into each stage, what comes out, and whether it is still true.

    make audit

A project this size accumulates a quiet failure mode: a stage runs, writes its
output, and then an input underneath it changes. Nothing errors. The file is
still there, still parses, still has plausible numbers in it - and is now a
record of a calculation nobody would get again. Two of today's bugs were that
shape: the economics read shading from a monthly working file instead of the
register, and read soiling back from a sweep's output.

So the pipeline is declared here explicitly rather than inferred, and the audit
checks three things per stage:

  * every input exists
  * every output exists
  * no output is older than an input that feeds it

The last is the one worth having. It is the difference between "the file is
there" and "the file is current", and only the second is provenance.

Staleness is reported at its **root**, not splashed downstream. If the register
changes, `economics` goes stale while `map` does not, because the map's own
output is still newer than the economics file it was drawn from. Re-run
economics and the map goes stale next. Running the audit repeatedly therefore
walks the dependency chain one stage at a time and converges on a clean tree,
which is more useful than lighting up eight stages at once and leaving the
reader to work out which one to fix first.

Writes ``reports/figures/pipeline.png``.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from btp_solar import config  # noqa: E402

FIGURE = ROOT / "reports" / "figures" / "pipeline.png"

NASA = f"nasa_power_{config.SITE_LAT}_{config.SITE_LON}_20140101_20231231.json"
PRECIP = f"nasa_precip_{config.SITE_LAT}_{config.SITE_LON}_20140101_20231231.json"
PVGIS = f"pvgis_tmy_{config.SITE_LAT}_{config.SITE_LON}.json"

# Status palette: reserved roles, never reused for anything else. Each is
# paired with a mark and a word, because a status colour must never be the only
# thing carrying the meaning.
GOOD, WARNING, CRITICAL = "#0ca30c", "#fab219", "#d03b3b"
MARKS = {"ok": ("ok", GOOD), "stale": ("stale", WARNING), "missing": ("missing", CRITICAL)}

INK, MUTED, RULE, SURFACE = "#1a1a1a", "#6b6b6b", "#d8d8d8", "#ffffff"


@dataclass
class Stage:
    target: str
    title: str
    inputs: list[str]
    outputs: list[str]
    external: str = ""
    notes: str = ""
    status: str = field(default="ok", init=False)
    reasons: list[str] = field(default_factory=list, init=False)


PIPELINE = [
    Stage("fr1", "Fetch the weather and the footprints",
          [], [NASA, PVGIS, "footprints_osm.json"],
          external="NASA POWER, PVGIS, OpenStreetMap",
          notes="two irradiance sources so one can arbitrate the other"),
    Stage("meters", "Read the Estate Office workbooks",
          ["Solar reading jan-24 to dec-24.xlsm",
           "Solar meter Report-2025 & 2026.xlsx"],
          ["campus_solar_monthly.csv"],
          notes="the Institute's own data; the only ground truth we have"),
    Stage("fr2", "Usable area from the traced roofs",
          ["roofs.gpkg", "obstructions.gpkg"],
          ["building_register.csv"],
          external="hand-traced in QGIS",
          notes="the project's primary measurement"),
    Stage("fr3", "Shading: neighbours, parapets, clutter",
          ["roofs.gpkg", "obstructions.gpkg", NASA],
          ["shading_factors.csv", "roof_horizons.npz"],
          notes="writes the shading columns of the register"),
    Stage("fr4", "Model the generation",
          [NASA, PVGIS, "roof_horizons.npz", "building_register.csv"],
          ["generation_results.csv", "generation_monthly.csv",
           "generation_variants.csv"],
          notes="pvlib chain; writes the yield columns of the register"),
    Stage("backtest", "Back-test the seasonal shape",
          ["generation_monthly.csv", "campus_solar_monthly.csv"],
          ["backtest_shape.csv"],
          notes="normalised shapes, so capacity cancels and cannot flatter it"),
    Stage("soiling", "Dust, and what rain removes",
          [PRECIP, "generation_monthly.csv", "campus_solar_monthly.csv"],
          ["soiling_monthly.csv"],
          notes="the sweep is a diagnostic, not an input to anything else"),
    Stage("economics", "Cost, LCOE and payback",
          ["building_register.csv", "generation_monthly.csv", PRECIP],
          ["economics.csv"],
          notes="shading from the register, soiling from a stated rate"),
    Stage("alarm", "Which plants have stopped",
          ["campus_solar_monthly.csv"],
          ["plant_health.csv", "../reports/figures/alarm_dashboard.png"],
          notes="runs on the measured fleet alone; no model involved"),
    Stage("map", "The Solar Map",
          ["roofs.gpkg", "economics.csv", "imagery_provenance.json"],
          ["../reports/figures/solar_map.png"],
          external="Esri World Imagery tiles",
          notes="same scene the roofs were traced against"),
]


def resolve(name: str) -> Path:
    return (config.DATA / name).resolve()


def stamp(path: Path) -> float | None:
    return path.stat().st_mtime if path.exists() else None


def audit() -> list[Stage]:
    for stage in PIPELINE:
        newest_input = None
        for name in stage.inputs:
            path = resolve(name)
            when = stamp(path)
            if when is None:
                stage.status = "missing"
                stage.reasons.append(f"input missing: {name}")
            elif newest_input is None or when > newest_input:
                newest_input = when

        for name in stage.outputs:
            path = resolve(name)
            when = stamp(path)
            if when is None:
                if stage.status != "missing":
                    stage.status = "missing"
                stage.reasons.append(f"output missing: {name}")
            elif newest_input is not None and when < newest_input:
                if stage.status == "ok":
                    stage.status = "stale"
                stage.reasons.append(f"stale: {name} predates an input")
    return PIPELINE


def print_report(stages: list[Stage]) -> None:
    print("Each stage, what it consumes and what it produces.\n")
    for stage in stages:
        word, _ = MARKS[stage.status]
        print(f"  [{word:>7}]  make {stage.target:<12} {stage.title}")
        if stage.external:
            print(f"               from outside: {stage.external}")
        for name in stage.inputs:
            mark = "ok" if resolve(name).exists() else "MISSING"
            print(f"               in   {name:<52} {mark}")
        for name in stage.outputs:
            path = resolve(name)
            if path.exists():
                age = datetime.fromtimestamp(path.stat().st_mtime).strftime("%d %b %H:%M")
                size = path.stat().st_size
                mark = f"{size:>9,} B  {age}"
            else:
                mark = "MISSING"
            print(f"               out  {name:<52} {mark}")
        for reason in stage.reasons:
            print(f"               !! {reason}")
        print()

    counts = {k: sum(1 for s in stages if s.status == k) for k in MARKS}
    print(f"  {counts['ok']} stages current, {counts['stale']} stale, "
          f"{counts['missing']} incomplete, of {len(stages)}")
    if counts["stale"]:
        print("  A stale stage still has a file. It is a record of a calculation")
        print("  nobody would get again. Re-run it before quoting its numbers.")


def draw(stages: list[Stage]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    # Row height follows the deepest column in that row. A fixed height let a
    # four-input stage run its last filename straight through the note beneath
    # it - the kind of defect no check finds and one look does.
    LINE = 0.21
    depths = [max(len(s.inputs) or 1, len(s.outputs)) for s in stages]
    heights = [max(1.0, 0.56 + LINE * d) for d in depths]
    fig_h = 1.9 + sum(heights)
    fig, ax = plt.subplots(figsize=(14.5, fig_h))
    fig.patch.set_facecolor(SURFACE)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, fig_h)
    ax.axis("off")

    x_in, x_stage, x_out = 2, 36, 66
    w_in, w_stage, w_out = 31, 27, 32

    for x, label in ((x_in, "I N P U T S"), (x_stage, "S T A G E"),
                     (x_out, "O U T P U T S")):
        ax.text(x, fig_h - 1.05, label, fontsize=8, fontweight="bold",
                color=MUTED)
    ax.plot([x_in, 98], [fig_h - 1.25, fig_h - 1.25], color=RULE, linewidth=1)

    def box(x, y, w, h, face, edge, lw=1.0):
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.12,rounding_size=0.18",
            facecolor=face, edgecolor=edge, linewidth=lw, zorder=2))

    cursor = fig_h - 2.1
    for i, stage in enumerate(stages):
        y = cursor
        cursor -= heights[i]
        word, colour = MARKS[stage.status]

        # inputs
        lines = stage.inputs or ["(fetched from outside)"]
        for j, name in enumerate(lines):
            present = (not stage.inputs) or resolve(name).exists()
            ax.text(x_in + 0.4, y + 0.52 - j * 0.21,
                    ("- " if present else "x ") + Path(name).name[:50],
                    fontsize=6.4, color=INK if present else CRITICAL,
                    va="center", family="monospace")

        # stage
        box(x_stage, y + 0.04, w_stage, 0.62, "#f4f6f9", colour, 1.6)
        ax.text(x_stage + 0.7, y + 0.46, f"make {stage.target}", fontsize=8,
                fontweight="bold", color=INK, va="center", zorder=3)
        ax.text(x_stage + 0.7, y + 0.21, stage.title[:44], fontsize=7,
                color=MUTED, va="center", zorder=3)
        # status: a word and a dot, never the colour alone
        ax.scatter([x_stage + w_stage - 1.0], [y + 0.46], s=36, color=colour,
                   zorder=4)
        ax.text(x_stage + w_stage - 1.9, y + 0.46, word, fontsize=6.6,
                color=colour, ha="right", va="center", fontweight="bold",
                zorder=4)

        # outputs
        for j, name in enumerate(stage.outputs):
            present = resolve(name).exists()
            ax.text(x_out + 0.4, y + 0.52 - j * 0.21,
                    ("- " if present else "x ") + Path(name).name[:50],
                    fontsize=6.4, color=INK if present else CRITICAL,
                    va="center", family="monospace")

        for x0, x1 in ((x_in + w_in, x_stage), (x_stage + w_stage, x_out)):
            ax.add_patch(FancyArrowPatch(
                (x0 + 0.4, y + 0.35), (x1 - 0.4, y + 0.35),
                arrowstyle="-|>", mutation_scale=9, color=RULE, linewidth=1.0,
                zorder=1))

        # The note sits below whichever column ran deepest, not at a fixed offset.
        depth = max(len(stage.inputs) or 1, len(stage.outputs))
        note_y = y + 0.52 - depth * LINE - 0.04
        if stage.notes:
            ax.text(x_in + 0.4, note_y, stage.notes, fontsize=6.4,
                    color=MUTED, style="italic", va="center")
        ax.plot([x_in, 98], [note_y - 0.16, note_y - 0.16],
                color="#eeeeee", linewidth=0.8)

    counts = {k: sum(1 for s in stages if s.status == k) for k in MARKS}
    # Headings drawn in axes space, so bbox_inches="tight" keeps them.
    ax.text(x_in, fig_h - 0.28, "The pipeline: what each stage consumes and produces",
            fontsize=14, fontweight="bold", color=INK, va="center")
    ax.text(x_in, fig_h - 0.66,
            f"{counts['ok']} stages current, {counts['stale']} stale, "
            f"{counts['missing']} incomplete. A stage is stale when an output is "
            f"older than an input that feeds it: the file exists, and is no longer "
            f"a calculation anyone would get again.",
            fontsize=8.5, color=MUTED, va="center")
    ax.text(x_in, 0.28,
            "Status is carried by a word and a dot together, never by colour alone. "
            "Generated by scripts/run_pipeline_audit.py",
            fontsize=7, color=MUTED, va="center")

    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=200, facecolor=SURFACE, bbox_inches="tight")
    print(f"\n  wrote {FIGURE.relative_to(ROOT)}")


def main() -> int:
    stages = audit()
    print_report(stages)
    draw(stages)
    return 1 if any(s.status == "missing" for s in stages) else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Draw the nine-part work breakdown for the mid-term report.

One figure, regenerated from this file so the report never carries a diagram
whose source has been lost. Status comes from docs/project_plan.md section 3.

    python3 scripts/make_parts_diagram.py
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch

OUT = Path("reports/figures/nine_parts.png")

INK = "#000000"
RULE = "#808080"

DONE = {"fc": "#DCEDE4", "ec": "#2E7D5B", "tc": "#14452F"}
TODO = {"fc": "#EFEFEF", "ec": "#555555", "tc": "#000000"}
BLOCKED = {"fc": "#F7E3DE", "ec": "#A2452F", "tc": "#6E2718"}

STAGES = [
    (
        "A · Scope and data",
        [
            (1, "Choose the buildings", "Campus survey; 10 candidates fixed", DONE, "complete"),
            (2, "Read the meter data", "Existing fleet characterised; FR-4 input", DONE, "complete"),
            (3, "Collect sunshine data", "Irradiance and footprints · FR-1", DONE, "complete"),
        ],
    ),
    (
        "B · Measuring the roofs",
        [
            (4, "Measure the roofs", "Hand digitising; usable area · FR-2", DONE, "complete"),
            (5, "Machine learning", "Segmentation to scale past 10 roofs · FR-2", TODO, "to do"),
        ],
    ),
    (
        "C · Modelling the output",
        [
            (6, "Shadows", "DSM and hourly shading factors · FR-3", TODO, "to do"),
            (7, "Calculate electricity", "pvlib chain, back-tested · FR-4", TODO, "to do"),
        ],
    ),
    (
        "D · Impact and synthesis",
        [
            (8, "Grid impact", "OpenDSS feeder study · FR-5", BLOCKED, "blocked"),
            (9, "Report and costs", "Ranking, payback, emissions", TODO, "to do"),
        ],
    ),
]

STAGE_X = [13.0, 37.5, 62.0, 86.5]
STAGE_W, STAGE_H, STAGE_Y = 21.0, 6.0, 80.0
LEAF_W, LEAF_H = 18.0, 11.0
LEAF_TOP, LEAF_STEP = 68.5, 13.0


def box(ax, cx, cy, w, h, fc, ec, lw=1.3, r=0.6):
    ax.add_patch(
        FancyBboxPatch(
            (cx - w / 2, cy - h / 2),
            w,
            h,
            boxstyle=f"round,pad=0,rounding_size={r}",
            fc=fc,
            ec=ec,
            lw=lw,
            zorder=2,
        )
    )


def main() -> Path:
    fig, ax = plt.subplots(figsize=(13.2, 7.0), dpi=200)
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 100)
    ax.set_ylim(31, 100)
    ax.axis("off")

    # root
    box(ax, 50, 93, 56, 7, "#000000", "#000000", r=0.8)
    ax.text(50, 94.4, "ROOFTOP SOLAR POTENTIAL MAPPING OF THE IIT DELHI CAMPUS",
            ha="center", va="center", color="white", fontsize=11, fontweight="bold")
    ax.text(50, 91.4, "B.Tech Project · nine work parts · four complete at mid-term",
            ha="center", va="center", color="#CCCCCC", fontsize=8.5)

    # bus from root to the four stages
    ax.plot([50, 50], [89.5, 86.5], color=RULE, lw=1.2, zorder=1)
    ax.plot([STAGE_X[0], STAGE_X[-1]], [86.5, 86.5], color=RULE, lw=1.2, zorder=1)

    for sx, (stage_name, leaves) in zip(STAGE_X, STAGES):
        ax.plot([sx, sx], [86.5, STAGE_Y + STAGE_H / 2], color=RULE, lw=1.2, zorder=1)
        box(ax, sx, STAGE_Y, STAGE_W, STAGE_H, "#E4E4E4", "#000000", lw=1.2)
        ax.text(sx, STAGE_Y, stage_name, ha="center", va="center",
                color="#000000", fontsize=9.5, fontweight="bold")

        spine_x = sx - 9.5
        leaf_cx = sx + 1.5
        ys = [LEAF_TOP - i * LEAF_STEP for i in range(len(leaves))]
        ax.plot([spine_x, spine_x], [STAGE_Y - STAGE_H / 2, ys[-1]],
                color=RULE, lw=1.1, zorder=1)

        for y, (num, name, desc, style, status) in zip(ys, leaves):
            ax.plot([spine_x, leaf_cx - LEAF_W / 2], [y, y], color=RULE, lw=1.1, zorder=1)
            box(ax, leaf_cx, y, LEAF_W, LEAF_H, style["fc"], style["ec"], lw=1.4)
            left = leaf_cx - LEAF_W / 2 + 1.0
            right = leaf_cx + LEAF_W / 2 - 1.0
            ax.text(left, y + 3.7, f"PART {num}", ha="left", va="center",
                    color=style["tc"], fontsize=7.5, fontweight="bold")
            ax.text(right, y + 3.7, status.upper(), ha="right", va="center",
                    color=style["ec"], fontsize=6.8, fontweight="bold")
            ax.text(left, y + 0.9, name, ha="left", va="center",
                    color=style["tc"], fontsize=9.2, fontweight="bold")
            ax.text(left, y - 2.6, textwrap.fill(desc, 30), ha="left", va="center",
                    color=style["tc"], fontsize=7.2, linespacing=1.45)

    legend = [
        Line2D([], [], marker="s", ls="", ms=11, mfc=DONE["fc"], mec=DONE["ec"],
               mew=1.4, label="Complete — reported here"),
        Line2D([], [], marker="s", ls="", ms=11, mfc=TODO["fc"], mec=TODO["ec"],
               mew=1.4, label="Remaining work"),
        Line2D([], [], marker="s", ls="", ms=11, mfc=BLOCKED["fc"], mec=BLOCKED["ec"],
               mew=1.4, label="Blocked on Estate Office data (D16, D17, D18)"),
    ]
    ax.legend(handles=legend, loc="lower center", bbox_to_anchor=(0.5, -0.035),
              ncol=3, frameon=False, fontsize=8.6, handletextpad=0.7,
              columnspacing=2.4, labelcolor=INK)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight", facecolor="white", pad_inches=0.25)
    plt.close(fig)
    return OUT


if __name__ == "__main__":
    print(f"wrote {main()}")

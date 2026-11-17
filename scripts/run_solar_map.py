"""The Solar Map: ten candidate roofs, drawn on the campus.

    make map

Two panels over the same ground, not one map doing two jobs. The left panel
answers *how much is there* and the right answers *what it costs*. They are
different measures on different scales, and folding them into a single symbol -
size for one, hue for the other - produces a picture nobody can read back into
numbers.

Each panel is a **sequential** encoding: one hue, light to dark, darker meaning
more. On the left more is better. On the right more is worse. Nothing in the
colour says which, so the subtitles say it instead, because a reader should
never have to infer the direction of a ramp.

Every roof is labelled with its own identifier, so identity never depends on
colour. The imagery is the same Esri scene the roofs were traced against - see
``data/imagery_provenance.json`` - which is why the outlines sit where they do.
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from btp_solar import basemap, config  # noqa: E402
from run_fr3_shading import rings_of  # noqa: E402

ROOFS = config.DATA / "roofs.gpkg"
ECONOMICS = config.DATA / "economics.csv"
FIGURE = ROOT / "reports" / "figures" / "solar_map.png"

ZOOM = 18          # 0.52 m/pixel here: enough for a page, a quarter the tiles
MARGIN_M = 115.0   # enough that an edge roof's label stays on the page

# The reference sequential ramp, blue, light to dark - but starting at step
# 250, not step 100. The full 100-700 range is for a continuous field where the
# lightest step means "near zero" and may recede into the surface. Ten discrete
# roofs are not a field: every one of them has to be visible as a mark against
# a photograph, so the ramp starts at the lightest step that still clears 2:1
# on a light surface.
BLUE = ["#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
        "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]

INK = "#1a1a1a"
MUTED = "#6b6b6b"
SURFACE = "#ffffff"


def load_roofs() -> dict[str, list]:
    to_lonlat, _ = basemap.utm_transformers()
    out = {}
    with sqlite3.connect(ROOFS) as conn:
        for bid, geom in conn.execute("select building_id, geom from roofs"):
            out[bid] = [to_lonlat.transform(x, y) for x, y in rings_of(geom)[0]]
    return out


def load_economics() -> dict[str, dict]:
    with ECONOMICS.open(encoding="utf-8") as handle:
        return {r["building_id"]: r for r in csv.DictReader(handle)}


def ramp(value: float, low: float, high: float) -> str:
    """Pick a step from the blue ramp. Linear in the value, not in rank."""
    if high <= low:
        return BLUE[len(BLUE) // 2]
    position = (value - low) / (high - low)
    index = int(round(position * (len(BLUE) - 1)))
    return BLUE[max(0, min(len(BLUE) - 1, index))]


def ink_for(hex_colour: str) -> str:
    """Label ink that stays legible as the fill darkens."""
    r, g, b = (int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#ffffff" if luminance < 0.5 else INK


def draw(ax, mosaic, roofs, values, low, high, title, subtitle, unit, fmt):
    import numpy as np
    from matplotlib.patches import Polygon as MplPolygon
    import matplotlib.patheffects as path_effects

    halo = [path_effects.withStroke(linewidth=2.6, foreground=SURFACE)]
    dark_halo = [path_effects.withStroke(linewidth=2.6, foreground="#11223a")]

    ax.imshow(np.asarray(mosaic.image))
    ax.set_xlim(0, mosaic.image.width)
    ax.set_ylim(mosaic.image.height, 0)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    for bid, ring in sorted(roofs.items()):
        pixels = [mosaic.lonlat_to_pixel(lo, la) for lo, la in ring]
        fill = ramp(values[bid], low, high)
        # A surface ring, not a dark one: it separates the fill from a busy
        # photograph without adding a second ink to read.
        ax.add_patch(MplPolygon(pixels, closed=True, facecolor=fill,
                                edgecolor=SURFACE, linewidth=2.0, alpha=0.88,
                                zorder=3))
        cx = sum(p[0] for p in pixels) / len(pixels)
        cy = sum(p[1] for p in pixels) / len(pixels)

        # A long thin strip has no room for two stacked lines inside it, so the
        # label goes above the shape instead of across it. Measuring the minor
        # axis rather than the area is what distinguishes B01's 140 m ribbon
        # from B09's compact block.
        width = max(p[0] for p in pixels) - min(p[0] for p in pixels)
        height = max(p[1] for p in pixels) - min(p[1] for p in pixels)
        thin = min(width, height) < 26

        ink = ink_for(fill)
        effects = dark_halo if ink == "#ffffff" else halo
        if thin:
            ty = min(p[1] for p in pixels) - 11
            ax.text(cx, ty, f"{bid}  {fmt(values[bid])}", ha="center",
                    va="bottom", fontsize=8, fontweight="bold", color=INK,
                    zorder=4, path_effects=halo)
        else:
            ax.text(cx, cy - 7, bid, ha="center", va="center", fontsize=8.5,
                    fontweight="bold", color=ink, zorder=4,
                    path_effects=effects)
            ax.text(cx, cy + 7, fmt(values[bid]), ha="center", va="center",
                    fontsize=7.5, color=ink, zorder=4, path_effects=effects)

    # Title and subtitle both go above the panel. Hanging the subtitle below
    # the axes put it outside tight_layout's rect, where it was clipped.
    ax.set_title(f"{title}\n", fontsize=12, fontweight="bold", color=INK,
                 loc="left", pad=22)
    ax.text(0, 1.004, subtitle, transform=ax.transAxes, fontsize=8.5,
            color=MUTED, va="bottom", ha="left")

    # Scale bar, in whole metres, sized from the mosaic's own resolution.
    metres = 200.0
    px = metres / mosaic.metres_per_pixel()
    x0, y0 = 18, mosaic.image.height - 26
    ax.plot([x0, x0 + px], [y0, y0], color=SURFACE, linewidth=4.5, zorder=5,
            solid_capstyle="butt")
    ax.plot([x0, x0 + px], [y0, y0], color=INK, linewidth=2.0, zorder=6,
            solid_capstyle="butt")
    ax.text(x0 + px / 2, y0 - 8, f"{metres:.0f} m", ha="center", va="bottom",
            fontsize=7.5, color=INK, zorder=6,
            bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.2, alpha=0.85))

    # North. The mosaic is Web Mercator, so up is north by construction.
    ax.annotate("N", xy=(mosaic.image.width - 26, 42),
                xytext=(mosaic.image.width - 26, 78),
                ha="center", va="center", fontsize=9, color=INK, zorder=6,
                arrowprops=dict(arrowstyle="-|>", color=INK, linewidth=1.4),
                bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.0, alpha=0.85))

    # The ramp, as a strip with its ends labelled. A continuous colourbar would
    # imply a precision the ten discrete roofs do not have.
    bar_w, bar_h = 150, 9
    bx, by = mosaic.image.width - bar_w - 18, mosaic.image.height - 34
    for i, colour in enumerate(BLUE):
        ax.add_patch(plt_rect(bx + i * bar_w / len(BLUE), by,
                              bar_w / len(BLUE) + 0.6, bar_h, colour))
    ax.text(bx, by - 5, fmt(low), ha="left", va="bottom", fontsize=7.5,
            color=INK, zorder=7, path_effects=halo)
    # The unit lives in the subtitle, not here. Spelled out above the bar it
    # ran the full 150 px of it and sat on top of the low-end number, which
    # simply vanished.
    ax.text(bx + bar_w, by - 5, fmt(high), ha="right", va="bottom",
            fontsize=7.5, color=INK, zorder=7, path_effects=halo)


def plt_rect(x, y, w, h, colour):
    from matplotlib.patches import Rectangle

    return Rectangle((x, y), w, h, facecolor=colour, edgecolor="none", zorder=6)


def main() -> int:
    if not ROOFS.exists():
        print("missing roofs.gpkg")
        return 1
    if not ECONOMICS.exists():
        print("missing economics.csv; run `make economics` first")
        return 1

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    roofs = load_roofs()
    econ = load_economics()
    missing = set(roofs) - set(econ)
    if missing:
        print(f"no economics for {sorted(missing)}; run `make economics`")
        return 1

    lons = [p[0] for ring in roofs.values() for p in ring]
    lats = [p[1] for ring in roofs.values() for p in ring]
    dlat = MARGIN_M / 111_320.0
    dlon = MARGIN_M / (111_320.0 * 0.878)
    mosaic = basemap.mosaic(min(lons) - dlon, min(lats) - dlat,
                            max(lons) + dlon, max(lats) + dlat, zoom=ZOOM)
    print(f"campus mosaic {mosaic.image.size} at "
          f"{mosaic.metres_per_pixel():.2f} m/pixel, zoom {ZOOM}")

    energy = {b: float(econ[b]["first_year_kwh"]) / 1000.0 for b in roofs}
    lcoe = {b: float(econ[b]["lcoe_inr_per_kwh"]) for b in roofs}

    fig, axes = plt.subplots(1, 2, figsize=(15.5, 8.2))
    fig.patch.set_facecolor(SURFACE)

    draw(axes[0], mosaic, roofs, energy, min(energy.values()), max(energy.values()),
         "What is there",
         "First-year generation, MWh/yr. Darker is more energy.",
         "MWh/yr", lambda v: f"{v:.0f}")
    draw(axes[1], mosaic, roofs, lcoe, min(lcoe.values()), max(lcoe.values()),
         "What it costs",
         "Levelised cost, Rs/kWh. Darker is more expensive.",
         "Rs/kWh", lambda v: f"{v:.2f}")

    fig.suptitle("Rooftop solar potential, IIT Delhi campus",
                 fontsize=15, fontweight="bold", color=INK, x=0.012, ha="left",
                 y=0.985)
    total_kwp = sum(float(econ[b]["capacity_kwp"]) for b in roofs)
    fig.text(0.012, 0.945,
             f"{len(roofs)} candidate roofs, {total_kwp:,.0f} kWp, "
             f"{sum(energy.values()):,.0f} MWh/yr after shading and soiling. "
             f"Costs are indicative: the tariff is a placeholder and capital "
             f"cost is a swept midpoint.",
             fontsize=9, color=MUTED, ha="left")
    fig.text(0.012, 0.012,
             "Imagery: Esri World Imagery, captured 2025-10-23, the same scene "
             "the roofs were traced against.",
             fontsize=7.5, color=MUTED, ha="left")

    fig.tight_layout(rect=(0, 0.03, 1, 0.925))
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE, dpi=200, facecolor=SURFACE)
    print(f"wrote {FIGURE.relative_to(ROOT)}")

    print(f"\n  {'id':<5}{'MWh/yr':>9}{'Rs/kWh':>9}")
    for bid in sorted(roofs):
        print(f"  {bid:<5}{energy[bid]:>9.0f}{lcoe[bid]:>9.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

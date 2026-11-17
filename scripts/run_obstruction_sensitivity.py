"""How much does FR-3 depend on the obstruction heights nobody measured?

    make sensitivity

``config.OBSTRUCTION_HEIGHTS_M`` is six assumed numbers, and roof clutter is
about 85% of the modelled shading loss, so those six carry more of FR-3 than
anything else in the project. The attempt to measure them from shadows failed
for a reason that is a property of the imagery and not of the method - see
``docs/decisions.md``, 2026-11-17 - and no roof visit is permitted.

When a parameter cannot be measured, the honest move is not to assert it more
confidently. It is to say how much it matters. This runs the shading model with
the heights scaled across the range a person could defend and reports what the
campus answer does. If the answer barely moves, the assumption is cheap and the
report can say so. If it moves a lot, that is the headline limitation and the
report must say *that* instead.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402

from btp_solar import config, fr4_generation, register  # noqa: E402
from btp_solar import fr3_shading  # noqa: E402
import run_fr3_shading as fr3  # noqa: E402

#: The band a surveyor would accept without going up to look. A water tank on a
#: stand is not 1 m and is not 6 m; everything in between has been seen.
SCALES = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)


def main() -> int:
    if not fr3.ROOFS.exists() or not fr3.NASA.exists():
        print("missing inputs; earlier steps must run first")
        return 1

    roofs = fr3.load_roofs()
    obstructions = fr3.load_obstructions()
    neighbours, _ = fr3.neighbour_casters({r["osm_id"] for r in roofs.values()})
    for bid, roof in roofs.items():
        neighbours.append(fr3_shading.Caster(bid, roof["height_m"], roof["outer"]))

    weather = fr4_generation.load_nasa_hourly(fr3.NASA)
    chain = fr4_generation.build_site_chain(weather)
    from pvlib import location

    site = location.Location(
        config.SITE_LAT, config.SITE_LON, config.SITE_TZ, config.SITE_ELEVATION_M
    )
    solpos = site.get_solarposition(weather.index)
    elevations = solpos["apparent_elevation"].to_numpy()
    azimuths = solpos["azimuth"].to_numpy()
    poa_direct = chain.poa_direct.to_numpy()
    poa_diffuse = chain.poa_diffuse.to_numpy()

    rows = {r["building_id"]: r for r in register.load()}
    baseline_heights = dict(config.OBSTRUCTION_HEIGHTS_M)

    print("Obstruction heights are assumed, not measured. This is what the")
    print("campus shading answer does when they move.\n")
    print("assumed heights, by scale:")
    for scale in SCALES:
        shown = ", ".join(
            f"{k} {v * scale:.1f}" for k, v in baseline_heights.items() if v > 0
        )
        print(f"  x{scale:<5} {shown}")

    print(f"\n{'scale':>6} {'campus loss':>12} {'vs base':>9} "
          f"{'worst roof':>11} {'energy MWh':>11} {'vs base':>9}")

    base_loss = None
    base_energy = None
    for scale in SCALES:
        scaled = {k: v * scale for k, v in baseline_heights.items()}
        config.OBSTRUCTION_HEIGHTS_M.clear()
        config.OBSTRUCTION_HEIGHTS_M.update(scaled)

        weighted_num = 0.0
        weighted_den = 0.0
        losses = {}
        energy = 0.0
        for bid in sorted(roofs):
            result = fr3.shading_for(
                roofs[bid], obstructions.get(bid, []),
                [c for c in neighbours if c.name != bid],
                poa_direct, poa_diffuse, azimuths, elevations,
            )
            kwp = float(rows[bid]["installable_capacity_kwp"])
            losses[bid] = result["annual"]
            weighted_num += result["annual"] * kwp
            weighted_den += kwp
            # unshaded annual yield scaled by what survives the shading
            energy += kwp * float(rows[bid]["specific_yield"]) * (
                1.0 - result["annual"]
            ) / 1000.0

        campus = weighted_num / weighted_den
        worst = max(losses, key=losses.get)
        if base_loss is None:
            base_loss, base_energy = campus, energy
            d_loss, d_energy = "base", "base"
        else:
            d_loss = f"{(campus - base_loss) * 100:+.2f} pp"
            d_energy = f"{energy - base_energy:+.0f}"
        print(f"{scale:>6.2f} {campus:>11.2%} {d_loss:>9} "
              f"{worst + ' ' + format(losses[worst], '.1%'):>11} "
              f"{energy:>11,.0f} {d_energy:>9}")

    config.OBSTRUCTION_HEIGHTS_M.clear()
    config.OBSTRUCTION_HEIGHTS_M.update(baseline_heights)

    print("\nRead this as the width of the band FR-3's answer sits in, given")
    print("that the heights behind it were never measured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

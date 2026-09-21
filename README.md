# Rooftop Solar Potential Mapping of the IIT Delhi Campus

B.Tech project, Department of Electrical Engineering, IIT Delhi.
Tejas Suresh Kamble (2023EE10974), supervised by Prof. Yashasvi.
Review period 18 August to 31 October 2026.

The specification this code implements is in
[`docs/BTP_Functional_Specification_Rooftop_Solar_IITD.pdf`](docs/BTP_Functional_Specification_Rooftop_Solar_IITD.pdf);
the week-by-week plan is in
[`docs/Rooftop_Solar_BTP_10_Week_Workflow.pdf`](docs/Rooftop_Solar_BTP_10_Week_Workflow.pdf).

## Getting started

```bash
make setup     # uv sync --extra dev, pinned to Python 3.12
make test      # the geometry derivations and the acceptance criteria
make register  # print the building register with its provenance
```

QGIS is installed separately (`brew install --cask qgis`); it is not a Python
dependency of this package. The UMEP plugin is added from inside QGIS and is
needed from week 6.

## Layout

```
data/raw/          downloaded inputs, never edited, never committed
data/interim/      intermediate products, reproducible from raw
data/processed/    building_register.csv  <- the audit trail, committed
docs/              specification, workflow, and the decision log
qgis/              campus.qgz and layer styles
src/btp_solar/     one module per functional requirement
scripts/           entry points, one per FR
tests/             the derivations and every acceptance criterion
reports/           figures and the written report
```

## The five modules

| Ref | Module | Code | Acceptance criterion |
|-----|--------|------|----------------------|
| FR-1 | Data acquisition | `fr1_data.py` | PVGIS and NASA POWER agree on annual GHI within 5% |
| FR-2 | Usable area | `fr2_usable_area.py`, `solar_geometry.py` | Segmentation IoU ≥ 0.75; area from a derived GCR, not an assumed percentage |
| FR-3 | Shading | `fr3_shading.py` | Modelled shadow within 15% of one measured in dated imagery |
| FR-4 | Generation | `fr4_generation.py` | Specific yield 1300–1600 kWh/kWp/yr, within 10% of PVGIS |
| FR-5 | Feeder impact | `fr5_feeder.py` | Base case within 15% of billed consumption |

Every criterion above is a callable in `src/btp_solar/acceptance.py`, so a
module is signed off by running a check rather than by asserting in prose.

## The two standing rules

**One register.** `data/processed/building_register.csv` has one row per
building and one column per computed number. Every column is described in
`register_schema.yml` with the module that produced it and the formula behind
it; a test fails if a column appears without one. It is CSV rather than a
spreadsheet binary so that a changed number shows up as a readable diff.

**Commit weekly.** The repository exists from week 1 precisely because "we lost
the file" is a real thing that happens in October.

## The usable-area derivation

The specification rules out assuming a fixed usable percentage, so the ground
coverage ratio is derived from the winter sun. A row of modules of slope length
L at tilt β stands L·sin β tall and casts a shadow L·sin β / tan α along the
solar azimuth; the component normal to the rows sets the pitch:

    pitch / L = cos β + sin β · cos γ / tan α
    GCR       = L / pitch

evaluated at the design sun position — by default 09:00 solar time on the
winter solstice, the conventional start of the six-hour window kept clear. At
IIT Delhi that is an elevation of 22.3° at 44.5° east of south, giving GCR
0.707 at 15° tilt. Applied to a 2100 m² roof with 8% under plant, the chain
yields about 50% of the gross roof as module area and 225 kWp — consistent
with the 40–50% rule of thumb, but with every step traceable.

Change the criterion to `winter_noon` in `config.py` to see what the laxer
design point buys, and record the choice in `docs/decisions.md`.

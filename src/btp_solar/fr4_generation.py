"""FR-4: generation estimation.

Week 7. A pvlib model chain per building: Perez transposition onto the tilted
plane, an explicit cell-temperature model because Delhi summers cost real
yield, and the itemised loss stack from config rather than a single lumped
derate.
"""

from __future__ import annotations

from . import config


def total_loss_fraction(losses: dict[str, float] | None = None) -> float:
    """Combine the itemised losses multiplicatively, not by addition.

    Adding percentages overstates the loss; each stage acts on what the
    previous one passed through.
    """
    losses = losses if losses is not None else config.LOSSES
    remaining = 1.0
    for value in losses.values():
        if not 0.0 <= value < 1.0:
            raise ValueError(f"loss fraction {value} is outside [0, 1)")
        remaining *= 1.0 - value
    return 1.0 - remaining


def specific_yield(annual_energy_kwh: float, capacity_kwp: float) -> float:
    """Annual energy per installed kilowatt, the number the FR-4 band applies to."""
    if capacity_kwp <= 0:
        raise ValueError("capacity must be positive")
    return annual_energy_kwh / capacity_kwp


def capacity_factor(annual_energy_kwh: float, capacity_kwp: float) -> float:
    return specific_yield(annual_energy_kwh, capacity_kwp) / 8766.0


def run_model_chain(building_id: str, weather, capacity_kwp: float):  # pragma: no cover
    """Full pvlib chain for one roof. Implement in week 7.

    Sketch, to be filled in against the pvlib ModelChain API:
      1. Location(SITE_LAT, SITE_LON, SITE_TZ, SITE_ELEVATION_M)
      2. solar position over the TMY index
      3. Perez transposition to tilt=MODULE_TILT_DEG, azimuth=MODULE_AZIMUTH_DEG
      4. apply the FR-3 hourly shading factor to the beam component
      5. cell temperature, SAPM open-rack or the Faiman model
      6. DC power, inverter model, then total_loss_fraction()
    """
    raise NotImplementedError("Week 7: see the docstring for the intended chain")

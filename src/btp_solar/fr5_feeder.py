"""FR-5: feeder impact study.

Weeks 9 and 10. One representative 11 kV feeder in OpenDSS, annual time-series
power flow with and without the modelled generation, evaluating steady-state
voltage rise, reverse power flow at the distribution transformers, feeder
losses and hosting capacity.

If the Estate Office data does not arrive, the specification's mitigation
applies: build a representative feeder from transformer ratings and distances
measured off the campus map, and declare every assumption in
docs/decisions.md. The `synthetic` flag exists so that the report can state
plainly which case was run.
"""

from __future__ import annotations

from dataclasses import dataclass

# Limits to assess against, per the specification: CEA regulations and
# IEEE 1547 practice. Confirm the applicable CEA clause before the final report.
VOLTAGE_UPPER_PU = 1.05
VOLTAGE_LOWER_PU = 0.95


@dataclass
class FeederCase:
    name: str
    synthetic: bool
    note: str = ""


def voltage_within_limits(voltages_pu: list[float]) -> bool:
    """True when every bus stays inside the statutory band."""
    return all(VOLTAGE_LOWER_PU <= v <= VOLTAGE_UPPER_PU for v in voltages_pu)


def reverse_power_hours(transformer_kw: list[float]) -> int:
    """Hours in the year with power flowing back through the transformer.

    The expected worst case is a summer Sunday with the hostels empty and
    generation at its peak.
    """
    return sum(1 for kw in transformer_kw if kw < 0)


def hosting_capacity(case: FeederCase):  # pragma: no cover
    """Largest total PV capacity before a limit is crossed. Implement in week 10.

    Bisect on installed capacity, running the annual time series at each step
    and stopping at the first violation of the voltage band, the transformer
    reverse-flow rating or the thermal limit. This number is the headline
    result of the project.
    """
    raise NotImplementedError("Week 10: bisection on capacity, see the docstring")

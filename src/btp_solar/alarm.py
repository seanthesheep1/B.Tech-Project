"""The solar alarm: which plants have stopped, and which are quietly sliding.

Four of the campus plants had not generated for between six and twenty-three
months when this project opened the workbooks. A reading was written down every
single day throughout. Nobody had ever subtracted one day from the next.

That is the whole idea here. The Institute already collects the data that would
have caught it; what was missing was something that reads it. This module is
that something, and it answers three questions:

    stopped          has the register stopped moving?
    underperforming  is this plant producing much less than it used to,
                     relative to the rest of the fleet?
    not being read   are the readings themselves missing or stuck?

The third is kept separate on purpose. A plant that has failed and a meter that
nobody is reading look identical in a spreadsheet and need completely different
people to fix them.

**Why "share of the fleet" and not kWh per kWp.** The obvious test - energy
divided by capacity - cannot be used here, because capacity is not in the
Estate Office workbooks and is itself back-calculated from the same generation
(docs/decisions.md, 2026-09-22). Dividing by it would compare a plant against
itself. Instead each plant's share of the fleet's output for that month is
compared against its own usual share. Weather cancels, because a dull month
pulls everyone down together, and capacity never appears.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from . import config

STOPPED = "stopped"
COLLAPSED = "collapsed"
UNDERPERFORMING = "underperforming"
NOT_READ = "not_read"
HEALTHY = "healthy"
TOO_NEW = "too_new"

SEVERITY = {STOPPED: "high", COLLAPSED: "high", UNDERPERFORMING: "medium",
            NOT_READ: "low", HEALTHY: "none", TOO_NEW: "none"}


@dataclass(frozen=True)
class Finding:
    """One plant's health, as of a given month."""

    meter: int
    location: str
    status: str
    detail: str
    months_idle: int = 0
    lost_kwh: float = 0.0
    share_now: float | None = None
    share_usual: float | None = None
    first_flagged: str | None = None

    @property
    def severity(self) -> str:
        return SEVERITY[self.status]

    @property
    def lost_inr(self) -> float:
        """Indicative only: rests on an estimated capacity and a provisional tariff."""
        return self.lost_kwh * config.TARIFF_INR_PER_KWH

    def __str__(self) -> str:
        return f"[{self.severity.upper():<6}] {self.location[:30]:<32} {self.detail}"


def months_in(plants) -> list[str]:
    """Every month any plant reported, oldest first."""
    return sorted({m for p in plants.values() for m in p.monthly_kwh})


def fleet_shares(plants) -> dict[str, dict[int, float]]:
    """Each plant's share of the fleet's output, month by month.

    Only plants that generated in a month take part in that month's split, so a
    plant that is dead does not dilute the rest. The consequence is worth
    stating: when plants leave the fleet - as the hostel meters do through
    2025 - the remaining shares rise, which makes this test *less* likely to
    cry wolf and slightly *more* likely to miss a real decline.
    """
    shares: dict[str, dict[int, float]] = {}
    for month in months_in(plants):
        live = {meter: p.monthly_kwh.get(month, 0.0) for meter, p in plants.items()}
        live = {meter: kwh for meter, kwh in live.items() if kwh > 0}
        total = sum(live.values())
        if total <= 0:
            continue
        shares[month] = {meter: kwh / total for meter, kwh in live.items()}
    return shares


def assess_plant(meter: int, plant, shares: dict[str, dict[int, float]],
                 as_of: str) -> Finding:
    """Decide one plant's status as of a month. The rules are applied in order
    of how much they matter: a stopped plant is not also reported as slipping."""
    history = [m for m in sorted(plant.monthly_kwh) if m <= as_of]
    live = [m for m in history if plant.monthly_kwh[m] > 0]

    if not live:
        return Finding(meter, plant.location, NOT_READ,
                       "no generation anywhere in the record")

    idle = plant.months_idle(as_of)
    if idle >= config.OUTAGE_MONTHS:
        lost = plant.lost_kwh(as_of)
        return Finding(
            meter, plant.location, STOPPED,
            f"last generated {live[-1]}, {idle} months ago; "
            f"about {lost / 1000:.0f} MWh not produced since",
            months_idle=idle, lost_kwh=lost, first_flagged=_first_stopped(plant, as_of),
        )

    seen = [m for m in history if m in shares and meter in shares[m]]
    if len(seen) < config.MIN_MONTHS_FOR_BASELINE:
        return Finding(meter, plant.location, TOO_NEW,
                       f"only {len(seen)} months of record; no baseline yet")

    usual = baseline_share(meter, seen, shares)
    recent = seen[-config.UNDERPERFORMANCE_MONTHS:]
    now = shares[recent[-1]][meter]

    if len(recent) == config.UNDERPERFORMANCE_MONTHS:
        # Collapsed first: a plant at a twentieth of what it was has not
        # merely slipped, and calling that "underperforming" would bury it
        # below the genuinely dead ones in any list sorted by severity.
        if all(shares[m][meter] < usual * config.COLLAPSE_RATIO for m in recent):
            idle_like = sum(1 for m in seen[::-1]
                            if shares[m][meter] < usual * config.COLLAPSE_RATIO)
            return Finding(
                meter, plant.location, COLLAPSED,
                f"down to {now / usual:.1%} of its baseline for {idle_like} months; "
                f"the meter still creeps, so it never reads as idle",
                months_idle=idle_like,
                share_now=now, share_usual=usual,
                first_flagged=_first_below(meter, seen, shares, config.COLLAPSE_RATIO),
            )
        if all(shares[m][meter] < usual * config.UNDERPERFORMANCE_RATIO for m in recent):
            return Finding(
                meter, plant.location, UNDERPERFORMING,
                f"share of the fleet is {now / usual:.0%} of its baseline, "
                f"for {len(recent)} months running",
                share_now=now, share_usual=usual,
                first_flagged=_first_below(meter, seen, shares,
                                           config.UNDERPERFORMANCE_RATIO),
            )

    if idle > 0:
        return Finding(meter, plant.location, NOT_READ,
                       f"nothing recorded for {idle} month(s), "
                       f"short of the {config.OUTAGE_MONTHS}-month outage rule",
                       months_idle=idle)

    return Finding(meter, plant.location, HEALTHY, "generating as usual")


def baseline_share(meter: int, seen: list[str], shares) -> float:
    """What this plant's share looked like when the record opened.

    Deliberately not the median over the whole record. A plant that failed
    early spends most of its history dead, so its all-time median *is* the
    dead level and it would be measured against its own corpse - which is how
    Director's Lodge, running at half a per cent of its old output since July
    2024, first came out as a mild 41 per cent case.
    """
    window = seen[:config.BASELINE_MONTHS]
    return statistics.median(shares[m][meter] for m in window)


def _first_below(meter: int, seen: list[str], shares, ratio: float) -> str | None:
    """First month a sustained drop below ``ratio`` of baseline was visible,
    judged only on what was known by then."""
    for i in range(config.MIN_MONTHS_FOR_BASELINE, len(seen)):
        window = seen[max(0, i - config.UNDERPERFORMANCE_MONTHS + 1):i + 1]
        if len(window) < config.UNDERPERFORMANCE_MONTHS:
            continue
        usual = baseline_share(meter, seen[:i + 1], shares)
        if all(shares[m][meter] < usual * ratio for m in window):
            return seen[i]
    return None


def _first_stopped(plant, as_of: str) -> str | None:
    """The month this plant would first have been called stopped."""
    for month in sorted(plant.monthly_kwh):
        if month > as_of:
            break
        if plant.months_idle(month) >= config.OUTAGE_MONTHS:
            return month
    return None


def assess(plants, as_of: str) -> list[Finding]:
    """Every plant's health as of a month, worst first."""
    shares = fleet_shares(plants)
    findings = [assess_plant(meter, plant, shares, as_of)
                for meter, plant in plants.items()]
    order = {"high": 0, "medium": 1, "low": 2, "none": 3}
    return sorted(findings, key=lambda f: (order[f.severity], -f.lost_kwh, f.location))

"""The solar alarm.

Every rule here exists because of something real in the campus data, and each
test names it. The hard requirement is not sensitivity but restraint: a monitor
that cries wolf gets ignored, and then the next dead plant goes unnoticed for
two years exactly as before.
"""

from __future__ import annotations

import datetime as dt

import pytest

from btp_solar import alarm, campus_meters, config


def plant(meter: int, location: str, monthly: dict[str, float]):
    """A Plant whose months come out as the given kWh.

    ``monthly_kwh`` is the register's rise across a month, so each month needs
    two readings whose difference is the energy wanted.
    """
    readings: dict[dt.date, float] = {}
    register = 1000.0
    for month in sorted(monthly):
        year, mon = int(month[:4]), int(month[5:])
        readings[dt.date(year, mon, 1)] = register
        register += monthly[month]
        readings[dt.date(year, mon, 28)] = register
    return campus_meters.Plant(meter=meter, location=location,
                               meter_factor=1.0, readings=readings)


def months(start_year: int, count: int) -> list[str]:
    out, year, mon = [], start_year, 1
    for _ in range(count):
        out.append(f"{year}-{mon:02d}")
        mon += 1
        if mon > 12:
            mon, year = 1, year + 1
    return out


def fleet(series: dict[str, dict[str, float]]):
    return {i: plant(i, name, monthly)
            for i, (name, monthly) in enumerate(series.items(), start=1)}


STEADY = {m: 1000.0 for m in months(2024, 24)}


# --- restraint ------------------------------------------------------------

def test_a_healthy_fleet_raises_nothing():
    plants = fleet({"A": STEADY, "B": STEADY, "C": STEADY})
    findings = alarm.assess(plants, "2025-12")
    assert all(f.status == alarm.HEALTHY for f in findings), \
        [str(f) for f in findings if f.status != alarm.HEALTHY]


def test_a_bad_month_for_everyone_is_weather_not_a_fault():
    """July is the monsoon. Every plant drops together, and none is broken."""
    monsoon = dict(STEADY)
    for m in ("2024-07", "2024-08", "2025-07", "2025-08"):
        monsoon[m] = 300.0
    plants = fleet({"A": monsoon, "B": dict(monsoon), "C": dict(monsoon)})
    findings = alarm.assess(plants, "2025-08")
    assert all(f.status == alarm.HEALTHY for f in findings)


def test_one_poor_month_is_not_an_alarm():
    """A single odd reading must not fire; the rule needs it sustained."""
    dip = dict(STEADY)
    dip["2025-12"] = 100.0
    plants = fleet({"A": dip, "B": dict(STEADY), "C": dict(STEADY)})
    findings = {f.location: f for f in alarm.assess(plants, "2025-12")}
    assert findings["A"].status == alarm.HEALTHY


def test_a_plant_with_too_little_history_is_not_judged():
    plants = fleet({"A": {m: 1000.0 for m in months(2024, 3)},
                    "B": dict(STEADY), "C": dict(STEADY)})
    findings = {f.location: f for f in alarm.assess(plants, "2024-03")}
    assert findings["A"].status == alarm.TOO_NEW


# --- the three faults -----------------------------------------------------

def test_a_register_that_stops_moving_is_an_outage():
    dead = dict(STEADY)
    for m in months(2024, 24)[12:]:
        dead[m] = 0.0
    plants = fleet({"A": dead, "B": dict(STEADY), "C": dict(STEADY)})
    findings = {f.location: f for f in alarm.assess(plants, "2025-12")}
    assert findings["A"].status == alarm.STOPPED
    assert findings["A"].severity == "high"
    assert findings["A"].months_idle >= config.OUTAGE_MONTHS


def test_a_sustained_slide_is_caught():
    sliding = dict(STEADY)
    for m in months(2024, 24)[-4:]:
        sliding[m] = 300.0        # 30% of its old share
    plants = fleet({"A": sliding, "B": dict(STEADY), "C": dict(STEADY)})
    findings = {f.location: f for f in alarm.assess(plants, "2025-12")}
    assert findings["A"].status == alarm.UNDERPERFORMING
    assert findings["B"].status == alarm.HEALTHY


def test_a_dead_plant_whose_meter_still_creeps_is_not_called_mild():
    """Director's Lodge: 1,500 kWh a month until July 2024, then 8 to 10 kWh
    ever since. It never reads as idle, because the register keeps inching
    forward, and it is not merely underperforming either."""
    creeping = dict(STEADY)
    for m in months(2024, 24)[6:]:
        creeping[m] = 9.0
    plants = fleet({"A": creeping, "B": dict(STEADY), "C": dict(STEADY)})
    findings = {f.location: f for f in alarm.assess(plants, "2025-12")}

    assert findings["A"].status == alarm.COLLAPSED
    assert findings["A"].severity == "high", "a dead plant must not rank below a live one"
    assert findings["A"].share_now < 0.05 * findings["A"].share_usual


def test_the_baseline_is_the_opening_window_not_the_all_time_median():
    """The bug this rule was rewritten for.

    A plant that failed early spends most of the record dead, so its all-time
    median IS the dead level. Measured against that it looks fine, which is
    how a plant running at half a per cent of its old output first came out as
    a mild 41 per cent case.
    """
    creeping = dict(STEADY)
    for m in months(2024, 24)[6:]:
        creeping[m] = 9.0
    plants = fleet({"A": creeping, "B": dict(STEADY), "C": dict(STEADY)})
    shares = alarm.fleet_shares(plants)
    seen = [m for m in sorted(shares) if 1 in shares[m]]

    opening = alarm.baseline_share(1, seen, shares)
    all_time = sorted(shares[m][1] for m in seen)[len(seen) // 2]

    assert opening > all_time * 10, (
        "the baseline must reflect the plant when it worked, not its long decline"
    )


# --- the properties that keep it honest -----------------------------------

def test_capacity_is_never_needed():
    """Plant capacity is back-calculated from generation, so any rule using it
    would be judging a plant against itself. Nothing here may require it."""
    sliding = dict(STEADY)
    for m in months(2024, 24)[-4:]:
        sliding[m] = 300.0
    plants = fleet({"A": sliding, "B": dict(STEADY), "C": dict(STEADY)})

    for p in plants.values():
        assert p.estimated_kwp is not None      # it exists here...
    findings = {f.location: f for f in alarm.assess(plants, "2025-12")}
    assert findings["A"].status == alarm.UNDERPERFORMING

    # ...and the verdict must not change when it is unavailable.
    original = config.MIN_MONTHS_FOR_CAPACITY
    try:
        config.MIN_MONTHS_FOR_CAPACITY = 10_000   # forces estimated_kwp to None
        assert all(p.estimated_kwp is None for p in plants.values())
        again = {f.location: f for f in alarm.assess(plants, "2025-12")}
        assert again["A"].status == alarm.UNDERPERFORMING
    finally:
        config.MIN_MONTHS_FOR_CAPACITY = original


def test_scaling_the_whole_fleet_changes_nothing():
    """Shares are dimensionless, so the units of the meter cannot matter."""
    small = fleet({"A": STEADY, "B": dict(STEADY), "C": dict(STEADY)})
    big = fleet({"A": {m: v * 37 for m, v in STEADY.items()},
                 "B": {m: v * 37 for m, v in STEADY.items()},
                 "C": {m: v * 37 for m, v in STEADY.items()}})
    assert ([f.status for f in alarm.assess(small, "2025-12")]
            == [f.status for f in alarm.assess(big, "2025-12")])


def test_the_first_flagged_month_does_not_peek_at_the_future():
    """The back-test claim - 'this would have fired in November 2024' - is only
    worth making if it was decided on what was known in November 2024."""
    dead = dict(STEADY)
    for m in months(2024, 24)[12:]:
        dead[m] = 0.0
    plants = fleet({"A": dead, "B": dict(STEADY), "C": dict(STEADY)})

    flagged = {f.location: f for f in alarm.assess(plants, "2025-12")}["A"].first_flagged
    assert flagged is not None

    # Asked at that month, with nothing later in view, it must already fire.
    at_the_time = {f.location: f for f in alarm.assess(plants, flagged)}["A"]
    assert at_the_time.status in (alarm.STOPPED, alarm.COLLAPSED)


def test_severity_orders_the_report_worst_first():
    findings = [alarm.Finding(1, "x", alarm.HEALTHY, ""),
                alarm.Finding(2, "y", alarm.STOPPED, ""),
                alarm.Finding(3, "z", alarm.UNDERPERFORMING, "")]
    assert [f.severity for f in findings] == ["none", "high", "medium"]


def test_rupees_are_derived_from_the_declared_tariff():
    finding = alarm.Finding(1, "x", alarm.STOPPED, "", lost_kwh=1000.0)
    assert finding.lost_inr == pytest.approx(1000.0 * config.TARIFF_INR_PER_KWH)


def test_every_status_can_be_drawn():
    """The figure once hardcoded the list of statuses, so adding one broke it -
    and the breakage was swallowed by the guard that stops a figure from
    killing the report. Anything the alarm can return must be drawable."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("run_alarm", "scripts/run_alarm.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Every status the alarm knows must have a severity, and every severity a shade.
    assert set(alarm.SEVERITY) >= {alarm.STOPPED, alarm.COLLAPSED,
                                   alarm.UNDERPERFORMING, alarm.NOT_READ,
                                   alarm.HEALTHY, alarm.TOO_NEW}
    assert set(alarm.SEVERITY.values()) <= {"high", "medium", "low", "none"}


def test_the_dashboard_draws_a_fleet_containing_every_status(tmp_path):
    import importlib.util

    spec = importlib.util.spec_from_file_location("run_alarm", "scripts/run_alarm.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    dead = dict(STEADY)
    for m in months(2024, 24)[12:]:
        dead[m] = 0.0
    creeping = dict(STEADY)
    for m in months(2024, 24)[6:]:
        creeping[m] = 9.0
    sliding = dict(STEADY)
    for m in months(2024, 24)[-4:]:
        sliding[m] = 300.0

    plants = fleet({"dead": dead, "creeping": creeping, "sliding": sliding,
                    "fine": dict(STEADY), "also fine": dict(STEADY)})
    findings = alarm.assess(plants, "2025-12")
    drawn = {f.status for f in findings}
    assert {alarm.STOPPED, alarm.COLLAPSED, alarm.UNDERPERFORMING} <= drawn

    module.FIGURE = tmp_path / "dashboard.png"
    module._figure(plants, findings, "2025-12")       # must not raise
    assert module.FIGURE.exists() and module.FIGURE.stat().st_size > 1000

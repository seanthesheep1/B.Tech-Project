"""The soiling model: accumulation, washing, and the arithmetic around them."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from btp_solar import soiling


def _rain(values, start="2020-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="D"),
                     dtype=float)


# --- reading the record --------------------------------------------------


def test_power_sentinel_values_are_not_read_as_negative_rain(tmp_path):
    """POWER marks a gap with -999, not a null. Left alone it reads as
    negative rainfall, which would suppress every wash in the record."""
    path = tmp_path / "precip.json"
    path.write_text(json.dumps({"properties": {"parameter": {"PRECTOTCORR": {
        "20200101": 12.0, "20200102": -999.0, "20200103": 0.0,
    }}}}))
    series = soiling.load_daily_rainfall(path)
    assert (series >= 0).all()
    assert series.iloc[1] == pytest.approx(6.0)  # interpolated between 12 and 0


def test_a_record_of_nothing_but_gaps_is_refused(tmp_path):
    path = tmp_path / "precip.json"
    path.write_text(json.dumps({"properties": {"parameter": {"PRECTOTCORR": {
        "20200101": -999.0, "20200102": -999.0,
    }}}}))
    with pytest.raises(ValueError, match="no usable rainfall"):
        soiling.load_daily_rainfall(path)


# --- accumulation and washing --------------------------------------------


def test_dust_accumulates_through_a_dry_spell():
    loss = soiling.soiling_loss(_rain([0.0] * 60), soiling_rate=0.003)
    assert loss.iloc[-1] > loss.iloc[10] > loss.iloc[0]


def test_rain_past_the_threshold_resets_the_glass():
    dry_then_wet = _rain([0.0] * 40 + [20.0] + [0.0] * 5)
    loss = soiling.soiling_loss(dry_then_wet, soiling_rate=0.003)
    assert loss.iloc[39] > 0.05
    assert loss.iloc[42] < loss.iloc[39] / 2


def test_drizzle_below_the_threshold_does_not_clean():
    drizzle = _rain([0.0] * 20 + [1.0] * 20)
    loss = soiling.soiling_loss(drizzle, soiling_rate=0.003)
    assert loss.iloc[-1] > loss.iloc[20]


def test_accumulated_loss_is_capped():
    loss = soiling.soiling_loss(_rain([0.0] * 500), soiling_rate=0.01,
                               max_soiling=0.2)
    assert loss.max() <= 0.2 + 1e-9


def test_a_higher_rate_never_means_less_dust():
    dry = _rain([0.0] * 90)
    gentle = soiling.soiling_loss(dry, soiling_rate=0.001).sum()
    harsh = soiling.soiling_loss(dry, soiling_rate=0.005).sum()
    assert harsh > gentle


def test_zero_rate_means_clean_glass_forever():
    loss = soiling.soiling_loss(_rain([0.0] * 200), soiling_rate=0.0)
    assert loss.abs().max() == pytest.approx(0.0, abs=1e-12)


def test_a_rate_outside_a_daily_fraction_is_refused():
    for bad in (-0.01, 1.0, 4.0):
        with pytest.raises(ValueError, match="daily fraction"):
            soiling.soiling_loss(_rain([0.0] * 5), soiling_rate=bad)


def test_a_manual_wash_removes_dust_the_weather_left():
    dry = _rain([0.0] * 120)
    washes = pd.DatetimeIndex([pd.Timestamp("2020-03-01")])
    dirty = soiling.soiling_loss(dry, soiling_rate=0.004)
    washed = soiling.soiling_loss(dry, soiling_rate=0.004, manual_wash_dates=washes)
    assert washed.sum() < dirty.sum()


# --- aggregation ---------------------------------------------------------


def test_monthly_mean_returns_twelve_months_january_first():
    loss = soiling.soiling_loss(_rain([0.0] * 400), soiling_rate=0.002)
    monthly = soiling.monthly_mean_loss(loss)
    assert len(monthly) == 12
    assert all(0.0 <= v <= 1.0 for v in monthly)


def test_applying_soiling_only_ever_removes_energy():
    energy = [100.0] * 12
    out = soiling.apply_monthly(energy, [0.1] * 12)
    assert out == pytest.approx([90.0] * 12)


def test_series_of_the_wrong_length_are_refused():
    with pytest.raises(ValueError, match="twelve months"):
        soiling.apply_monthly([1.0] * 11, [0.0] * 12)


def test_annual_loss_is_weighted_by_the_energy_at_risk():
    """Delhi's dirtiest months are also among its dimmest, so an unweighted
    mean of the twelve overstates what soiling actually costs."""
    energy = [10.0] * 6 + [100.0] * 6        # dim half, bright half
    monthly = [0.20] * 6 + [0.00] * 6        # dirt only in the dim half
    unweighted = sum(monthly) / 12
    assert soiling.annual_loss(energy, monthly) < unweighted
    assert soiling.annual_loss(energy, monthly) == pytest.approx(
        (6 * 10 * 0.20) / (6 * 10 + 6 * 100)
    )


def test_annual_loss_of_a_year_with_no_energy_is_refused():
    with pytest.raises(ValueError, match="no energy"):
        soiling.annual_loss([0.0] * 12, [0.1] * 12)


# --- cleaning schedules --------------------------------------------------


def test_a_wash_outside_the_rainfall_record_is_refused():
    rain = _rain([0.0] * 30)
    with pytest.raises(ValueError, match="outside the rainfall record"):
        soiling.cleaning_schedule(["2030-01-01"], rain)


def test_recurring_washes_land_once_per_named_month_per_year():
    rain = _rain([0.0] * 800)  # a little over two years
    washes = soiling.washes_each_year(rain, months=(1, 3))
    assert len(washes) == len({(d.year, d.month) for d in washes})
    assert {d.month for d in washes} == {1, 3}
    assert (washes >= rain.index.min()).all() and (washes <= rain.index.max()).all()


def test_more_washes_recover_more_energy():
    rain = _rain([0.0] * 740)
    energy = [100.0] * 12
    base = soiling.soiling_loss(rain, 0.004)
    once = soiling.soiling_loss(rain, 0.004,
                                manual_wash_dates=soiling.washes_each_year(rain, (2,)))
    thrice = soiling.soiling_loss(
        rain, 0.004, manual_wash_dates=soiling.washes_each_year(rain, (12, 2, 4))
    )
    losses = [soiling.annual_loss(energy, soiling.monthly_mean_loss(s))
              for s in (base, once, thrice)]
    assert losses[0] > losses[1] > losses[2]

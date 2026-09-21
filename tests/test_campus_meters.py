"""The meter-workbook cleaning rules.

These are regression tests for real defects found in the supervisor's data,
each one named after the defect it guards against.
"""

from __future__ import annotations

import datetime as dt

import pytest

from btp_solar import campus_meters
from btp_solar.campus_meters import Reading


def series(values, meter=12345678, mf=1.0, location="Test Block", start=dt.date(2024, 1, 1)):
    return [Reading(start + dt.timedelta(days=i), meter, location, mf, v)
            for i, v in enumerate(values)]


def test_a_clean_rising_register_is_left_alone():
    plants = campus_meters.clean(series([100.0, 110.0, 121.0, 133.0]))
    plant = plants[12345678]
    assert len(plant.readings) == 4
    assert plant.dropped == []


def test_decimal_slip_is_removed():
    """113341.7 typed as 1113411.2 - the real defect in the March 2024 sheet."""
    plants = campus_meters.clean(series([113341.7, 1113411.2, 113489.7]))
    plant = plants[12345678]
    assert len(plant.readings) == 2
    assert len(plant.dropped) == 1
    assert plant.dropped[0][1] == pytest.approx(1113411.2)


def test_blank_entered_as_zero_is_removed():
    """Several columns read exactly 0 on 2024-04-26; a register cannot do that."""
    plants = campus_meters.clean(series([83941.0, 0.0, 83950.0]))
    plant = plants[12345678]
    assert len(plant.readings) == 2
    assert "blank" in plant.dropped[0][2]


def test_a_genuine_zero_register_survives():
    """A new plant legitimately reads near zero; do not strip it."""
    plants = campus_meters.clean(series([0.0, 1.0, 2.0, 3.0]))
    assert len(plants[12345678].readings) == 4


def test_meter_factor_is_applied_to_energy():
    plants = campus_meters.clean(series([100.0, 200.0], mf=60.0))
    assert plants[12345678].monthly_kwh["2024-01"] == pytest.approx(6000.0)


def test_the_relabelled_meter_is_folded_into_one_plant():
    """29490555 and 42490555 are one continuous register, proved contiguous."""
    readings = (series([155000.0, 155597.2], meter=29490555)
                + series([155631.2, 155700.0], meter=42490555, start=dt.date(2024, 1, 3)))
    plants = campus_meters.clean(readings)
    assert 42490555 not in plants
    assert len(plants[29490555].readings) == 4


def test_a_mid_month_reset_is_dropped_not_counted_as_negative():
    plants = campus_meters.clean(series([5000.0, 5100.0, 20.0, 40.0]))
    assert "2024-01" not in plants[12345678].monthly_kwh


def test_text_dates_are_parsed():
    """The March 2024 sheet stores dates as '01.03.2024' strings."""
    assert campus_meters._parse_date("01.03.2024") == dt.date(2024, 3, 1)
    assert campus_meters._parse_date("2024-03-01") == dt.date(2024, 3, 1)
    assert campus_meters._parse_date("not a date") is None


def test_meter_numbers_are_recognised_by_shape():
    assert campus_meters._is_meter_number(29490556)
    assert not campus_meters._is_meter_number(60)        # a meter factor
    assert not campus_meters._is_meter_number(1234)      # a register reading

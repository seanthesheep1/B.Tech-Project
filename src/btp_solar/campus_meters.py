"""Campus solar generation meters: the supervisor's monthly reading workbooks.

These workbooks are daily cumulative register readings for the rooftop PV
plants already installed on campus. They are the single most valuable input
the project has, because they turn FR-4 from a modelling exercise validated
against two buildings into one validated against a whole fleet.

Three things about the format have to be handled or every number comes out
wrong:

1. **Meter factor.** Each column carries an ``MF`` of 1 to 80. Energy is the
   register difference multiplied by that factor. The January to June 2024
   sheets omit the MF row; the register values are continuous across the June
   to July boundary, so the factors from the later sheets apply throughout.
2. **Column order changes between sheets**, so columns must be joined on the
   meter number and never on position.
3. **The readings contain transcription errors** - decimal-point slips such as
   113341.7 typed as 1113411.2, blanks entered as 0, and dates stored as text
   on some sheets. Differencing raw readings without repairing these inflates
   annual generation by roughly an order of magnitude.
"""

from __future__ import annotations

import datetime as dt
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

DATE_FORMATS = ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d")

# Proved contiguous: the last reading under 29490555 (31 Jul 2025, 155597.2)
# and the first under 42490555 (1 Aug 2025, 155631.2) differ by one ordinary
# day of generation, so this is one plant whose label changed, not two plants.
METER_ALIASES = {42490555: 29490555}


@dataclass
class Reading:
    date: dt.date
    meter: int
    location: str
    meter_factor: float
    register: float


@dataclass
class Plant:
    meter: int
    location: str
    meter_factor: float
    readings: dict[dt.date, float] = field(default_factory=dict)
    dropped: list[tuple[dt.date, float, str]] = field(default_factory=list)

    @property
    def monthly_kwh(self) -> dict[str, float]:
        """Energy per calendar month, from the cleaned register."""
        by_month: dict[str, list[tuple[dt.date, float]]] = defaultdict(list)
        for date, value in self.readings.items():
            by_month[date.strftime("%Y-%m")].append((date, value))

        out: dict[str, float] = {}
        for month, points in by_month.items():
            if len(points) < 2:
                continue
            points.sort()
            delta = points[-1][1] - points[0][1]
            if delta < 0:
                continue  # register reset inside the month; unusable, not negative
            out[month] = delta * self.meter_factor
        return out

    def annual_kwh(self, year: int) -> float:
        prefix = str(year)
        return sum(v for m, v in self.monthly_kwh.items() if m.startswith(prefix))


def _is_meter_number(value) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and 1e7 <= float(value) < 1e8
        and float(value) == int(value)
    )


def _parse_meter_factor(value) -> float | None:
    if value is None:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", str(value))
    return float(match.group(1)) if match else None


def _parse_date(value) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        for fmt in DATE_FORMATS:
            try:
                return dt.datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
    return None


def read_workbook(path: Path) -> list[Reading]:
    """Read every monthly sheet of one workbook into flat readings."""
    import openpyxl

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    readings: list[Reading] = []

    for sheet in workbook.worksheets:
        grid = [list(r) for r in sheet.iter_rows(min_row=1, max_row=min(sheet.max_row, 60),
                                                 values_only=True)]
        if not grid:
            continue

        header_depth = min(8, len(grid))
        meter_row = max(range(header_depth), key=lambda i: sum(map(_is_meter_number, grid[i])))
        if sum(map(_is_meter_number, grid[meter_row])) < 5:
            continue

        mf_row = next(
            (i for i in range(header_depth)
             if sum(1 for c in grid[i] if isinstance(c, str) and c.strip().upper().startswith("MF"))
             >= 5),
            None,
        )
        name_row = next(
            (i for i in range(meter_row)
             if grid[i][0] and str(grid[i][0]).strip().lower().startswith(("location", "date"))),
            meter_row - 1,
        )

        columns = {}
        for j, cell in enumerate(grid[meter_row]):
            if _is_meter_number(cell):
                meter = int(cell)
                columns[j] = (
                    METER_ALIASES.get(meter, meter),
                    str(grid[name_row][j]).strip() if grid[name_row][j] else "",
                    _parse_meter_factor(grid[mf_row][j]) if mf_row is not None else None,
                )

        for row in sheet.iter_rows(min_row=meter_row + 2, values_only=True):
            date = _parse_date(row[0])
            if date is None:
                continue
            for j, (meter, location, mf) in columns.items():
                if j < len(row) and isinstance(row[j], (int, float)) and not isinstance(row[j], bool):
                    readings.append(Reading(date, meter, location, mf or 1.0, float(row[j])))

    workbook.close()
    return readings


def clean(readings: list[Reading]) -> dict[int, Plant]:
    """Group readings by plant and repair transcription errors.

    A generation register only ever rises. A reading that sits well outside
    both of its neighbours is therefore a typing error, not a measurement, and
    a zero on a register reading in the thousands is a blank cell.
    """
    grouped: dict[int, list[Reading]] = defaultdict(list)
    for r in readings:
        grouped[METER_ALIASES.get(r.meter, r.meter)].append(r)

    plants: dict[int, Plant] = {}
    for meter, group in grouped.items():
        locations = Counter(r.location for r in group if r.location)
        factors = Counter(r.meter_factor for r in group if r.meter_factor)
        plant = Plant(
            meter=meter,
            location=locations.most_common(1)[0][0] if locations else str(meter),
            meter_factor=factors.most_common(1)[0][0] if factors else 1.0,
        )

        series = sorted({r.date: r.register for r in group}.items())
        largest = max((v for _, v in series), default=0.0)

        # blanks entered as zero
        kept = []
        for date, value in series:
            if value == 0 and largest > 100:
                plant.dropped.append((date, value, "blank entered as zero"))
            else:
                kept.append((date, value))

        # transient breaks in monotonicity: decimal-point and digit-shift slips
        values = [v for _, v in kept]
        alive = [True] * len(kept)
        for i, (date, value) in enumerate(kept):
            previous = next((values[j] for j in range(i - 1, -1, -1) if alive[j]), None)
            following = values[i + 1] if i + 1 < len(values) else None
            if previous is None or following is None:
                continue
            low, high = min(previous, following), max(previous, following)
            outside = value < low * 0.97 or value > high * 1.03
            material = high == 0 or abs(value - low) > max(50.0, 0.05 * max(high, 1.0))
            if outside and material:
                alive[i] = False
                plant.dropped.append((date, value, f"outside neighbours {low:.1f}/{high:.1f}"))

        plant.readings = {d: v for (d, v), ok in zip(kept, alive) if ok}
        plants[meter] = plant

    return plants


def load(paths: list[Path]) -> dict[int, Plant]:
    readings: list[Reading] = []
    for path in paths:
        readings.extend(read_workbook(path))
    return clean(readings)

"""The building register: one row per building, one column per computed number.

This is the project's audit trail and the first of the two standing rules in
the workflow note. Nothing may appear in the report that is not traceable to a
column here, and every column is described in register_schema.yml with the
module that produced it and the formula or source behind it.

Kept as CSV rather than a spreadsheet binary so that every change to a number
shows up as a readable diff in git.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import config


@dataclass(frozen=True)
class Column:
    name: str
    unit: str
    module: str
    source: str


def load(path: Path | None = None) -> list[dict[str, str]]:
    """Read the register. Returns a list of row dicts, values left as strings."""
    path = path or config.REGISTER_CSV
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fieldnames(path: Path | None = None) -> list[str]:
    path = path or config.REGISTER_CSV
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        return next(reader)


def save(rows: list[dict[str, Any]], path: Path | None = None) -> None:
    """Write the register back, preserving column order and adding new columns.

    New columns are appended rather than inserted, so a diff shows exactly what
    a run added.
    """
    path = path or config.REGISTER_CSV
    existing = fieldnames(path) if path.exists() else []
    extra = [k for row in rows for k in row if k not in existing]
    seen: set[str] = set()
    ordered = existing + [k for k in extra if not (k in seen or seen.add(k))]

    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=ordered, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in ordered})


def update_building(
    building_id: str, values: dict[str, Any], path: Path | None = None
) -> list[dict[str, str]]:
    """Merge computed values into one building's row and write the register back."""
    rows = load(path)
    ids = [r["building_id"] for r in rows]
    if building_id not in ids:
        raise KeyError(
            f"{building_id!r} is not in the register; add the row first so the "
            f"building list stays the single source of truth. Known: {', '.join(ids)}"
        )
    for row in rows:
        if row["building_id"] == building_id:
            row.update({k: _fmt(v) for k, v in values.items()})
    save(rows, path)
    return rows


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)

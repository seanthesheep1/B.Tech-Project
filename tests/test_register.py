"""The register is the audit trail, so its invariants are tested."""

from __future__ import annotations

import csv

import pytest
import yaml

from btp_solar import config, register


def test_register_parses_and_every_row_has_an_id():
    rows = register.load()
    assert rows, "the register should ship with template rows"
    assert all(r["building_id"].strip() for r in rows)


def test_building_ids_are_unique():
    ids = [r["building_id"] for r in register.load()]
    assert len(ids) == len(set(ids))


def test_every_column_is_described_in_the_schema():
    schema = yaml.safe_load(config.REGISTER_SCHEMA.read_text(encoding="utf-8"))
    described = {col for group in schema.values() for col in group}
    undocumented = set(register.fieldnames()) - described
    assert not undocumented, f"undocumented columns: {sorted(undocumented)}"


def test_validation_buildings_are_reserved():
    """Existing-PV buildings held back for the FR-4 back-test.

    The specification says two. The meter data revealed 29 locations already
    carrying PV, about 20 of them live, so the validation set was widened with
    the supervisor's agreement - see docs/decisions.md, 2026-09-22.
    """
    rows = register.load()
    validation = [r for r in rows if r["role"] == "validation"]
    assert len(validation) >= 2
    assert all(r["has_existing_pv"] == "yes" for r in validation)
    assert all(r["category"] == "existing_pv" for r in validation)


def test_candidates_have_no_existing_pv():
    """A candidate with panels already on it is a selection error."""
    candidates = [r for r in register.load() if r["role"] == "candidate"]
    assert all(r["has_existing_pv"] == "no" for r in candidates)


def test_candidates_span_the_required_categories():
    """Scope: academic blocks, laboratory blocks, hostels and a service building."""
    cats = {r["category"] for r in register.load() if r["role"] == "candidate"}
    assert {"academic", "laboratory", "hostel", "service"} <= cats


def test_every_candidate_carries_a_footprint_and_height():
    for r in register.load():
        if r["role"] != "candidate":
            continue
        assert r["osm_id"].strip(), f"{r['building_id']} has no footprint id"
        assert float(r["height_m"]) > 0, f"{r['building_id']} has no height"
        assert r["height_source"].strip(), f"{r['building_id']} height has no source"


def test_candidate_count_is_within_scope():
    """Eight to ten candidate buildings, per section 1 of the specification."""
    candidates = [r for r in register.load() if r["role"] == "candidate"]
    assert 8 <= len(candidates) <= 10


def test_every_row_has_the_same_column_count():
    with config.REGISTER_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert len({len(r) for r in rows}) == 1


def test_update_rejects_an_unknown_building(tmp_path):
    target = tmp_path / "register.csv"
    target.write_text(config.REGISTER_CSV.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(KeyError, match="not in the register"):
        register.update_building("B99", {"gross_roof_area_m2": 100.0}, path=target)


def test_update_appends_new_columns_without_disturbing_the_old(tmp_path):
    target = tmp_path / "register.csv"
    target.write_text(config.REGISTER_CSV.read_text(encoding="utf-8"), encoding="utf-8")
    before = register.fieldnames(target)

    register.update_building("B01", {"gross_roof_area_m2": 1600.0, "new_metric": 42.0},
                             path=target)

    after = register.fieldnames(target)
    assert after[: len(before)] == before
    assert "new_metric" in after
    row = next(r for r in register.load(target) if r["building_id"] == "B01")
    assert row["gross_roof_area_m2"] == "1600"
    assert row["new_metric"] == "42"

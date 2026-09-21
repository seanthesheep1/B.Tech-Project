"""Print the building register with the provenance of each column.

    uv run python scripts/show_register.py
"""

from __future__ import annotations

import sys

import yaml

sys.path.insert(0, "src")

from btp_solar import config, register  # noqa: E402


def main() -> int:
    rows = register.load()
    schema = yaml.safe_load(config.REGISTER_SCHEMA.read_text(encoding="utf-8"))
    described = {col for group in schema.values() for col in group}

    selected = [r for r in rows if r["selected"].strip().lower() == "yes"]
    print(f"{len(rows)} buildings in the register, {len(selected)} confirmed selected")
    print()

    header = f"{'id':<5} {'name':<28} {'category':<12} {'role':<11} {'roof m2':>9}"
    print(header)
    print("-" * len(header))
    for r in rows:
        area = r["gross_roof_area_m2"] or "-"
        print(
            f"{r['building_id']:<5} {(r['building_name'] or '(unnamed)'):<28} "
            f"{r['category']:<12} {r['role']:<11} {area:>9}"
        )

    undocumented = [c for c in register.fieldnames() if c not in described]
    if undocumented:
        print()
        print("Columns with no entry in register_schema.yml (add one before use):")
        for col in undocumented:
            print(f"  - {col}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

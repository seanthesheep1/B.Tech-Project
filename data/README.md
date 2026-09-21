# Data

Every data file for the project lives in this one folder: downloaded inputs,
the workbooks from the Estate Office, and the products the code writes.

## Committed

    building_register.csv       the audit trail, one row per building and one
                                column per computed number
    register_schema.yml         the data dictionary; a test fails if a column
                                appears in the register without an entry here

    Solar reading jan-24 to dec-24.xlsm     daily generation-meter readings,
    Solar meter Report-2025 & 2026.xlsx     Jan 2024 to Apr 2026, from the
                                            supervisor

These two workbooks are committed so the raw data survives a lost laptop, the
failure mode the workflow note warns about. They are the **Institute's data**,
so the repository must stay private and the files must not be redistributed
without the supervisor's permission. If the repository is ever made public,
remove them from the history first, not just from the working tree.

## Not committed

Reproducible from a download, so it stays out of git. See `.gitignore`.

    campus_solar_monthly.csv                written by scripts/run_campus_meters.py
    pvgis_tmy_*.json                        cached PVGIS typical year
    nasa_power_*.json                       cached NASA POWER hourly series

Record the download date and the exact query for anything fetched here in
`docs/decisions.md` as you go. A number whose provenance is not written down at
the time it is fetched is a number that gets argued about in November.

## One rule

All area and length measurement happens in EPSG:32643 (UTM 43N), never in
EPSG:4326. Measuring in degrees is the single most common way to get a rooftop
area wrong by a factor of ten thousand.

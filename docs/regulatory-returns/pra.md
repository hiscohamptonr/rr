# PRA and combined BSCR aggregate process

## Data sources

- SQL Server EDM `HISCO_UKEU_01JAN26_010126_ROLLUP_ByLoB_GC_v25`, as named in [`aggregates/aggs-from-edm.sql`](../../aggregates/aggs-from-edm.sql) and the workbook's `sql` sheet.
- Canonical calculation workbook: [`pra/PRA_BSCR_Aggs.xlsx`](../../pra/PRA_BSCR_Aggs.xlsx).
- Embedded workbook lookups: `region_mappings`, `cds_mapping`, and `rms_geog`.
- Approved PRA instructions and final return template held outside this repository.

See the [complete data-flow map](data-flow.md) for the BSCR overlap, workbook formulas, and discrepancy register.

## Purpose

`PRA_BSCR_Aggs.xlsx` is a combined calculation workbook. It produces PRA geography/class pivots and contains separate BSCR earthquake-split calculation panels. It is not itself a final PRA submission template.

## Workbook structure

| Sheet | Role |
|---|---|
| `region_mappings` | Country/territory to Standard Formula and PRA region mapping |
| `pivot_allperil` | 838-row aggregate table with PRA class/geography formulas and all-peril pivots |
| `pivot_eq` | Separate 838-row aggregate table with the same formula family and earthquake pivots |
| `raw_data_for_bscr_splits_eq` | 270,675-row earthquake table, retention/geography flags, and BSCR calculation panels |
| `cds_mapping` | Portfolio/CDS class lookup |
| `rms_geog` | RMS country and region lookup |
| `sql` | Aggregate extraction query for peril `2`, policy type `2` |

The checked-in `aggregates/aggs-from-edm.sql` matches the embedded query's calculation route: allocate account PML to locations by TIV, subtract deductibles, cap at policy limit, then group by geography and underwriting identifiers.

## PRA calculation route

The two pivot input tables derive:

- Fine-art classification from `uwritrname`.
- Country display from country code.
- US, by-country, and by-state groupings.
- PRA region from `region_mappings`.
- CDS class from `cds_mapping`.
- USD aggregate as `pml * 1.25`.

The exact producer/population step for the all-peril 838-row table is not checked in. The embedded SQL is earthquake-specific, so do not claim that one query regenerates both pivot tabs.

## BSCR calculation route inside the PRA workbook

`raw_data_for_bscr_splits_eq` identifies HIG, `_QS`, `_SRP`, North American hurricane, and North American earthquake records. Formula panels to the right of the raw table calculate values intended for the BSCR schedule handoff. `_QS` retains `50%`; `_SRP` retains `33%` in this workbook.

These panels overlap the separate Python/BSCR-workings route. Reconcile them before entering final green cells; neither route automatically supersedes the other.

## Duplicate copy

`pra/UKEU/PRA_BSCR_Aggs.xlsx` is SHA-256 identical to `pra/PRA_BSCR_Aggs.xlsx`. Treat the root `pra/PRA_BSCR_Aggs.xlsx` as canonical. Do not update both independently. The duplicate remains in place pending an owner decision to delete or archive it.

## Required controls before use

- Confirm database, peril/policy-type parameters, source row counts, and as-of date.
- Record how each 838-row table was populated.
- Confirm `1.25` is the approved currency factor for the target cycle; it differs from other checked-in artefacts.
- Resolve `_SRP` retention differences: `33%` here, `0.3333` in Python, and `0.33333` in SQL.
- Confirm the geography and class lookup versions.
- Check that `pivot_eq` is refreshed from the earthquake table; its cached view shows totals also present in the all-peril view.
- Reconcile raw input totals, transformed totals, pivot totals, and final return cells.
- Preserve formulas, tables, pivot sources, validations, and formatting when replacing input data.

## Controlled handoff

For every value entered into a PRA or BSCR return, retain:

- source query/script and version;
- source workbook, sheet, and cell/range;
- mapping and rate versions;
- destination workbook and green cell;
- amount, currency, unit, and as-of date;
- preparer and reviewer evidence.

No final PRA template is checked in, so its green-cell addresses remain unresolved until the controlled template is supplied.

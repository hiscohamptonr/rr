# BSCR Schedule X

## Data sources

- SQL Server EDM configured by [`bscr/BSCR_UKEU.py`](../../bscr/BSCR_UKEU.py): `loc`, `policy`, `accgrp`, and `loccvg` tables.
- Script CSV output loaded into [`bscr/Workings_with_geocodingFW - Including blanks USD.xlsx`](../../bscr/Workings_with_geocodingFW%20-%20Including%20blanks%20USD.xlsx).
- Final HIC return workbook: [`bscr/2026 BSCR - UKEU - HIC.xlsx`](../../bscr/2026%20BSCR%20-%20UKEU%20-%20HIC.xlsx).
- Approved BSCR template, mappings, rates, and instructions held outside this repository.

See the [complete data-flow map](data-flow.md) for cross-return dependencies, workbook internals, and unresolved mismatches.

## Purpose

The process calculates entity and regional catastrophe exposure values for BSCR Schedules X(a), X(b), X(c), and X(f). The current repository contains an executable SQL-to-CSV script, a pivot workbook, and the HIC return workbook.

## Flow

1. `BSCR_UKEU.py` queries the configured EDM.
2. It allocates account PML to locations by TIV, zeroes invalid locations, subtracts location deductibles, and caps at policy limits.
3. It classifies entity and geography, applies `_QS` and `_SRP` retention, and groups gross/net totals.
4. Its seven-column CSV is loaded into `Sheet1` columns A:G of the workings workbook.
5. Workbook formulas apply the `1.35` USD factor and USD-millions scaling; `output` consolidates and `piv` presents entity/region totals.
6. Approved pivot/calculation results are entered into the final HIC workbook's green cells under review.

The final workbook is not formula-linked to the workings workbook. The transfer is a controlled manual handoff.

## Script output contract

| Column | Meaning |
|---|---|
| `cntrycode` | Source country code; blank for the `ALL` row |
| `bscr_entity` | `HIG`, `HSA`, or `33` |
| `region` | `ALL`, `is_eu`, `is_jp`, `is_na_eq`, `is_nahu`, or `is_us_all` |
| `sum_pml` | Gross modelled PML before currency conversion |
| `sum_net` | PML after suffix-based retention |
| `count_policies` | Count of contributing query rows, not guaranteed distinct policies |
| `is_geocoded` | Geocoding flag or blank for `ALL` |

Regional flags can overlap. Do not add regional totals together unless the return instructions explicitly require it.

## Workbook handoff

| Source | Transformation | Destination |
|---|---|---|
| Script CSV A:G | Paste into `Sheet1`; preserve formula columns | BSCR workings `Sheet1` |
| `Sheet1` | Consolidation and `1.35` conversion | `output` |
| `output` | Entity/region/geocoding pivots in USD millions | `piv` |
| Approved pivot/calculation cells | Manual, reviewed green-cell entry | HIC Schedules X(a), X(b), X(c), X(f) |

For every green-cell entry, record source workbook/range, destination cell, value, unit, currency, as-of date, preparer, and reviewer.

## Required controls before use

Resolve or approve every item below:

- `is_nahu()` currently classifies every non-null US state as North American hurricane; the state tests are unreachable in that path.
- Script and workbook geography lists are not identical.
- `_SRP` retention differs across artefacts: `0.3333` in Python, `33%` in the PRA workbook, and `0.33333` in SQL.
- The workings workbook hard-codes `1.35`; confirm that source values are GBP and that the rate is approved for the cycle.
- The final HIC workbook contains external links to older 2025 and 2017 workbooks and a blank 2026 HIG template.
- Confirm the workings pivot source ranges and refresh state.
- Reconcile gross/net totals and row counts at query, CSV, `Sheet1`, `output`, `piv`, and final schedule boundaries.

## Run

```bash
uv run python bscr/BSCR_UKEU.py \
  --server '<sql-server>' \
  --database '<edm-database>' \
  --output '<controlled-output>.csv'
```

Use connection-security options only as approved for the environment. The CLI defaults are documented by `--help` and in the [script runbook](../../bscr/bscr-runbook.md).

## Not automatic

The script does not select the reporting database, approve mapping/rate changes, refresh Excel, identify green cells, or sign off the return. Those remain controlled owner/reviewer decisions.

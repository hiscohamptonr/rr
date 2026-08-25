# BSCR Schedule X

## Summary

- **Sources:** approved January EDM and current BSCR entity, geography, retention, and FX assumptions.
- **Calculation:** `bscr/BSCR_UKEU.py` and `bscr/workbooks/Workings_with_geocodingFW - Including blanks USD.xlsx`.
- **Final workbook/output:** `bscr/workbooks/2026 BSCR - UKEU - HIC.xlsx`, Schedules X(a), X(b), X(c), and X(f).
- **Time estimate:** included in 1 day for PRA and BSCR together.

## Purpose and sources

This process calculates entity and regional catastrophe exposure values for BSCR Schedule X. It uses:

- SQL Server EDM tables `loccvg`, `loc`, `policy`, and `accgrp` selected by `bscr/BSCR_UKEU.py`;
- the seven-column script output loaded into `bscr/workbooks/Workings_with_geocodingFW - Including blanks USD.xlsx`; and
- reviewed manual entry into `bscr/workbooks/2026 BSCR - UKEU - HIC.xlsx`.

Current BSCR instructions, the approved template, mappings, rates, and annual owner decisions are external to the repository and remain authoritative.

For current code/workbook grain, null behaviour, formulas, and automated
validation rules, see [bscr-for-llm.md](bscr-for-llm.md). It is an observed
implementation specification, not an approved BSCR methodology.

See the repository [calculation discrepancy register](../../docs/calculation-discrepancies.md)
for the exact evidence and owner decisions.

## Current production blockers

Do not complete a Schedule X handoff from the checked-in workbooks until the
following are resolved and evidenced:

1. `Sheet1` does not automatically populate `output!A:F`; those static rows
   feed `piv`, so refreshing pivots alone can retain stale values.
2. The Python policy join/cap grain is not an approved policy-level contract
   and can cross-multiply account geography and policy rows.
3. `count_policies` is a grouped source-row count, not a distinct contract
   count; it cannot establish Schedule X(f) contract counts.
4. `piv` supplies only some exposure-limit-like inputs. EP curves, premiums,
   narratives, and X(f) methodology classifications require separately
   approved sources and an exact source-to-cell map.
5. The HIC workbook contains `#REF!` formulas and older external links. An
   unresolved formula/link is a stop condition, not something to preserve.

## Calculation boundary

The script performs the following work:

1. Selects `loccvg` records for the approved peril and groups coverage `valueamt` by location and deductible fields.
2. Sets the grouped amount to zero when it is below `deductamt`; it does not subtract the deductible.
3. Groups to account/geography and joins policies for the approved policy type.
4. Caps exposure using the query's `partof`/`blanlimamt` policy-limit logic.
5. Assigns BSCR entity, geography, and geocoding classifications.
6. Applies substring retention: `_QS = 0.50`, `_SRP = 0.3333`, otherwise
   `1.00`; if both markers occur, `_QS` wins. This is current code behaviour,
   not a suffix-only rule.
7. Writes grouped gross/net totals and contributing-row counts.

The script does not perform currency conversion. The workings workbook owns the hard-coded `1.35` conversion and `/1,000,000` scaling, but its `output!A:F` consolidation rows are static and require an approved rebuild procedure. The final HIC workbook owns template formulas and controlled inputs.

The workings and HIC files are not formula-linked. The final transfer is manual, reviewed, and evidenced.

## Output contract

| Column | Meaning |
|---|---|
| `cntrycode` | Source country code retained in both regional and `ALL` output rows |
| `bscr_entity` | First configured substring found in `userid1`: `HIG`, `HSA`, `33`, `3624`, or `HIC` |
| `region` | `ALL`, `is_eu`, `is_jp`, `is_na_eq`, `is_nahu`, or `is_us_all` |
| `sum_pml` | Gross amount before workbook currency conversion |
| `sum_net` | Amount after substring-based `_QS`/`_SRP` retention |
| `count_policies` | Count of contributing grouped/source rows; not guaranteed to be distinct policies |
| `is_geocoded` | `0` only when `addrmatch = 0`; null is currently treated as `1` |

Regional flags overlap. A source row can contribute to more than one regional bucket. Do not add regional rows together as if they were mutually exclusive. `ALL` is calculated separately and remains grouped by country and geocoding status.

## Pre-run controls

1. Record the server, EDM database and roll-up/version, reporting date, script revision, operator, and reviewer.
2. Confirm the annual meaning and approval of peril/policy codes; January defaults are `1/1`.
3. Approve the entity list, geography mappings, geocoding treatment, and `_QS`/`_SRP` factors.
4. Confirm the source currency and approve the workbook's `1.35` conversion and `/1,000,000` unit scaling.
5. Open controlled copies of both workbooks and record formulas, pivot sources, calculation mode, external links, designated unlocked/yellow input ranges, and pre-refresh values.

## Run

From the repository root:

```bash
uv sync --locked
uv run python bscr/BSCR_UKEU.py --help
uv run python bscr/BSCR_UKEU.py \
  --server '<approved-server>' \
  --database '<approved-edm>' \
  --peril 1 \
  --policy-type 1 \
  --output '<new-empty-run-directory>/bscr-output.csv' \
  --source-output '<new-empty-run-directory>/bscr-source.csv'
```

`--help` does not connect to SQL Server. The run itself tests the connection,
executes the embedded query, prints source diagnostics, writes the optional
account-level/geocoded source file, and writes the seven-column aggregate
output. The files are written sequentially, so use a new empty run directory
and do not load any result if the command fails or either expected file is
missing.

Retain both CSVs and the complete run record. `bscr-source.csv` is the detailed evidence needed to investigate entity, geography, geocoding, retention, and row-count results.

## Workings workbook

| Sheet | Role |
|---|---|
| `AUDIT_SUMMARY` | Purpose, lineage, output, and required-control reminder |
| `Sheet1` | Script output in A:G; formula columns H:K calculate converted and USD-million measures |
| `output` | Static entity/region/geocoding rows in A:F; formula columns G:J apply `1.35` and `/1,000,000` |
| `piv` | Presents reviewed gross/net values in USD millions by entity/region/geocoding |

### Load and refresh

1. Open a controlled copy of `bscr/workbooks/Workings_with_geocodingFW - Including blanks USD.xlsx` and review `AUDIT_SUMMARY`. Verify ODBC Driver 18/integrated authentication and the approved certificate policy before connecting.
2. Clear only the old source rows in `Sheet1!A:G`; preserve row 1, formulas H:K, tables, pivots, and formatting.
3. Validate the CSV header, then paste **data rows only** into `Sheet1!A2:G...`
   in the existing order. `Sheet1` has no Excel table; retain the fixed
   full-column source used by its local pivot and do not create a table unless
   an approved workbook change defines one.
4. Fill formulas H:K through every pasted row and confirm the `1.35` and `/1,000,000` logic is still intact.
5. Stop: `output!A:F` are static, not a refreshable consolidation. Before any
   pivot refresh, obtain the approved procedure that rebuilds its rows from
   `Sheet1`, including clearing vanished groups and retaining source evidence.
6. Inspect workbook connections and pivot sources. Refresh `piv` only after the
   static bridge has been rebuilt and reconciled; use **Data > Refresh All**
   only when it will not update stale or unapproved external connections.
7. Check `output` first, then `piv`, and inspect errors, blanks, unmapped
   entities, unexpected geography, geocoding splits, and each final-cell map.
8. Reconcile query diagnostics, `bscr-source.csv`, `bscr-output.csv`, `Sheet1`,
   rebuilt `output`, and `piv` for gross, net, and source-row counts.

The checked-in January `Sheet1` `ALL` comparison totals are:

- gross: `237,171,936,541.44`
- net: `225,427,324,454.27`

Record currency, unit, source range, as-of date, parameters, and row count with these values. They are comparison baselines, not approved tolerances.

## Final output and handoff

Use `piv` only for reviewed, mapped exposure inputs. Its regional values include
Atlantic hurricane, North American earthquake, European windstorm, and Japanese
earthquake views potentially used by Schedule X(c); they are not a complete
source for all Schedule X schedules or fields.

Copy only values listed in an approved source-to-destination cell map into the
designated unlocked/yellow inputs in Schedules X(a), X(b), X(c), and X(f). Do
not rely on a generic “green cell” convention and do not replace template
formulas, validation, structure, or non-input cells.

For every entry, record the source workbook/range, destination workbook/cell, value, currency, unit, as-of date, preparer, reviewer, and review date.

## Known issues requiring review

- `is_nahu()` currently returns true for all US records: a null state returns true, while a non-null state bypasses the unreachable allow-list. Resolve or explicitly approve this behavior before production use.
- Python and workbook geography lists differ, including Caribbean codes and US coastal-state definitions.
- `_SRP` is `0.3333` in Python, `33%` in the PRA workbook, and `0.33333` in supplementary SQL.
- The workings workbook hard-codes `1.35`; confirm the source amounts are on the intended basis and that the rate is approved for the cycle.
- The final HIC workbook contains links to older external workbooks and a blank current-cycle HIG template. Schedule X(b) references an external `Import` sheet.
- Confirm every pivot source range and refresh state before handoff.
- Review policy/account join cardinality and `count_policies`; a final group does not prove that upstream one-to-many joins did not multiply exposure.

## Automation boundary

The script does not approve the reporting database, mappings, rates, source currency, green cells, refresh behavior, final values, or sign-off. A successful SQL connection or command completion is not evidence that those controls passed.

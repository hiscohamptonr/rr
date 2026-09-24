# PRA — SQL and Excel

Work from the `reporting/` directory. The checked-in workbook is a calculation
workbook, not the final PRA submission template. Treat repository SQL and
cached workbook values as implementation evidence until the reporting-period
source, database, mappings, currency/measure, and reviewer approvals are
recorded in the run record.

## Current SQL artefacts and boundaries

| File | Present behaviour |
|---|---|
| `pra/sql/pra-earthquake.sql` | Uses `@peril = 2` and `@policy_type = 2`; it has no `USE` clause or connection details. It returns five columns: `pml, state, userid1, cntrycode, uwritrname`. |
| `pra/sql/pra-raw.sql` | Uses the same defaults and returns seven columns, adding `accgrpid` and `branchname`; this is the offline/raw route, not the five-column pivot input. |
| `pra/sql/aggs-from-edm.sql` | Despite its name, hard-codes `peril = 2` and `policytype = 2`, and returns a grouped five-column result. It is not an all-peril query. |

The SQL files are runnable in an approved SQL client, but the repository
supplies no database connection or execution wrapper, approved snapshot, or
credentials. Preserve the exact command, connection/database identity,
parameters, headers, row counts, totals, and export path in the run record.

The SQL's observed grain is important before any export is used. It sums
location value by account group and location geography, joins policy rows back
on `accgrpid`, caps with the derived `policy_limit`, then groups the final
result only by `state, cntrycode, userid1, uwritrname`. The final five-column
export has no policy or account identifier and does not convert currencies.
The policy join/cardinality, zero-limit behaviour, deduction treatment, source
currency, and aggregation are therefore controls to resolve—not approved
calculation rules. Reconcile before/after each join and by geography and
currency; stop on unexplained multiplication or an unapproved measure.

## Earthquake

1. Confirm the approved EDM/database, reporting date, `2/2` meanings, scope,
   source currency, output unit, and current geography/CDS mappings. Do not
   infer them from the SQL defaults or workbook cache.
2. From the `reporting/` directory, run the approved SQL client against the
   approved database using `pra/sql/pra-earthquake.sql`. Export headers
   exactly as `pml, state, userid1, cntrycode, uwritrname`. Retain the raw
   result and exact command. For offline diagnostics, `pra-raw.sql` instead
   produces the seven-column `pml, accgrpid, uwritrname, state, userid1,
   branchname, cntrycode` output; do not paste that shape into the pivot input.
3. Make a controlled working copy of
   `pra/workbooks/PRA_Aggs.xlsx`. Before loading, inspect and record the
   current tables and pivot sources. Both `Table3` and `Table32` currently
   reference `A1:M838`; the workbook's shared pivot cache currently names
   `Table3` as its worksheet source, including the pivots shown on
   `pivot_eq`. The current file is therefore not evidence that earthquake
   pivots use `Table32`.
4. Do not clear, resize, paste, or refresh until the workbook owner has
   approved the source table, value field (`pml` versus any converted measure),
   currency/unit, mappings, and populated-range procedure. If approved, clear
   only the controlled input rows, paste the five-column export with headers
   into the selected table's A1:E range, preserve formula columns F:M, and
   fill formulas through the complete new source range. Record the resulting
   table reference and row count.
5. The checked-in `pivot_eq` formulas reference `Table32`, while the shared
   pivot cache points to `Table3`; this inconsistency is a stop condition, not
   an instruction to change the workbook ad hoc. After an explicit approved
   change, repoint all four earthquake pivots to the selected table, refresh
   only those pivots, and retain the before/after source and value-field
   settings.
6. Reconcile SQL/export totals to the loaded input, then to each pivot and
   report area at the required geography and mapping grains. Inspect `#N/A`,
   `#REF!`, `#VALUE!`, blanks, stale cached values, and rows outside the
   approved range. The checked-in workbook has known geography/CDS mapping
   gaps; do not treat a successful refresh or a zero as approval.

## All-peril

`pivot_allperil` and `Table3` may be used only with a separately approved
all-peril producer/export. No checked-in SQL file is an all-peril query:
`pra-raw.sql`, `pra-earthquake.sql`, and `aggs-from-edm.sql` all select peril
2. Do not copy earthquake results into the all-peril table, guess query codes,
or describe the cached `Table3` pivot as a current all-peril result without
lineage and reconciliation.

## Completion boundary

Archive the approved SQL/export, run record, raw and grouped reconciliations,
working workbook, and reviewer evidence together without overwriting source
evidence. A final PRA submission template and destination-cell map are not
present in this repository; locating and approving them remains a prerequisite
for submission.

# PRA — LLM calculation and workbook validation contract

This document captures observed behaviour of `BSCR_UKEU.py`,
`pra/sql/aggs-from-edm.sql`, and `PRA_BSCR_Aggs.xlsx`. It is not approval of an
all-peril producer, currency basis, mappings, or final PRA return values.

## Input contracts and query behaviour

For a selected peril/policy type, Python writes:

```text
PRA raw A:G:       pml, accgrpid, uwritrname, state, userid1, branchname, cntrycode
PRA aggregate A:E: pml, state, userid1, cntrycode, uwritrname
```

The query sums coverage values, zeros an amount when below deductible, does not
subtract deductible, then joins/caps via policy logic. It groups deductible and
limit currencies but does not convert them. Null deductible retains value;
zero `blanlimamt` zeroes the cap branch; null/negative currency/limit behaviour
must be owner-approved. PRA and BSCR queries are separate reads and not a
transactional snapshot; the BSCR outputs are context controls, not a proof that
PRA amounts must match.

## Workbook identities

| Purpose | Table | Required source |
|---|---|---|
| All-peril aggregate | `Table3` on `pivot_allperil` | loaded A:E and F:M formulas |
| Earthquake aggregate | `Table32` on `pivot_eq` | loaded A:E and F:M formulas |
| Earthquake raw | `Table2` on `raw_data_for_bscr_splits_eq` | loaded A:G and H:P formulas |

Load data rows only below the headers, resize each table to its exact final row,
and leave no residual blank table rows or data outside the table. Headers are
part of the CSV but must not be pasted into data row 2.

## Formula and pivot facts

- Fine Art is case-insensitive `userid1` contains `_FA_`; it does not use
  `uwritrname`.
- `Agg_USD = pml * 1.25`, but all eight checked-in pivots sum field 0 (`pml`),
  not `Agg_USD`. Do not call the pivot output USD until the value field is
  approved and verified.
- `pivot_eq` has four pivots but they currently share the all-peril cache
  (`Table3`). Before using it, every earthquake pivot must resolve to `Table32`;
  every all-peril pivot must resolve to `Table3`; and visible grand totals must
  equal approved table totals.
- `CDSClass` is an unguarded `XLOOKUP` on `userid1`. Any populated row with
  CDS/PRA-region `#N/A` is a stop. The baseline has material CDS-unmapped
  exposure; count helper-field errors separately only if they are bypassed and
  explicitly approved.
- The raw `is_na_eq` (Q) column is empty. Do not infer North American
  earthquake output from the raw sheet.

## Reconciliation gates

For a frozen approved source, compare raw and aggregate `pml` to the same
currency/unit and defined rounding tolerance. The observed earthquake table
total is `233,586,155,482.80`; the all-peril cached input total is
`255,773,631,164.60`. They are baselines, not business acceptance tolerances.

Stop for: missing/uncertain all-peril population; mismatch of pivot source or
value field; populated mapping errors; a table size/range mismatch; unapproved
1.25 currency basis; NAHU/retention discrepancy versus BSCR; partial output
files; or an external template without an approved cell map. An LLM must never
repair mappings, infer an all-peril scope, or use cached pivots as lineage.

# BSCR — LLM calculation and workbook validation contract

This is a technical description of observed `BSCR_UKEU.py` and workbook
behaviour. It does not approve current mappings, policy logic, currency, or
Schedule X handoff. Follow [bscr.md](bscr.md) stop conditions.

## Query mechanics

1. Group `loccvg.VALUEAMT` by location/deductible/limit fields for the selected
   peril. If `valueamt < deductamt`, use zero; do not subtract the deductible.
   Equality and null deductible retain the amount. Location limit fields are
   grouping fields, not applied limits.
2. Group to account/state/country/geocode, join policies, and apply the
   `partof`/`blanlimamt` cap expression. The policy join is not demonstrably at
   a policy-level grain: multiple geography/geocode rows and policies can form
   a cross-product, and grouping omits `policyid`.
3. Assign entity by the first case-insensitive substring in this order:
   `HIG`, `HSA`, `33`, `3624`, `HIC`. Assign retention by substring: `_QS`
   first (0.5), then `_SRP` (0.3333), else 1.
4. Emit separately grouped overlapping regional rows and `ALL` rows. `ALL`
   remains split by country and geocode. `count_policies` is `len()` of grouped
   source rows, not distinct policies/contracts.

Currency conversion is not in Python. The workings formula columns apply 1.35
and `/1,000,000`; source currency and rate direction need independent approval.

## Geography and null truth table

- `addrmatch = 0` is not geocoded; null and every other value are geocoded.
- Current NAHU code returns true for every US row because the state allow-list
  is unreachable for non-null states; it also includes selected Caribbean/Mexico
  codes. Do not call this approved coastal-state logic.
- NA EQ, EU, Japan, and other country sets are hard-coded, case-sensitive, and
  overlap. `LX` is used in the EU list. Produce country/state frequency tables
  and owner-approved regional totals before use.

## Workbook invariants and blockers

The input contract is seven columns in `Sheet1!A:G`, with formulas H:K filled
through the exact data range. `Sheet1` is not an Excel table; its local pivot
uses the fixed full-column source `A1:K1048576`, is filtered, and is not the
downstream consolidation. Do not create/resize a table without an approved
workbook change.

`output!A:F` are static values. Only G:J are formulas. All `piv` pivots source
`output!A1:J50`. Therefore this sequence is invalid:

```text
paste Sheet1 -> Refresh All -> use piv
```

An approved bridge must specify how to rebuild `output!A:F` from `Sheet1`,
including exact key, aggregation, clear/paste method, formula coverage, and
reconciliation. Without it, stop. The baseline `Sheet1` ALL totals are gross
`237,171,936,541.44` and net `225,427,324,454.27`; they do not prove that
`output`, `piv`, or HIC are current.

## Schedule X constraints

`piv` can support only mapped exposure inputs. It does not derive EP curves,
premiums, narratives, model/data-quality classifications, or distinct contract
counts for X(f). The HIC template contains `#REF!` formulas and old external
links. Require an approved cell map containing source range, destination cell,
measure, currency/unit, and reviewer for every input. Never infer a cell from
fill colour; current editable cells are yellow/unlocked rather than generally
green.

## LLM execution gates

Do not continue unless all are true:

- approved database snapshot, parameters, mappings, retention, FX and output
  cell map are recorded;
- ODBC/certificate policy is approved; unique output directory is empty;
- per-CTE before/after join counts, distinct policies/accounts, and gross/net
  totals meet owner-approved checks;
- all unmapped entities/geography, unexpected address-match values, and
  multi-policy accounts are resolved;
- output bridge and pivots are rebuilt and reconciled; and
- all final-workbook `#REF!` and external links are resolved or explicitly
  approved as out of scope.

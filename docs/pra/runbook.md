# PRA aggregates

[Start here](../../README.md) · [Run checklist](../operating-controls.md) ·
[Detailed LLM reference](technical-contract.md)

**Result:** reviewed earthquake and all-peril aggregates in
`pra/workbooks/PRA_BSCR_Aggs.xlsx`. The final PRA return is a separate template.

**Before production:** the owner must confirm the all-peril source, pivot value
fields, currency and mapping rules, and final-template cell map.
See [PRA-01–03](../decisions.md#pra-01). Do not use cached January values as a new return.

## 1. Get ready

Use an approved EDM snapshot, current mappings and a working copy of the
workbook. Complete the [run checklist](../operating-controls.md), including
ODBC Driver 18 and SQL Server access. Confirm earthquake codes `2/2` for this cycle.

## 2. Extract earthquake data

Run from the repository root. Replace the placeholders; use a new run folder.

```bash
uv sync --locked
uv run python bscr/BSCR_UKEU.py \
  --server '<approved-server>' --database '<approved-edm>' \
  --peril 2 --policy-type 2 \
  --output '<run-dir>/bscr-2-2-control.csv' \
  --source-output '<run-dir>/bscr-2-2-source.csv' \
  --pra-raw-output '<run-dir>/pra-eq-raw.csv' \
  --pra-aggregate-output '<run-dir>/pra-eq-aggregate.csv'
```

Keep all four files and the run log. If the command fails or a file is missing,
do not load partial results. The two BSCR files are supporting controls, not
substitutes for the PRA amounts.

## 3. Load the workbook

Check CSV headers against the existing columns. Clear old input rows only;
paste **data without headers** from row 2. Preserve formulas and report areas.

| CSV | Paste into | Extend formulas / table |
|---|---|---|
| `pra-eq-raw.csv` | `raw_data_for_bscr_splits_eq!A:G` | H:P; `Table2` |
| `pra-eq-aggregate.csv` | `pivot_eq!A:E` | F:M; `Table32` |
| Approved all-peril aggregate | `pivot_allperil!A:E` | F:M; `Table3` |

Resize tables to the new rows; leave no stale data. Reconcile earthquake raw
and aggregate `pml` totals.

## 4. Check pivots and results

- The checked-in earthquake pivots use the **wrong, all-peril cache**. With the
  approved correction, point them to `Table32`; all-peril pivots use `Table3`.
- Confirm the approved value field and currency basis before refreshing.
  Refresh only approved pivots, then recalculate in Excel.
- Stop on mapping/formula errors, missing rows or unexplained differences.
  Reconcile against independent totals for this reporting period.

## 5. Complete all-peril and hand off

The all-peril producer is **not confirmed**. The technical reference includes
an experimental `1/1` extraction command; do not treat it as an approved source.
Once the owner approves a producer, load its five-column aggregate using the
table above and repeat the checks. No all-peril raw load destination is documented.

Transfer reviewed pivot values only using an approved final-template cell map.
Record each transfer and reviewer sign-off using the run checklist. The workbook's
legacy BSCR panels are incomplete aids, not final PRA outputs.

For formulas, historical totals and diagnostics, use the
[technical reference](technical-contract.md). For the known transfer boundary,
use the [handoff trace](handoff.md).

# PRA aggregates

## Summary

- **Sources:** approved January EDM and mappings in `pra/workbooks/PRA_BSCR_Aggs.xlsx`.
- **Calculation:** PRA exports from `bscr/BSCR_UKEU.py`, then workbook formulas and pivots.
- **Final workbook/output:** `pivot_eq` and `pivot_allperil`; the final PRA return workbook is external.
- **Time estimate:** included in 1 day for PRA and BSCR together.

## Purpose and scope

`pra/workbooks/PRA_BSCR_Aggs.xlsx` is a combined calculation workbook. It produces PRA geography/class pivots and also contains separate BSCR earthquake-split panels. It is not the final PRA submission template.

The current Python route produces controlled regeneration candidates. The workbook also contains a legacy SQL route, and `pra/sql/aggs-from-edm.sql` matches that embedded query family. Neither route proves how the checked-in cached tables were populated because no prior run record is embedded in the workbook.

The legacy workbook route records `HISCO_UKEU_01JAN26_010126_ROLLUP_ByLoB_GC_v25`, while the Python script currently defaults to `HISCO_UKEU_01JAN26_010126_ROLLUP_ByLOB_GC_v25_EDM`. Select the approved database explicitly and record it; do not treat either hard-coded name as approval.

## Workbook structure

| Sheet | Role |
|---|---|
| `region_mappings` | Country/territory to Standard Formula and PRA region mapping |
| `pivot_allperil` | January baseline 838-row aggregate table, PRA formulas, and all-peril pivots |
| `pivot_eq` | Separate January baseline 838-row aggregate table, the same formula family, and earthquake pivots |
| `raw_data_for_bscr_splits_eq` | January baseline 270,675-row earthquake input, retention/geography flags, and BSCR Schedule X(c) panels |
| `cds_mapping` | Portfolio/CDS class lookup |
| `rms_geog` | RMS country and region lookup |
| `sql` | Legacy aggregate extraction query using peril `2` and policy type `2` |

The row counts above describe the checked-in January evidence. They are comparison points, not fixed sizes for a future run.

## Calculation mechanics

The current Python PRA query:

1. selects `loccvg` rows for the approved peril;
2. sums coverage `valueamt` by location and deductible grouping;
3. sets the location amount to zero when the summed value is below `deductamt`;
4. groups those values to account/geography;
5. joins the selected policy type and caps the amount using the query's `partof`/`blanlimamt` policy-limit logic; and
6. writes either the seven-column raw workbook grain or the five-column pivot-input grain.

The January SQL does **not** subtract the deductible from the amount and does **not** allocate an account PML to locations by TIV. Preserve this behavior for reconciliation unless a reviewed code change is approved.

The PRA input-table formulas derive:

- Fine Art classification from `uwritrname`;
- country display and US country/state labels;
- PRA region from `region_mappings`;
- CDS class from `cds_mapping`; and
- `Agg_USD = pml * 1.25`.

The `1.25` factor belongs to the workbook calculation. Confirm its currency basis and approval for the cycle before relying on the USD result.

## Run earthquake

From the repository root:

```bash
uv sync
uv run python bscr/BSCR_UKEU.py \
  --server '<approved-server>' \
  --database '<approved-edm>' \
  --peril 2 \
  --policy-type 2 \
  --output outputs/bscr-2-2-control.csv \
  --source-output outputs/bscr-2-2-source.csv \
  --pra-raw-output outputs/pra-eq-raw.csv \
  --pra-aggregate-output outputs/pra-eq-aggregate.csv
```

Retain all four CSVs with the server, database, codes, script revision, execution date, operator, row counts, and totals. The BSCR-shaped files are controls for the same selected source; the two PRA files are the workbook inputs.

## Load earthquake data

1. Open a controlled copy of `pra/workbooks/PRA_BSCR_Aggs.xlsx`.
2. Record the current formulas, table ranges, pivot sources, calculation mode, mappings, and pre-refresh totals.
3. Clear only the previous input rows in `raw_data_for_bscr_splits_eq!A:G`; preserve row 1, formulas H:P, panels to the right, tables, and formatting. Column Q is currently unused.
4. Paste `pra-eq-raw.csv` into `raw_data_for_bscr_splits_eq!A:G` in the existing header order.
5. Fill formulas H:P through the last pasted row and check for blanks or Excel errors.
6. Clear only the prior aggregate input rows in `pivot_eq!A:E`; preserve formulas F:M and the pivot areas.
7. Paste `pra-eq-aggregate.csv` into `pivot_eq!A:E` and fill formulas F:M through the last pasted row.
8. Reconcile raw `pml`, grouped aggregate `pml`, and the completed input-table totals before refreshing pivots.

## Refresh earthquake pivots

The checked-in `pivot_eq` pivots currently point at the all-peril cache. In Excel, change every pivot on `pivot_eq` to use `Table32`, confirm that the table covers the complete earthquake input, then refresh the intended pivots.

Use **Data > Refresh All** only after checking that it will not update unapproved external connections. Recalculate the workbook, check for `#REF!`, `#N/A`, and `#VALUE!`, and compare the before/after pivot values.

The checked-in January earthquake source total is `233,586,155,482.80`. Record its currency/unit and treat it as a comparison baseline, not an acceptance tolerance. Stop if the selected source, raw CSV, aggregate CSV, or workbook input does not reconcile to it.

## Earthquake output

The PRA earthquake results are on `pivot_eq`. Reconcile the source input through formulas and pivots, then record the exact output range used for the external PRA template.

The `raw_data_for_bscr_splits_eq` sheet also identifies HIG, `_QS`, `_SRP`, North American hurricane, and North American earthquake rows. Panels to the right calculate values intended for a BSCR Schedule X handoff. `_QS` uses `50%`; `_SRP` uses `33%` in this workbook.

Those BSCR panels overlap the separate Python and BSCR-workings route. Neither automatically supersedes the other. Reconcile and obtain owner approval before selecting final BSCR values.

## All-peril candidate

The repository does not contain the confirmed producer or population record for the checked-in all-peril table. The first regeneration candidate is the current query with codes `1/1`:

```bash
uv run python bscr/BSCR_UKEU.py \
  --server '<approved-server>' \
  --database '<approved-edm>' \
  --peril 1 \
  --policy-type 1 \
  --output outputs/bscr-1-1-control.csv \
  --source-output outputs/bscr-1-1-source.csv \
  --pra-raw-output outputs/pra-allperil-raw-candidate.csv \
  --pra-aggregate-output outputs/pra-allperil-candidate.csv
```

Do not load this result merely because the command succeeds. Confirm that codes `1/1` represent the approved all-peril scope, compare row counts and classifications, and reconcile the aggregate candidate to the checked-in source total `255,773,631,164.60`.

Only after that reconciliation and owner approval:

1. clear the old input rows in `pivot_allperil!A:E` without disturbing formulas or pivots;
2. paste `pra-allperil-candidate.csv` into A:E;
3. fill formulas F:M through the complete range;
4. confirm each pivot points to the intended all-peril table; and
5. refresh, recalculate, and reconcile the output.

Otherwise stop and preserve the existing all-peril table as evidence.

## Required controls

- Record how both aggregate tables were populated and retain their producer outputs.
- Confirm the `1.25` factor and the versions of `region_mappings`, `cds_mapping`, and `rms_geog`.
- Resolve the `_SRP` difference between `33%` here, `0.3333` in Python, and `0.33333` in supplementary SQL.
- Reconcile raw input, grouped input, formulas, pivots, and final return values.
- Preserve formulas, table definitions, pivot sources, validation, formatting, and non-input cells.
- Do not use cached pivot similarity as proof of current lineage or approval.

## Controlled handoff

No final PRA template is checked in, so its destination and green-cell addresses remain unresolved until the controlled template is supplied.

For every PRA or overlapping BSCR value, retain the query/script version, source workbook and range, mapping/rate versions, destination workbook/cell, amount, currency, unit, as-of date, preparer, reviewer, and review date.

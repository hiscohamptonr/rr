# PRA aggregates — operator and manager guide

## Start here: what this process does

This guide contains the setup, files, operating steps, checks and stop conditions. No other document is required to understand the workflow.

**Result:** reviewed earthquake and all-peril aggregates in `pra/workbooks/PRA_BSCR_Aggs.xlsx`. This is a calculation workbook, not the final PRA return.

**Current status:** the materials describe January 2026, not approval for a new reporting cycle. The all-peril producer, pivot correction/value fields, currency/mapping rules and final-template handoff remain unapproved. Never use cached January values as a new return.

## 1. Files and tools

Paths below are relative to the repository folder.

| File | Purpose |
|---|---|
| `pra/workbooks/PRA_BSCR_Aggs.xlsx` | Calculation workbook; work on a copy in a new restricted run folder |
| `pra/sql/pra-earthquake.sql` | Parameterized five-column aggregate extraction |
| Final PRA template | Must be supplied and approved by the return owner; not checked in |
| `docs/generated/Regulatory-Returns-Operator.xlsx` | Optional import/control template, not the PRA calculation workbook |

Use desktop Excel and approved SQL Server access, normally integrated authentication. The existing run setup specifies ODBC Driver 18; Excel/Power Query manages its own connector. The optional operator workbook has **no embedded Power Query connections**. It is not a one-click extraction tool. Operators do not need Python or `uv` for the intended Excel-first route, but an approved separate raw-input producer is still required.

If a workbook fails to open, preserve the original, retain Excel's error/repair log and try a fresh raw download under a new local filename. Repair a duplicate only; check formulas, tables and pivots before using a repaired copy.

## 2. Manager: authorize the run

Record the reporting period, approved EDM server/database snapshot, peril/policy codes, mappings, retention/proxy rules, FX, units and controlled template. Name the operator and reviewer; record query/code revision and a restricted run folder. Agree independent control totals and acceptable differences. Keep credentials out of the record.

Close these decisions before the affected step:

| Blocker | Required decision or artifact |
|---|---|
| Earthquake raw input | Approve a producer of the seven-column raw input; the canonical SQL below supplies only the five-column aggregate |
| All-peril input | Confirm producer, population and scope; neither an experimental `1/1` route nor a `4/4` query candidate is approved by this guide |
| Workbook calculation | Approve pivot sources/value fields, currency, mapping-error treatment and NAHU/retention alignment |
| Final handoff | Supply the current PRA template and approved source-range to destination-cell map, including measure, currency/unit and reviewer |

## 3. Extract earthquake inputs

In the approved SQL client, connect to the approved snapshot and open `pra/sql/pra-earthquake.sql`. Confirm `@peril` and `@policy_type`; January earthquake used `2/2`. Change parameters only, not calculation logic. Execute and export with headers. Retain the query revision, parameters, row count and control totals.

**This SQL produces the five-column aggregate only:**

```text
pml, state, userid1, cntrycode, uwritrname
```

Save the reviewed export as `pra-eq-aggregate.csv`. It does **not** also produce the separate raw input required by the workbook:

```text
pml, accgrpid, uwritrname, state, userid1, branchname, cntrycode
```

The existing technical producer `bscr/BSCR_UKEU.py` has separate `--pra-raw-output` and `--pra-aggregate-output` options. The technical owner must supply and approve the raw export as `pra-eq-raw.csv`, or approve an equivalent producer. Use the same approved snapshot and parameters for both inputs. Do not reconstruct raw rows from an aggregate or paste the aggregate into the raw tab.

Check output headers/order, row counts, required nulls, duplicate keys at the approved grain and join multiplication. Reconcile raw and aggregate `pml` totals. Stop on failed/partial output or an unavailable required producer.

## 4. Load the calculation workbook

Inspect input ranges, formulas, tables, pivot sources and external links first. Clear old input rows only; keep headers and report areas. Paste **data without headers**, starting at row 2:

| Input | Destination | Preserve and extend |
|---|---|---|
| Approved `pra-eq-raw.csv` | `raw_data_for_bscr_splits_eq!A:G` | Formulas H:P and `Table2` |
| Approved `pra-eq-aggregate.csv` | `pivot_eq!A:E` | Formulas F:M and `Table32` |
| Approved all-peril five-column aggregate | `pivot_allperil!A:E` | Formulas F:M and `Table3` |

Resize tables to cover all new rows and remove stale input rows. Do not overwrite formulas or copy known inconsistent formulas into new rows. No all-peril raw destination is documented; do not invent one.

## 5. Correct approved pivots, then refresh

The checked-in earthquake pivots use the **wrong all-peril cache**. Under the owner's approved correction, point earthquake pivots to `Table32`; all-peril pivots use `Table3`. Confirm value fields and currency/unit basis before refreshing. Do not blindly refresh external links.

Refresh only approved pivots, recalculate in desktop Excel, and reconcile source → raw/aggregate inputs → formula/table totals → pivots by the relevant entity, geography and peril. Investigate mapping errors, missing rows, Excel errors and unexplained movements. Use current-period independent controls, not January cached totals as a target.

Stop if the pivot correction, source, measure or currency cannot be traced, or a difference exceeds the reviewer's tolerance.

## 6. Complete all-peril and transfer

All-peril work remains blocked until the owner approves its producer and population. The same SQL can technically be parameterized with `4/4`, while historical technical instructions also describe an experimental `1/1` candidate. Neither establishes the required all-peril scope. The operator must not choose between them without approval.

After approval, load the five-column all-peril aggregate into the destination above and repeat the table, formula, pivot and reconciliation checks.

Transfer reviewed results only using an approved final-template map. The final PRA template and approved map are not checked in. Do not infer destination cells from formatting, matching labels, cached values or legacy BSCR panels; those panels are incomplete aids, not final PRA outputs.

For each transfer, record source file/sheet/range, destination file/sheet/cell, value, measure, currency/unit, as-of date, assumption versions and reviewer. Recalculate and reconcile the final template, then obtain reviewer sign-off.

## 7. Retain the run evidence

Keep raw and aggregate exports, calculation/final workbooks, query/code revision, server/database, parameters, row counts, control totals, mapping/FX versions, exception decisions, reconciliations, transfer records and sign-off together in the restricted run folder, not source control. Keep credentials out of all evidence.

**A successful query or pivot refresh is not a completed or approved PRA return.**

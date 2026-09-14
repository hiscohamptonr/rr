# BSCR Schedule X — operator and manager guide

## Start here: what this process does

This guide contains the setup, file list, operating steps, checks and stop conditions. No other document is required to understand the workflow.

**Result:** reviewed exposure inputs for HIC Schedule X, not a complete return. EP curves, premiums, narratives, model classifications and distinct contract counts require separately approved sources.

**Current status: not an unattended or production-approved Excel refresh.** The checked-in materials describe the January 2026 implementation. The source-to-workbook transformation, static consolidation, calculation assumptions and final-template handoff need approval before the affected steps can run.

## 1. Files to open

All paths below are relative to the repository folder. Make working copies in a new restricted run folder; never overwrite the originals.

| File | Purpose |
|---|---|
| `bscr/workbooks/Workings_with_geocodingFW - Including blanks USD.xlsx` | Calculation workbook: input, formulas, consolidation and reporting pivots |
| `bscr/workbooks/2026 BSCR - UKEU - HIC.xlsx` | Final template; confirm the approved current-cycle version |
| `bscr/sql/bscr-extract.sql` | Parameterized SQL source extraction, not a workbook-ready seven-column export |
| `docs/generated/Regulatory-Returns-Operator.xlsx` | Optional import/control template, not the calculation workbook and not a connected extraction tool |

The calculation workbook and HIC template are **not formula-linked**. Updating one does not populate the other. The optional operator workbook has no embedded Power Query connections.

### If the workings workbook will not open

Stop the load. Keep the failing file unchanged and retain Excel's exact error and any repair log. Download a fresh raw workbook file, save it locally under a new name and try desktop Excel. Repair a duplicate only. Any repaired copy needs formula and pivot checks before use.

The repository copy passes ZIP/XML integrity checks and loads with a spreadsheet parser. That is not proof of a clean desktop Excel open or successful recalculation; desktop Excel verification remains outstanding.

## 2. Manager: authorize the run

Before the operator changes any inputs, record:

- Reporting period, approved EDM server/database snapshot and current-cycle template.
- Approved peril and policy codes; January used `1/1`, not an automatic default for another cycle.
- Approved entity/geography mappings, retention rules, FX and units.
- Operator, reviewer, query/code revision, run folder and assumption versions.
- Independent control totals and acceptable differences.

Operators need desktop Microsoft Excel and approved SQL Server access, normally integrated authentication. The existing run setup specifies ODBC Driver 18; Excel/Power Query manages its own connector. Do not store credentials in files or logs. Operators do not need Python or `uv` for the intended Excel-first route, but that route is not complete until an approved workbook-ready producer is supplied.

### Decisions the manager must close

| Blocker | Required decision or artifact |
|---|---|
| Source transformation and calculation rules | Approve policy join/grain diagnostics, geography and retention rules, FX, and a producer of the seven-column workbook input |
| Static consolidation | Approve how `Sheet1` becomes `output!A:F`: grouping keys, aggregation, clearing old groups, formula coverage and reconciliation |
| Final handoff | Approve source ranges to HIC destination cells, measures, currency/units and supplemental sources, including distinct-contract methodology |
| HIC template | Resolve documented `#REF!` formulas and old external links; approve the current-cycle template |

Do not ask the operator to infer these decisions from cell colours, cached values or prior-year layouts.

## 3. Extract source data — do not paste it directly into Sheet1

In the approved SQL client, connect to the approved snapshot, open `bscr/sql/bscr-extract.sql`, and set `@peril` and `@policy_type` to the approved cycle values. Execute without changing calculation logic. Export with headers and retain the query revision, parameters, row count and source control totals.

**The SQL returns eight source columns:**

```text
pml, accgrpid, uwritrname, state, userid1, branchname, cntrycode, is_geocoded
```

**The calculation workbook requires seven transformed columns, in this order:**

```text
cntrycode, bscr_entity, region, sum_pml, sum_net, count_policies, is_geocoded
```

These are not interchangeable. Renaming or deleting headers does not perform the required entity, region, retention and aggregation calculations.

The existing technical producer is `bscr/BSCR_UKEU.py`, which can produce `bscr-output.csv` and a separate source export. A technical owner must supply and approve the workbook-ready output, or approve an equivalent SQL/Power Query implementation. This guide does not imply that `bscr-extract.sql` alone implements that transformation. **If only the eight-column SQL export is available, stop before loading Excel.**

Check headers/order, row count, nulls, duplicate keys at the approved grain, join multiplication and source totals. A failed query or partial export is a stop condition.

## 4. Load the calculation workbook

Only continue with an approved seven-column `bscr-output.csv` and an approved consolidation procedure.

1. Open the working copy. Review `AUDIT_SUMMARY`, input ranges, formulas and pivot sources without refreshing external connections.
2. Clear old input rows in `Sheet1!A:G` only. Keep the header row.
3. Paste CSV data **without headers**, starting at `Sheet1!A2`.
4. Preserve and extend formulas `H:K` through every new row. Remove stale input rows. `Sheet1` is not an Excel table; do not create one.
5. Check the workbook's `1.35` conversion and `/1,000,000` scaling against the approved currency/unit basis. Do not silently reuse an old FX assumption.
6. **Stop at `output!A:F` unless the approved consolidation procedure is available.** These are static values: loading `Sheet1` does not update them.
7. Rebuild `output` using that procedure, preserving the approved formulas in `G:J` and reconciling all groups.
8. Check approved pivot sources, refresh the relevant pivots and recalculate in desktop Excel. Do not blindly refresh external links.

### Known workbook cautions

The checked-in reporting pivots use `output!A1:J50`, while the sheet extends to row 82. Review whether rows beyond 50 belong in the approved source; do not automatically include them. The pivot on `Sheet1` references `A1:K1048576`, which also requires review before refresh.

The audit sheet says the reporting pivot is older than `Sheet1`. Its instruction to refresh `output` is insufficient because the bridge is static. Its `docs/index.md` reference is outdated. Follow the procedure in this guide, not the audit sheet alone. Snapshot dimensions are not future load limits.

## 5. Reconcile the results

Reconcile **source export → approved seven-column output → Sheet1 → rebuilt output → piv**. Use the same approved currency, units, mappings and reporting period.

- Check gross, net and contributing-row counts by entity, region and geocode classification.
- Investigate missing mappings, formula errors, unexpected rows and unexplained movements.
- Regional views overlap: do not add them together. `ALL` is a separate view.
- `count_policies` counts grouped source rows, not distinct contracts. It cannot alone supply Schedule X(f).
- Stop when a range, transformation, FX basis or difference cannot be explained, or a difference exceeds the reviewer's tolerance.

## 6. Transfer, sign off and retain evidence

Transfer reviewed values only through an approved map naming each source workbook/sheet/range and HIC destination sheet/cell. No approved final-cell map is supplied by this repository. Do not choose cells by colour or label, or overwrite formulas/non-input areas.

For each transfer, record value, measure, currency/unit, as-of date, assumption versions, preparer and reviewer. Recalculate the final workbook and reconcile destination totals. Obtain reviewer sign-off.

Keep working and final workbooks, raw and transformed exports, query/code revision, server/database, parameters, row counts, control totals, reconciliation, exception decisions, transfer record and sign-off together in the restricted run folder. Keep credentials out of the record.

**Finish means reviewed inputs and an approved handoff, plus the separately sourced Schedule X requirements—not merely a refreshed pivot.**

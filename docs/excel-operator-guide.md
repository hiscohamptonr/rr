# Excel-first operator workflow

This is the supported operator workflow. It does not require Python, `uv`, or a local development environment.

## Required tools

- Microsoft Excel with Power Query enabled
- Approved SQL Server access (normally Windows integrated authentication)
- An approved SQL Server snapshot and current-cycle mappings
- The checked-in calculation workbook for the relevant return

The operator must not edit SQL logic, workbook formulas, or final-template structure during a run.

## Configure once per workbook

Open the workbook's `Config` sheet and record:

| Setting | BSCR/PRA default | Global Exposures default |
|---|---|---|
| SQL Server | approved EDM server/instance | approved GlobalExposures server |
| Database | approved EDM snapshot | `GlobalExposures` |
| Driver | Excel/Power Query managed | Excel/Power Query managed |
| Peril | approved cycle code | approved event peril |
| Policy type | approved cycle code | approved EDM policy type |
| Reporting period | approved value | approved value |

Use the workbook's Power Query connection properties to select the server and database. Do not place credentials in the workbook or run log.

## Refresh sequence

1. Save a new copy of the workbook in a new run folder.
2. Complete the run checklist and record the snapshot, query revision, operator, and reviewer.
3. Refresh the raw SQL query only.
4. Check the raw row count, headers, nulls, duplicate keys, and source control totals.
5. Refresh the calculation queries/formulas.
6. Review the `Exceptions` and `Controls` sheets. Any unexplained exception is a stop condition.
7. Reconcile source totals to grouped totals by entity, peril, geography, currency, and relevant workbook destination.
8. Transfer reviewed values to the final template using the approved handoff map.
9. Recalculate in Excel and obtain reviewer sign-off.

A successful refresh is not approval and does not prove that the return is complete.

## SQL assets

- `bscr/sql/bscr-extract.sql` — BSCR source extraction; review `@peril` and `@policy_type`.
- `pra/sql/pra-earthquake.sql` — PRA earthquake source extraction; review the hard-coded cycle codes before execution.
- `lloyds/sql/*.sql` — Lloyd's supplementary source routes; execute in the approved SQL client and retain exported results.
- `dataiku/Dataiku-Aggs.sql` — Dataiku/Databricks SQL only; not a SQL Server query.

Global Exposures remains a spatial calculation. It requires an approved SQL Server spatial implementation before it can be represented as a pure Excel refresh. Do not replace it with worksheet point-in-polygon formulas.

## Evidence to retain

Keep the workbook, exported raw query results, query revision, server/database, reporting period, row counts, control totals, exception review, reconciliation, and reviewer sign-off together. Keep credentials out of all evidence.

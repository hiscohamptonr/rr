# BSCR Schedule X runbook

## Data sources

- Configured SQL Server EDM tables `loccvg`, `loc`, `policy`, and `accgrp`.
- [`BSCR_UKEU.py`](BSCR_UKEU.py).
- [`Workings_with_geocodingFW - Including blanks USD.xlsx`](Workings_with_geocodingFW%20-%20Including%20blanks%20USD.xlsx).
- [`2026 BSCR - UKEU - HIC.xlsx`](2026%20BSCR%20-%20UKEU%20-%20HIC.xlsx).
- Current BSCR instructions, approved mappings, rate set, and return-owner decisions.

## Requirements

- Python 3.13+ and `uv`.
- Trusted Microsoft/Windows access to the selected SQL Server EDM.
- ODBC Driver 18 for SQL Server.
- Approved database, reporting scope/date, mappings, retention, currency basis, and output location.

## Install and inspect

```bash
uv sync
uv run python bscr/BSCR_UKEU.py --help
```

`--help` does not connect to SQL Server.

## Pre-run controls

1. Record server, EDM database, reporting date, roll-up/version, script revision, operator, and reviewer.
2. Approve `peril = 1`, `policytype = 1`, deductible/limit logic, joins, and grouping grain.
3. Resolve the known `is_nahu()` defect and approve entity/geography mappings before a production run.
4. Approve `_QS` and `_SRP` factors; `_SRP` differs across Python, SQL, and workbook artefacts.
5. Confirm source currency and the workings workbook's hard-coded `1.35` conversion.
6. Freeze the controlled copies of both workbooks and verify their formulas, pivot ranges, external links, and green cells.

## Run

```bash
uv run python bscr/BSCR_UKEU.py \
  --server 'SQLSERVER\INSTANCE' \
  --database APPROVED_EDM_DATABASE \
  --output outputs/bscr-output.csv
```

Optional connection controls:

```text
--encrypt {yes,no}
--trust-server-certificate {yes,no}
```

Do not weaken connection security merely to make a run succeed. The script tests the connection, executes the embedded query, prints selected-source diagnostics, and writes the CSV. An existing output path may be replaced.

## Output contract

```text
cntrycode,bscr_entity,region,sum_pml,sum_net,count_policies,is_geocoded
```

The CSV contains all configured entities. It performs no currency conversion and has no currency column.

## Workbook handoff

1. Preserve the raw CSV and its run metadata.
2. Load the seven CSV columns into `Sheet1` A:G of a controlled copy of the workings workbook; preserve formula columns.
3. Confirm the formulas applying `1.35` and `/1,000,000` are approved and filled for every input row.
4. Refresh only the intended `output` and `piv` ranges.
5. Reconcile query, CSV, `Sheet1`, `output`, and `piv` gross/net totals and row counts.
6. Enter reviewed results into the designated green cells in HIC Schedules X(a), X(b), X(c), and X(f).
7. Record source range, destination cell, value, currency, unit, as-of date, preparer, and reviewer for every entry.
8. Check stale external links before sign-off; the HIC workbook currently references older external templates.

The final HIC workbook is not formula-linked to the workings workbook. Do not describe the manual transfer as automated.

## Troubleshooting

### SQL connection failure

- Confirm trusted access to the exact server and database.
- Confirm ODBC Driver 18 and the instance name.
- Use only approved encryption/certificate settings.
- Do not add credentials to source control.

The script has no CSV-input fallback. Adding one requires a controlled code change, schema validation, and reconciliation.

### Implausible totals

Treat the run as failed. Review join cardinality, mixed currencies, unmapped entities, overlapping geography flags, geocoding, row-based counts, deductible/limit logic, and retention before workbook handoff.

See the [BSCR process guide](../docs/regulatory-returns/bscr.md) and [complete data-flow map](../docs/regulatory-returns/data-flow.md).

# Global Exposures

## Summary

- **Sources:** `GlobalExposures` event/polygon/PML tables and the approved annual EDM.
- **Calculation:** `globalexposures/exposures.py`.
- **Final workbook/output:** CSV output pack under `global_exposures_outputs/`; there is no final Excel workbook.
- **Time estimate:** 2 days.

## Purpose and sources

Global Exposures intersects EDM locations with configured event polygons, applies polygon PML values, and writes a queryable CSV output pack. It does not use an Excel calculation workbook.

| Source | Role |
|---|---|
| `GlobalExposures.data.Events` | Event identifiers, names, and descriptions |
| `GlobalExposures.data.ShapeFiles` | Ordered latitude/longitude points defining each event polygon |
| `GlobalExposures.data.PML` | Polygon-level PML factors |
| Approved annual EDM | `dbo.loc`, `dbo.loccvg`, `dbo.policy`, `dbo.accgrp`, `dbo.portacct`, and `dbo.portinfo` exposure records |

The script does not read input spreadsheets or flat files. Database defaults are defined in `RunConfig` in `globalexposures/exposures.py`; approve and record them for every run.

The EDM query applies the selected peril to both `loccvg.PERIL` and `policy.POLICYTYPE`. It also applies Fine Art QS/SRP factors from portfolio-name patterns. Review the annual schema, code meanings, portfolio selection, and reinsurance factors before production use.

## Install and inspect

From the repository root:

```bash
uv sync --project globalexposures
uv run --project globalexposures python globalexposures/exposures.py --help
```

`--help` does not connect to either database.

## Pre-run record

Record the Global Exposures and EDM server/database identities, reporting date, script revision, complete command, selected event(s), peril, optional portfolio, output directory, operator, and reviewer.

Confirm event/polygon/PML completeness, WGS84 coordinate assumptions, selected EDM, portfolio scope, policy/peril code, retention factors, and handling of missing PML before execution.

## Run

Run every configured event:

```bash
uv run --project globalexposures python globalexposures/exposures.py \
  --output-dir global_exposures_outputs
```

Run one event or override controlled inputs:

```bash
uv run --project globalexposures python globalexposures/exposures.py \
  --event-id 123 \
  --peril 4 \
  --portnum PORTFOLIO_NUMBER \
  --output-dir global_exposures_outputs
```

Use `--all-events` to override a single-event default. Use `--allow-missing-pml` only when the run owner has approved incomplete polygon PML data; the default is to fail the affected event.

The script uses trusted SQL Server connections. It exits with status `1` for a pipeline-level failure and status `2` when one or more selected events fail. A run with event failures is not complete merely because some CSVs were written.

## Input and refresh

There is nothing to paste into Excel. The database queries are the input, and rerunning the controlled command is the refresh process. A selected run rewrites its output pack, so preserve reviewed prior outputs separately before rerunning.

## Output pack

The default folder is `global_exposures_outputs/`. Output names use `all_events` or the selected event ID as a prefix where applicable.

| File | Use |
|---|---|
| `*_summary.csv` | Overall run result and event counts |
| `*_run_log.csv` | Status for each selected event |
| `*_error_log.csv` | Event failures and investigation trail |
| `*_location_rows.csv` | Detailed impacted exposure rows |
| `*_account_breakdown.csv` | Account-level totals |
| `*_location_breakout.csv` | Location-level totals |
| `edm_exposures.csv` | EDM exposure extract used by the run |

Start with `*_summary.csv` and `*_run_log.csv`. Investigate every error-log row, then reconcile account and location outputs to the preserved EDM extract before use.

Preserve the complete output pack with the exact script revision, database identities, CLI arguments, event selection, row counts, totals, operator, reviewer, and reconciliation evidence.

## Material controls

- Reconcile event counts and polygon IDs across `Events`, `ShapeFiles`, and `PML`; missing PML fails an event by default.
- Confirm polygon point ordering, polygon validity, location coordinates, and the WGS84 CRS assumption.
- Review EDM joins for row multiplication and unmatched locations/accounts/policies.
- Reapprove `_QS`/`_SRP` name matching and factors whenever terms or portfolio naming changes.
- Reconcile the EDM extract to location rows, location breakouts, account totals, and final summary totals.
- Confirm failed events are absent or explicitly approved; do not combine partial output with a successful prior run.
- Keep database and event inputs, generated outputs, and review evidence together as one run pack.

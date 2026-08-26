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

The EDM query applies the selected peril to both `loccvg.PERIL` and `policy.POLICYTYPE`. Its current Fine Art QS/SRP factors match `PORTNUM` with SQL `LIKE` patterns (where `_` is a wildcard), not `PORTNAME`. Review the annual schema, code meanings, portfolio selection, and reinsurance factors before production use.

For the current code's exact joins, calculations, spatial rules, status
semantics, and machine-checkable controls, see
[global-exposures-for-llm.md](global-exposures-for-llm.md). It documents
observed implementation, not approval of its calculation logic.

See the repository [calculation discrepancy register](../../docs/calculation-discrepancies.md)
for the exact evidence and owner decisions.

## Current production blockers

Do **not** treat a successful command as an approved result. Escalate before a
production run until the owner has approved or corrected these observed
behaviours:

- the code multiplies location TIV by `MAX(BLANLIMAMT)` per account, treating a
  field named as a monetary limit as a factor, and defaults a missing policy
  match to `1`;
- unfiltered portfolio membership can duplicate locations; the saved
  `edm_exposures.csv` is already post-join and cannot prove that this did not
  happen;
- `--allow-missing-pml` can report success while aggregate loss totals turn
  unknown PML loss into zero; and
- empty extracts, unusable coordinates, no polygons, or no impacts can exit
  successfully without proving an approved zero result.

Until code controls exist, use a new empty output directory for each validation
run, do not use `--allow-missing-pml`, retain pre/post-join controls produced
outside the script, and treat every non-success event, warning, zero result, or
missing PML as a stop condition.

## Install and inspect

From the repository root:

```bash
uv sync --project globalexposures --locked
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
  --output-dir '<new-run-specific-directory>'
```

Run one event or override controlled inputs:

```bash
uv run --project globalexposures python globalexposures/exposures.py \
  --event-id 123 \
  --peril 4 \
  --portnum PORTFOLIO_NUMBER \
  --output-dir '<new-run-specific-directory>'
```

Use `--all-events` to override a single-event default. Do not use
`--allow-missing-pml` in a production calculation: the current aggregation can
turn unknown PML losses into zero while retaining a success status. The default
is to fail the affected event.

The script uses integrated SQL Server authentication. Confirm its ODBC driver
and certificate-trust settings against the approved connection policy. It exits
with status `1` for a pipeline-level failure and status `2` when one or more
selected events fail. A run with event failures is not complete merely because
some CSVs were written.

## Input and refresh

There is nothing to paste into Excel. The database queries are the input, and
rerunning the controlled command is the refresh process. A selected run
overwrites files individually and is not an atomic publication. Use a new
empty, run-specific directory for every run; do not regard a reused directory
as a coherent output pack.

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

Start with `*_summary.csv` and `*_run_log.csv`. The current summary contains
statuses and row counts, not final monetary totals. Investigate every error-log
row and every zero/no-polygon/no-impact result, then reconcile account and
location outputs to independently preserved pre-join EDM controls before use.

Preserve the complete output pack with the exact script revision, database identities, CLI arguments, event selection, row counts, totals, operator, reviewer, and reconciliation evidence.

## Material controls

- Reconcile event counts and polygon IDs across `Events`, `ShapeFiles`, and `PML`; missing PML fails an event by default.
- Confirm polygon point ordering, polygon validity, location coordinates, and the WGS84 CRS assumption.
- Review EDM joins for row multiplication and unmatched locations/accounts/policies.
- Reapprove `_QS`/`_SRP` name matching and factors whenever terms or portfolio naming changes.
- Reconcile independently preserved pre-join EDM controls to location rows,
  location breakouts, and account totals; the current summary has no monetary
  totals to reconcile.
- Require approved zero-impact evidence for an empty extract, no usable
  coordinates, no polygons, or no impacted exposures; these states are not
  inherently successful outcomes.
- Treat overlapping polygons, boundary locations, duplicate polygon/PML keys,
  and repaired geometries as owner decisions. The current code retains one
  intersecting polygon, preferring highest PML and then lowest polygon ID.
- Confirm failed events are absent or explicitly approved; do not combine partial output with a successful prior run.
- Keep database and event inputs, generated outputs, and review evidence together as one run pack.

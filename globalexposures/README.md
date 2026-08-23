# Global Exposures

## Data sources

- `GlobalExposures.data.Events`: event identifiers, names, and descriptions.
- `GlobalExposures.data.ShapeFiles`: ordered latitude/longitude points defining each event polygon.
- `GlobalExposures.data.PML`: polygon-level PML factors.
- The configured annual SQL Server EDM: `dbo.loc`, `dbo.loccvg`, `dbo.policy`, `dbo.accgrp`, `dbo.portacct`, and `dbo.portinfo`.

The script does not read input spreadsheets or flat files. Database server and
database defaults are defined in `RunConfig` in
[`exposures.py`](exposures.py); approve them for each run.

## Purpose

`exposures.py` is an ordinary Python command-line script that intersects EDM
locations with configured event footprints, applies polygon PML values, and
writes a queryable CSV output pack.

The checked-in EDM query applies the selected peril to both `loccvg.PERIL` and
`policy.POLICYTYPE`. It also implements Fine Art QS/SRP factors from portfolio
name patterns. Review the annual EDM schema, peril code, portfolio selection,
and reinsurance factors before production use.

## Install and inspect

From this directory:

```bash
uv sync
uv run python exposures.py --help
```

`--help` does not connect to either database.

## Run

Run every configured event:

```bash
uv run python exposures.py
```

Run one event or override controlled inputs:

```bash
uv run python exposures.py \
  --event-id 123 \
  --peril 4 \
  --portnum PORTFOLIO_NUMBER \
  --output-dir global_exposures_outputs
```

Use `--all-events` to override a single-event default. Use
`--allow-missing-pml` only when the run owner has approved incomplete polygon
PML data; the default is to fail the affected event.

The script uses trusted SQL Server connections. It exits with status `1` for a
pipeline-level failure and status `2` when one or more individual events fail.

## Outputs

The default output directory is `global_exposures_outputs`. The script writes:

- run summary, run log, and error log CSVs;
- event/location result rows;
- account and location breakouts; and
- the EDM exposure extract used by the run.

Output names use `all_events` or the selected event ID as a prefix where
applicable. Preserve the output pack with the exact script revision, database
identities, CLI arguments, and reconciliation evidence.

## Material controls

- Reconcile event counts and polygon IDs across `Events`, `ShapeFiles`, and
  `PML`; missing PML fails an event by default.
- Confirm location coordinates, event polygon validity, and the WGS84 CRS
  assumption.
- Review the SQL joins for row multiplication and unmatched locations.
- Reapprove Fine Art `_QS` and `_SRP` matching and factors whenever
  reinsurance terms or portfolio naming changes.
- Reconcile the EDM extract, location rows, account totals, and final report
  totals before use.

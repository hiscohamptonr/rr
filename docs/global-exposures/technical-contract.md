# Global Exposures — technical contract

[Start here](../../README.md) · [Runbook](runbook.md) ·
[Shared controls](../operating-controls.md) · [Open decisions](../decisions.md#global-01)

This is the observed implementation contract for `globalexposures/exposures.py`.
It supports review and test design; it is **not** approval to operate the
pipeline in production. The runbook is the only operator route. GLOBAL-01 and
COMMON-01 remain open.

## Inputs and configuration

The default `RunConfig` connects with integrated SQL Server authentication to:

- Global Exposures server `PR0603-41001-00`, database `GlobalExposures`, tables
  `data.Events`, `data.ShapeFiles`, and `data.PML`;
- EDM server `prod-lmrmsinsurance-db\\LMRMSinsurance`, database
  `HISCO_UKEU_01JAN26_010126_ROLLUP_ByLOB_GC_v25_EDM`, tables `dbo.loc`,
  `dbo.loccvg`, `dbo.policy`, `dbo.accgrp`, `dbo.portacct`, and `dbo.portinfo`.

The default ODBC driver is `ODBC Driver 17 for SQL Server`; trusted connection
and server-certificate trust are enabled in the SQL connection string. The
configured peril is `4`, applied to both `loccvg.PERIL` and `policy.POLICYTYPE`.
`event_id_to_run=None` selects all events, `portnum_filter=None` selects all
portfolios, output defaults to `global_exposures_outputs`, and the CRS is
`EPSG:4326`. Missing PML fails an event by default (`fail_on_missing_pml=True`).
CLI arguments override these defaults:

```bash
uv sync --project globalexposures --locked
uv run --project globalexposures python globalexposures/exposures.py --help
uv run --project globalexposures python globalexposures/exposures.py \
  --output-dir '<new-run-specific-directory>'
uv run --project globalexposures python globalexposures/exposures.py \
  --event-id 123 --peril 4 --portnum PORTFOLIO_NUMBER \
  --output-dir '<new-run-specific-directory>'
```

`--event-id` and `--all-events` are mutually exclusive; the default is the
configured event selection, which is all events. `--allow-missing-pml` changes
the missing-PML failure gate and is not an approved production option. The
script consumes no input spreadsheets, flat files, or other external feeds.

## EDM query and calculation

The query first groups `dbo.loccvg.VALUEAMT` by location, account group,
location number, coordinates, country, peril, and currency after filtering the
selected peril. This gives:

```text
GroundUpTIV = SUM(loccvg.VALUEAMT)
```

Policy terms group `dbo.policy` by `ACCGRPID` and `POLICYTYPE`, retaining:

```text
PolicyFactor = MAX(CASE BLANLIMAMT WHEN 0 THEN 1 ELSE BLANLIMAMT END)
```

`BLANLIMAMT` is a field named as a monetary limit, but current code uses it as a
multiplicative factor. A missing policy match is defaulted to `1.0`. The
account/portfolio CTE joins `accgrp` to `portacct` and `portinfo`; an optional
exact `PORTNUM` filter is applied there. Fine Art QS/SRP logic is:

```text
FineArtFactor = 0.5       if PORTNUM LIKE '%_QS'  and PORTNUM LIKE '%_FA_%'
                0.3333333 if PORTNUM LIKE '%_SRP' and PORTNUM LIKE '%_FA_%'
                1.0       otherwise
```

The patterns test `PORTNUM`, not `PORTNAME`; SQL `_` is a single-character
wildcard, not a literal underscore. The selected peril filters coverage and
policy type. For each post-join row:

```text
PolicyAdjustedTIV = GroundUpTIV * COALESCE(PolicyFactor, 1.0) * FineArtFactor
TIV              = PolicyAdjustedTIV       # exported alias
GroundUpLoss     = GroundUpTIV * PML
GULoss           = PolicyAdjustedTIV * PML  # gross_loss_after_policy_terms
```

The policy result is account-level and is joined back to locations. Multiple
`portacct` memberships can therefore multiply location rows. The exported
`edm_exposures.csv` is post-join and cannot prove that duplication did not occur.

## Spatial contract

`ShapeFiles` rows require `EventID`, `PolygonID`, `Lat`, `Long`, and `DrawOrder`.
Points are interpreted as latitude/longitude in the configured WGS84 CRS and
ordered by `DrawOrder` to construct polygons. Invalid geometries are repaired
with `buffer(0)` when possible; polygons with too few usable points may be
dropped. These are observed transformations, not approval to continue.

Exposure rows with null coordinates are dropped. Remaining coordinates outside
latitude `[-90, 90]` or longitude `[-180, 180]` are dropped, then assigned an
internal `_ExposureRowID`. Spatial join uses GeoPandas `predicate='intersects'`,
so a point on a polygon boundary counts as impacted.

If one exposure intersects several polygons, exactly one row is retained: sort
by `_ExposureRowID`, descending PML, then ascending `PolygonID`, and keep the
first. This is a selection rule, not an additive overlapping-loss calculation.
The retained PML is copied to `SourcePML`; `PMLOverrideApplied` is `False`.

## Event processing and status semantics

The pipeline checks both database connections, reads and selects events, reads
EDM exposures, drops unusable coordinates, then processes each selected event
independently. For each event it loads shape points and PML, left-merges PML on
`(EventID, PolygonID)`, intersects valid exposure points, and computes losses.
An event with no shape points/polygons receives `No polygons`; an event with no
intersections receives `No impacted exposures`; a completed event receives
`Success` and its impacted-row count. Any exception is retained in
`*_error_log.csv` and the event receives `Error` while other events continue.

The summary metrics are `overall_status`, `events_selected`, `events_successful`,
`events_no_polygons`, `events_no_impacted_exposures`, `events_failed`, and
`impacted_exposure_rows`. `overall_status` is `Complete with errors` if any
run-log row is `Error`, otherwise `Complete`. This status does not establish
that a zero result is approved or that monetary totals are complete.

Exit code `1` indicates a pipeline-level failure. Exit code `2` indicates one
or more selected events failed. A run with event failures is incomplete even
when some CSV files were written. Files are written one at a time after all
events; output-directory creation allows existing directories and publication
is not atomic.

## Output pack

The output prefix is `all_events` for all-event runs or `event_<EventID>` for a
single-event run. The generated files are:

| File | Contents |
|---|---|
| `*_summary.csv` | Overall status and event/row counts |
| `*_run_log.csv` | Event ID, name, status, and row count |
| `*_error_log.csv` | Event ID, name, exception text |
| `*_location_rows.csv` | Impacted post-join exposure rows and loss measures |
| `*_account_breakdown.csv` | Event/peril/account grouped counts, TIV, and losses |
| `*_location_breakout.csv` | Event/peril/location grouped counts, TIV, and losses |
| `edm_exposures.csv` | Post-policy/portfolio-join EDM extract |

Account and location breakdowns group post-join rows and sum ground-up TIV,
policy-adjusted TIV, ground-up loss, and policy-adjusted loss. Empty frames are
still written as header-bearing CSVs where their columns are known; a header or
file alone is not evidence of a complete result.

## Required controls and evidence

Before use, independently preserve controls at these grains:

1. location coverage before policy join (rows, accounts, locations, currencies,
   TIV and peril);
2. after policy join (account, policy count, selected factor, and row count);
3. after portfolio join (account, portfolio count, and row count);
4. valid, dropped, and out-of-range coordinates plus TIV;
5. polygon/PML key match, point counts, CRS, validity, repairs, and overlaps;
6. event, account, location, currency, ground-up TIV, policy-adjusted TIV,
   ground-up loss, and policy-adjusted loss totals.

Reconcile `Events`, `ShapeFiles`, and `PML` IDs and counts. Investigate every
unmatched policy/account, duplicate portfolio membership, invalid coordinate,
repaired geometry, boundary impact, missing PML, warning, and zero/no-impact
status. Require independently approved zero-impact evidence for an empty EDM
extract, no usable coordinates, no polygons, or no impacted locations.

Require a run manifest containing resolved non-secret arguments, database
identity and time, code and lock revision, start/end times, status and exit
code, output checksums, event selection, and pre/post-join counts and totals.
Publish only a complete run-specific directory. Never put credentials, tokens,
or connection secrets in the manifest or repository.

## Hard stops and unresolved decisions

Stop and escalate for missing, non-numeric, duplicate, out-of-range, or
unmatched polygon/PML data; overlapping polygons without an owner-approved
rule; empty or malformed extracts; dropped coordinates; multiple policy or
portfolio memberships without cardinality/allocation rules; missing policy
factors; or unapproved Fine Art patterns/factors.

Also stop for any use of `--allow-missing-pml`, reused/nonempty output folders,
partial event status, nonzero exit code, missing expected CSVs/headers, or a
status that claims completion without the controls above. GLOBAL-01 requires
owners to resolve policy-limit semantics, portfolio membership, Fine Art
matching, PML and geometry handling, independent zero-impact evidence, complete
publication, and provenance. COMMON-01 requires approved source period,
connection policy, scope, assumptions, and reconciliation tolerance.

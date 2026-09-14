# Global Exposures — technical contract

This contract describes the CSV route implemented by
`globalexposures/exposures.py`. SQL extraction is a separate preparation step;
the Python process reads local CSV files and does not connect to either
database, require a database driver, or accept CLI options.

## Inputs and configuration

Run these standalone SQL files and export the results with the stated names:

| SQL file | Database | CSV and required columns |
|---|---|---|
| `events.sql` | `GlobalExposures` | `events.csv`: `EventID`, `EventName`, `EventDescription` |
| `shape-points.sql` | `GlobalExposures` | `shape-points.csv`: `ShapefileID`, `EventID`, `PolygonID`, `Lat`, `Long`, `DrawOrder` |
| `pml.sql` | `GlobalExposures` | `pml.csv`: `EventID`, `PolygonID`, `PML` |
| `edm-exposures.sql` | selected EDM snapshot | `edm-exposures.csv`: `CEDANTID`, `PORTACCTID`, `PERIL`, `LOCID`, `LOCNUM`, `LATITUDE`, `LONGITUDE`, `GroundUpTIV`, `PolicyAdjustedTIV`, `CountryCode`, `CurrencyCode`, `PORTNAME`, `PORTNUM`, `POLICY_LINE_FACTOR`, `FA_QS_SRP_FACTOR`, `Coverage` |

The first three SQL files have optional `@event_id int = NULL`; `NULL` exports
all events. The same event selection must be used for all three. The EDM file
has `@peril_to_use int = 4` and
`@portnum_filter nvarchar(255) = NULL`; these preserve the original peril and
portfolio-filter semantics. The EDM projection uses the exact 16-column
order above; Python derives the `TIV` alias from `PolicyAdjustedTIV`.

The editable constants at the top of `exposures.py` are:

```python
EVENTS_INPUT_CSV = Path(__file__).with_name("events.csv")
SHAPE_POINTS_INPUT_CSV = Path(__file__).with_name("shape-points.csv")
PML_INPUT_CSV = Path(__file__).with_name("pml.csv")
EDM_INPUT_CSV = Path(__file__).with_name("edm-exposures.csv")
OUTPUT_DIR = Path(__file__).with_name("global_exposures_outputs")
EVENT_ID_TO_RUN = None
```

Each input may instead be any configured full path. `EVENT_ID_TO_RUN=None`
selects all events; an integer selects one event. Run from `globalexposures/`
with the dependency cache rather than a local virtual environment:

```bash
uv run --no-project --with-requirements requirements.txt python exposures.py
```

Inputs must be header-bearing CSVs with the columns above. Header-only shape or
PML files can be valid exports when the selected scope has no rows; missing
shape data and every no-impact result require independent review. Use one
matching snapshot, event scope, and peril scope across all inputs.

## EDM query and calculation

`edm-exposures.sql` first groups `dbo.loccvg.VALUEAMT` by location, account
group, location number, coordinates, country, peril, and currency after
filtering the selected peril:

```text
GroundUpTIV = SUM(loccvg.VALUEAMT)
```

Policy terms group `dbo.policy` by `ACCGRPID` and `POLICYTYPE`, retaining:

```text
PolicyFactor = MAX(CASE BLANLIMAMT WHEN 0 THEN 1 ELSE BLANLIMAMT END)
```

`BLANLIMAMT` is named as a monetary limit, but this implementation uses it as a
multiplicative factor. A missing policy match defaults to `1.0`. The
account/portfolio query joins `accgrp` to `portacct` and `portinfo`; an exact
optional `PORTNUM` filter is applied there. Fine Art QS/SRP logic is:

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
TIV              = PolicyAdjustedTIV
GroundUpLoss     = GroundUpTIV * PML
GULoss           = PolicyAdjustedTIV * PML
```

The policy result is account-level and is joined back to locations. Multiple
`portacct` memberships can therefore multiply location rows. The exported
`edm-exposures.csv` is post-join and cannot prove that duplication did not
occur.

## Spatial contract

`shape-points.csv` rows require `EventID`, `PolygonID`, `Lat`, `Long`, and
`DrawOrder`. Points are interpreted as latitude/longitude in WGS84
(`EPSG:4326`) and ordered by `DrawOrder` to construct polygons. Invalid
geometries are repaired with `buffer(0)` when possible; polygons with too few
usable points may be dropped.

Exposure rows with null coordinates are dropped. Remaining coordinates outside
latitude `[-90, 90]` or longitude `[-180, 180]` are dropped, then assigned an
internal `_ExposureRowID`. The spatial join uses GeoPandas
`predicate='intersects'`, so a point on a polygon boundary counts as impacted.

If one exposure intersects several polygons, exactly one row is retained:
sort by `_ExposureRowID`, descending PML, then ascending `PolygonID`, and keep
the first. This is a selection rule, not additive overlapping-loss
calculation. The retained PML is copied to `SourcePML`;
`PMLOverrideApplied` is `False`.

## Event processing and status semantics

The pipeline reads and selects events, reads the EDM CSV, drops unusable
coordinates, then processes each selected event independently. For each event
it loads shape points and PML, left-merges PML on `(EventID, PolygonID)`,
intersects valid exposure points, and computes losses. An event with no shape
points/polygons receives `No polygons`; an event with no intersections receives
`No impacted exposures`; a completed event receives `Success` and its
impacted-row count. Missing PML fails the event by default. Any exception is
retained in `*_error_log.csv` and the event receives `Error` while other
events continue.

The summary metrics are `overall_status`, `events_selected`,
`events_successful`, `events_no_polygons`, `events_no_impacted_exposures`,
`events_failed`, and `impacted_exposure_rows`. `overall_status` is `Complete
with errors` if any run-log row is `Error`, otherwise `Complete`. This status
does not establish that a zero result is approved or that monetary totals are
complete.

Exit code `1` indicates a pipeline-level failure. Exit code `2` indicates one
or more selected events failed. A run with event failures is incomplete even
when some CSV files were written. Files are written one at a time after all
events; the output directory must be new or empty, and publication is not atomic.

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
still written as header-bearing CSVs where columns are known; a header or file
alone is not evidence of a complete result.

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

Reconcile event, shape, and PML IDs and counts. Investigate every unmatched
policy/account, duplicate portfolio membership, invalid coordinate, repaired
geometry, boundary impact, missing PML, warning, and zero/no-impact status.
Require independently approved zero-impact evidence for an empty EDM extract,
no usable coordinates, no polygons, or no impacted locations.

Require a run manifest containing resolved non-secret settings, source snapshot
identity and time, code and dependency revision, start/end times, status and
exit code, output checksums, event selection, and pre/post-join counts and
totals. Never put credentials, tokens, or connection secrets in the manifest or
repository. Publish only a complete run-specific directory.

## Hard stops and unresolved decisions

Stop and escalate for missing, non-numeric, duplicate, out-of-range, or
unmatched polygon/PML data; overlapping polygons without an owner-approved
rule; empty or malformed extracts; dropped coordinates; multiple policy or
portfolio memberships without cardinality/allocation rules; missing policy
factors; or unapproved Fine Art patterns/factors.

Also stop for reused/nonempty output folders, partial event status, nonzero exit
code, missing expected CSVs/headers, or a status that claims completion without
the controls above. GLOBAL-01 still requires owners to resolve policy-limit
semantics, portfolio membership, Fine Art matching, PML and geometry handling,
independent zero-impact evidence, complete publication, and provenance.
COMMON-01 still requires an approved source period, scope, assumptions,
connection policy for the SQL export step, and reconciliation tolerance.

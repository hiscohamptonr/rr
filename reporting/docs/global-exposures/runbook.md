# Global Exposures — CSV operator run

This is an offline CSV calculation. `exposures.py` does not connect to a
database, execute SQL, or read a workbook. The SQL files produce four CSV
inputs; the Python step reads those files and writes a local output pack.
Repository SQL comments contain original/default server and database names,
not evidence that those sources or snapshots are approved for a reporting run.

## 1. Export one controlled input scope

Run the four files in `globalexposures/sql/` against the approved sources and
retain the exact query revision, server/database, snapshot, parameters, and
CSV export evidence:

- `events.sql`, `shape-points.sql`, and `pml.sql` use the `GlobalExposures`
  source (`data.Events`, `data.ShapeFiles`, and `data.PML`). Use the same
  approved `@event_id` in all three files (`NULL` means all events).
- `edm-exposures.sql` uses the selected EDM snapshot and has no event
  predicate. Set `@peril_to_use` and, where required, `@portnum_filter` for
  the exposure population. Its checked-in defaults are peril `4` and no
  portfolio filter; these are not standing business selections.

Export with headers as `events.csv`, `shape-points.csv`, `pml.csv`, and
`edm-exposures.csv`. The Python loader requires the exact header and column
order emitted by the checked-in SQL:

- events: `EventID, EventName, EventDescription`;
- shape points: `ShapefileID, EventID, PolygonID, Lat, Long, DrawOrder`;
- PML: `EventID, PolygonID, PML`;
- EDM: `CEDANTID, PORTACCTID, PERIL, LOCID, LOCNUM, LATITUDE, LONGITUDE,
  GroundUpTIV, PolicyAdjustedTIV, CountryCode, CurrencyCode, PORTNAME,
  PORTNUM, POLICY_LINE_FACTOR, FA_QS_SRP_FACTOR, Coverage`.

Do not treat the checked-in EDM SQL as an approved methodology: it currently
uses a policy-line value as a multiplicative factor, defaults an unmatched
policy to `1.0`, and joins every qualifying portfolio membership to a
location. Resolve the policy-term formula, policy grain, membership
cardinality/allocation, and unmatched-account treatment before production.

## 2. Place the inputs

Put the four header-bearing CSVs beside `exposures.py`, or edit each input
constant to an approved full path. A header-only shape or PML export can be
valid as an input file, but it produces no valid polygons or no PML rows;
review every `No polygons` and `No impacted exposures` result independently.
An empty selected event set is a hard failure.

## 3. Set the run constants

Use a new or empty output folder and keep the paths and event selection
explicit:

```python
EVENTS_INPUT_CSV = Path(__file__).with_name("events.csv")
SHAPE_POINTS_INPUT_CSV = Path(__file__).with_name("shape-points.csv")
PML_INPUT_CSV = Path(__file__).with_name("pml.csv")
EDM_INPUT_CSV = Path(__file__).with_name("edm-exposures.csv")
OUTPUT_DIR = Path(__file__).with_name("global_exposures_outputs")
EVENT_ID_TO_RUN = None  # or one approved EventID
```

`fail_on_missing_pml` is `True` in `RunConfig`; do not disable it to bypass
unknown loss. A valid polygon with a null/missing PML fails that event, while
an event with no valid polygon is logged as `No polygons` and requires
separate evidence.

## 4. Run the offline calculation

From the `reporting/` directory, run:

```bash
cd globalexposures
uv run --isolated --locked python exposures.py
```

`globalexposures/pyproject.toml` requires Python `>=3.13` and declares
`geopandas`, `pandas`, and `shapely`; `uv.lock` is the locked dependency
input. Do not rely on an unrelated interpreter or an unrecorded local
environment.

## 5. Review the output pack and grain

For `EVENT_ID_TO_RUN = None`, the prefix is `all_events`; for one event it is
`event_<EventID>`. The pack contains:

- `<prefix>_summary.csv`: the fixed metrics `overall_status`,
  `events_selected`, `events_successful`, `events_no_polygons`,
  `events_no_impacted_exposures`, `events_failed`, and
  `impacted_exposure_rows`;
- `<prefix>_run_log.csv` and `<prefix>_error_log.csv`: per-event status and
  caught exception text;
- `<prefix>_location_rows.csv`: one retained input exposure row per selected
  event/spatial match after overlap tie-breaking, with the EDM fields plus
  `EventName`, `SelectedPeril`, `PML`, `SourcePML`, `PMLOverrideApplied`,
  `GroundUpLoss`, and `GULoss`. `_ExposureRowID` identifies the filtered
  input row; repeated `LOCID` values are not automatically one location;
- `<prefix>_account_breakdown.csv`: grouped by event/peril and available
  cedant, account, portfolio, and currency fields;
- `<prefix>_location_breakout.csv`: grouped by event/peril/location
  coordinates, currency, polygon, and PML, with account/portfolio counts and
  TIV/loss sums; and
- `edm_exposures.csv`: the loaded EDM extract with the added `TIV` column
  (equal to `PolicyAdjustedTIV`).

If a result frame is empty, the writer can produce a headerless CSV because
the implementation has no fixed empty-frame schema. Do not use a headerless
empty breakdown as evidence that its columns or totals are complete.

Inspect all files, account for every selected event, and reconcile source
rows, distinct accounts/locations, TIV, and loss totals at the event,
peril, portfolio, currency, and location grains. A `Complete` summary is
processing status only; it does not approve a zero result or prove monetary
completeness. The process returns `0` with no event errors, `2` when one or
more events were caught as errors, and `1` for a pre-run failure.

## 6. Spatial and PML controls

Boundary points count as impacted. If an exposure row intersects multiple
polygons, the retained match is the highest PML, then lowest `PolygonID`;
the calculation is not additive across overlaps. PML values are not range
validated, and duplicate `(EventID, PolygonID)` PML rows are not rejected;
resolve the PML key, one-row rule, valid range, and missing-data treatment.
`PMLOverrideApplied` is currently always `False`; no override is implemented.

Rows with missing or out-of-range coordinates are silently excluded.
Shape rows with missing required fields or fewer than three usable points are
dropped, and invalid polygons are repaired with `buffer(0)`. The output pack
does not persist rejection counts, dropped TIV, or geometry-change evidence.
Reconcile those populations independently before delivery. Also investigate
invalid numeric TIV/PML values, policy-join multiplication, and every zero
or error result. Keep inputs, constants, command, outputs, manifest, and
reconciliations together; the unresolved methodology and publication
decisions are tracked under `GLOBAL-01`.

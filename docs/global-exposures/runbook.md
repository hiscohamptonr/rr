# Global Exposures — event exposure files

**Not ready for an operator run:** the SQL Server spatial implementation is still required; `globalexposures/exposures.py` remains a maintainer-only calculation, not an approved reporting route.

## Prepare the run

1. Confirm the annual EDM snapshot and the event, polygon and PML records in `GlobalExposures.data.Events`, `ShapeFiles` and `PML`.
2. Confirm event IDs, polygon validity, coordinates, policy/portfolio rules and independent exposure totals before any calculation.
3. Use a new, empty output folder for each run so files from different events or snapshots are not mixed.
4. Do not run or deliver this as an operator process until the spatial implementation, validation evidence and source rules have been approved.

## Check a supplied calculation pack

1. Read `*_summary.csv` for status and event counts, not monetary totals.
2. Check `*_run_log.csv` and `*_error_log.csv` and account for every selected event.
3. Reconcile `edm_exposures.csv` to independent EDM totals.
4. Reconcile `*_account_breakdown.csv` and `*_location_breakout.csv` to the impacted-location detail in `*_location_rows.csv`.
5. Investigate missing files or headers, multiplied exposure, invalid geometry/PML, missing policy factors and every zero/no-impact result.
6. Accept a zero only with independent evidence of no impact, and do not sum overlapping events without an agreed rule.
7. Keep the full CSV pack, source settings, calculation command and reconciliations together.

There is no Excel-loading step for this process; a CSV pack alone does not establish that every event was calculated correctly.

**To return to later:** finish and validate the SQL Server spatial route before using this process for reporting.

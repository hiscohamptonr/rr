---
Report: BSCR
Time: 1d
---


# BSCR — SQL-only outputs

## Output scripts

1. Run `bscr/sql/bscr-extract.sql` against the approved EDM database, checking
   `@policy_type` for the run. Its header table selects peril 1 (earthquake)
   and peril 2 (wind) together.
2. Export that source-level result as the raw CSV with headers:
   `pml, accgrpid, uwritrname, state, userid1, cntrycode, is_geocoded, peril_id`.
3. Run `bscr/sql/bscr-output.sql` against the same database snapshot and
   parameters. Leave `@bscr_entity = NULL` for all entities, or set it to
   `33`, `HIC`, `HIG`, `HSA` or `3624` for one entity.
   Set `@gbp_to_usd` to the approved USD-per-GBP rate (default `1.35`).
   The final SELECT converts `sum_pml` and `sum_net` to full USD; counts
   and grouping remain unchanged.
4. Export the aggregate result with headers:
   `cntrycode, bscr_entity, region, sum_pml, sum_net, count_policies, is_geocoded`.
5. The SQL routes `is_nahu`, `is_eu` and `is_jp` to peril 2, and
   `is_na_eq`, `is_jp_eq`, `is_us_all`, `is_non_us` and `ALL` to peril 1.
6. Reconcile the aggregate `ALL` rows to the earthquake raw/source totals
   after applying the same FX rate, then check entity, geography, geocode,
   retention and regional splits. The extract still contains the legacy
   policy/geocoding defects, so FX alone does not resolve those differences.
7. Save both SQL files, parameters, raw output, aggregate output and database
   snapshot together.

Both active calculation steps are SQL-only. `BSCR_UKEU.py` is retained only
as historical comparison material and is not part of the production process.

## Entity workbooks through Power Query

Use one controlled `BSCR_Workings.xlsx` workbook as the calculation and
schedule bridge. Select the entity in one settings cell rather than maintaining
separate calculation logic for `33`, `HIC`, `HIG`, `HSA` and `3624`.

1. Set the existing `Entity` setting in `Settings!B7`; its validation list
   contains `33`, `HIC`, `HIG`, `HSA` and `3624`.
2. Set that cell to the entity being prepared.
3. Pass the same value to `@bscr_entity` in `bscr-output.sql`.
4. Load the result into the controlled BSCR input table and refresh formulas
   and pivots.
5. Review the linked Schedule X(a), X(b), X(c) and X(f) areas; save a separate
   copy only when a submission package is required.

The workbook now uses `Settings!$B$7` for the schedule entity criteria and
recalculates formulas on open. The Power Query source connection still needs
to be configured in Excel to load the SQL result into the controlled input
table. The files in `bscr/old-process/Workings/` are presentation targets, not
SQL sources. Replace unresolved external-link inputs before production
refreshes.

Schedule X(a) and X(b) still require approved EP-curve/premium sources.
Schedule X(f) requires an approved distinct-contract identifier and count
rule; `count_policies` is only a contributing-row count.

## Run controls

- The extract retains source currency. The aggregate assumes all source
  amounts are GBP and applies `@gbp_to_usd` only in the final SELECT.
  Confirm the source-currency population independently; a single rate
  cannot normalize mixed-currency data. SQL output is full USD, not millions.
- Before loading the USD aggregate, remove or bypass workbook FX on every
  gross/net path to avoid converting twice. Retain division by 1,000,000
  only where USD millions are required. The workbook is unchanged and
  includes hard-coded `1.35` factors as well as `Settings!B3`; changing
  that setting alone is insufficient. Reconcile all affected formulas.
- Do not add overlapping regional rows together.
- Set `@qs_pct_retention` and `@srp_pct_retention` at the top of
  `bscr-output.sql`; they are fractions (`0.5` and `0.3333` by default).
- Confirm QS-first retention and the approved geography mappings.
- Investigate failed or partial exports, unexplained totals and policy-join
  multiplication before using the outputs.
- Preserve raw and aggregate exports separately for reconciliation.

**To return to later:** map the approved Schedule X(a), X(b) and X(f) fields
to SQL output metrics and identify the controlled sources for EP curves,
premiums and distinct contract counts.

`bscr/BSCR_UKEU_original.py` preserves the original Marimo application,
also archived at `bscr/old-process/BSCR_UKEU.py`. It connects directly to
SQL Server and runs its embedded earthquake-only query before the Python
aggregation. Its original policy/geocoding calculation defects are preserved,
so its totals are not a correctness baseline for the corrected SQL output.

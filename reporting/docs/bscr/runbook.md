# BSCR reporting and reconciliation

[Back to reporting index](../index.md)

## Two SQL scripts

| Script | Purpose |
|---|---|
| `bscr/sql/bscr-extract-legacy.sql` | Full historical aggregate output, despite the extract name. Earthquake/policy type 1 throughout; preserves the old geocode duplication and cap grouping, plus Python-style case-sensitive geographic matching. Diagnostic only. |
| `bscr/sql/bscr-output.sql` | Current aggregate with corrected geocode joins, policy-ID grouping and earthquake/wind routing. |

Both return:

`cntrycode, bscr_entity, region, sum_pml, sum_net, count_policies, is_geocoded, peril_id`

Both default to full USD using source GBP multiplied by `@gbp_to_usd = 1.35`.
Neither divides by 1,000,000. The legacy script can be run with FX 1 when
comparing directly to the historical source-currency CSV. Keep FX, retention
and entity parameters identical when comparing the two scripts.

The scripts are not otherwise equivalent: the legacy query reconstructs the
whole old workflow, including earthquake-only regions and case-sensitive
geographic classification. The current query intentionally retains its current
peril routing and additional regional output views. Do not attribute every
regional difference to the geocode correction.

## Concise reconciliation workbook

Use `bscr/reconcile/results/BSCR_Reconciliation.xlsx`.

- **Read first:** which saved outputs were reproduced and what was established.
- **Counts:** old saved output versus legacy query; new saved output versus
  corrected query; entity totals and the difference.
- **Gross exposure / Net exposure:** the same comparison in USD millions.
- **Why it changed:** the measured effect of changing only the geocode join,
  and the separate state-matching/peril-routing changes.
- **Queries and source:** the two scripts, source database, raw row counts and hashes.

Verified on the supplied source snapshot:

1. Original embedded SQL plus original Python aggregation reproduces all 452
   rows of `bscr/output/bscr-output.csv`, with exact counts and monetary differences
   below one cent in source currency.
2. The retained legacy SQL reproduces those 452 rows after the documented FX
   conversion and matches all 49 groups in the later March USD workings.
3. Current SQL reproduces all 737 rows of
   `bscr/reconcile/bscr_output_wseq.csv`, with exact counts and monetary
   differences below one cent.
4. Changing only the geocode join explains the whole `ALL` reduction:
   USD 4.813bn gross, USD 3.051bn net and 285 grouped output rows. All 184
   affected accounts have both geocoded and ungeocoded earthquake locations.
5. Policy-ID cap grouping has no material effect on this snapshot: no account
   has multiple type-1 policies. This does not establish that policy identity
   is unnecessary on other populations.

These are local DuckDB replays checked against the saved outputs, not live
SQL Server executions. SQL Server's case-insensitive comparisons were reproduced
locally; the legacy query's geographic comparisons deliberately remain
case-sensitive to reproduce Python. `count_policies` counts grouped source rows,
not verified distinct contracts. This is numerical reconciliation, not approval
of all policy terms, modelability classifications or regulatory filing figures.

## Preserve the source evidence

The six uploaded CSVs remain under `bscr/sql/edm-parquet/`; the folder name is
historical and the files are CSV, not Parquet:

| File | Verified rows |
|---|---:|
| `01_accgrp.csv` | 354,830 |
| `02_policy.csv` | 662,306 |
| `03_loc.csv` | 1,008,151 |
| `04_loccvg.csv` | 1,053,391 |
| `source_metadata.csv` | 1 metadata record |
| `06_schema.csv` | Source column definitions |

Do not deduplicate, apply FX, edit or resave the raw files in Excel.
Preserve empty strings separately from SQL NULL representations. The supplied
state field has 30 literal `NULL` markers in French/German locations; raw lexical
values were preserved for inspection. Source metadata identifies
`HISCO_UKEU_01JAN26_010126_ROLLUP_ByLOB_GC_EDM` and its case-insensitive collation.
All four source counts match the metadata.

Historical input workbooks and saved output CSVs are retained unchanged.
`workings_old_report.xlsx` is identical to `Workings_with_geocodingFW.xlsx`.
The earlier workings divide by 1,000; FW divides by 1,000,000. The later
`Workings_with_geocodingFW - Including blanks USD.xlsx` applies 1.35 FX and
restores US exposure to NA hurricane. Its 49 raw groups match the historical
CSV without excluding US. Do not reproduce the earlier workbook's omission
as a production rule.

The five April templates retain the historical total counts. All 46 populated
regional gross/net exposure limits match the later USD workings within USD 1.
Their modelability allocations, premiums, EP placeholders, cached errors and
external links remain separate controls; dates do not prove submission.

The original Marimo application remains at `bscr/BSCR_UKEU_original.py` and
`bscr/old-process/BSCR_UKEU.py`. The separate `bscr/BSCR_UKEU.py` is an older
seven-column CSV workflow, not a consumer of these eight-column query outputs.

## Running the retained queries

1. Select the approved EDM database/snapshot in your SQL client.
2. Run `bscr-extract-legacy.sql` for the historical comparison and
   `bscr-output.sql` for the corrected result. Both are read-only.
3. Use the same frozen source and the same FX, retention and entity settings.
4. Save results separately; retain all eight headers and preserve NULLs.
5. Compare `ALL` for earthquake totals and compare regional populations
   separately. Never sum across overlapping regional rows.

Current routing: wind (2) feeds `is_nahu`, `is_eu`, `is_jp`; earthquake (1)
feeds `ALL`, `is_na_eq`, `is_jp_eq`, `is_us_all`, `is_non_us`. The legacy
script uses earthquake for every retained regional label and does not add
`is_jp_eq` or `is_non_us`. Uppercase US states do not match the legacy Python
lookup's title-case names; current SQL includes the selected US states through
case-insensitive matching. Canada is included in both.

## Loading the current reporting workbook

`bscr/workbooks/BSCR_Workings.xlsx` is the operational workbook, not the concise
reconciliation report. Preserve its approved formulas and controls:

1. Back it up before loading. Load only the first seven aggregate columns into
   `BSCR Source Data!A:G`; retain `peril_id` in the CSV, not worksheet H.
2. Clear stale input rows and verify complete entity/region/geocode coverage.
   `BSCR Output!A2:F70` has a fixed list of keys; new keys are not added by recalculation.
3. Bypass workbook FX on every gross/net path before loading USD query output.
   Some formulas hard-code 1.35, so changing `Settings!B3` alone is insufficient.
   Retain division by 1,000,000 only where USD millions are required.
4. Reconcile cached/formula outputs after Excel refresh. Do not infer modelled,
   modellable, detailed or data-deficient classifications solely from geocoding.
5. Review the controlled final template, external links, premium source,
   modelability decisions and EP results before transfer or sign-off.

See the [discrepancy register](../calculation-discrepancies.md#bscr-schedule-x)
for remaining controls, especially policy-cap allocation grain and distinct
contract counting.

---
Report: BSCR
Time: 1d
---


# BSCR — SQL-only outputs

Paths below are relative to `reporting/`. The current route is **SQL extraction
and aggregation → CSV → Excel**. The repository supplies the queries, not an
approved database snapshot, connection, or reporting-cycle methodology.
Resolve the [BSCR decisions](../decisions.md#bscr-01) before production use.

For a single-peril comparison, use `bscr/sql/bscr-output-peril1.sql`.
It runs the full aggregate calculation with `peril = 1` and `policytype = 1`
for every region, including `is_nahu`, `is_eu` and `is_jp`. Those labels
therefore contain earthquake exposure in this variant, not wind. FX,
retention, entity filtering and the eight-column aggregate output are retained;
`peril_id` is always `1`. This replaces the mistakenly supplied
`bscr-extract-peril1.sql` raw extract. The main dual-peril queries are unchanged.

## Historical workbook reconciliation

The supplied files in `bscr/reconcile/` are candidate historical evidence,
not confirmed submissions. The detailed comparison is
`bscr/reconcile/results/bscr_workbook_collection_reconciliation.xlsx`;
its companion CSVs record every template version change, cached error,
regional limit comparison, file hash, and control total.

- `workings_old_report.xlsx` is byte-identical to
  `Workings_with_geocodingFW.xlsx`.
- `Workings_with_geocoding.xlsx` and the FW version have the same 47 raw
  output rows. The first divides by 1,000; FW divides by 1,000,000.
- `Workings_with_geocodingFW - Including blanks USD.xlsx` restores US
  exposure to NA hurricane, has 49 output groups, and explicitly applies
  1.35 FX followed by division by 1,000,000. Its static output sheet is not
  linked to `Sheet1`; a GB/HIC amount differs between those populations.
- The February corrected template family is the 33 original plus the four
  other entities' v2 files. Their total counts and source amounts divided
  by 1,000 match the workings, despite template US$M labels.
- The five top-level April templates retain the historical total counts.
  All 46 populated regional gross/net limit cells match the later USD
  workings within USD 1; four 3624 Japan cells are blank with no source rows.
  Overall limits are rounded, and modelability categories are reallocated.
  Do not equate those categories directly with `is_geocoded`.
- The templates still contain external links, cached errors and nonnumeric
  EP-curve placeholders. Premiums, modelability judgments and actual
  submission status need independent evidence.

## Export raw EDM data for local diagnosis

The aggregate exports cannot explain changes at policy/location level.
Use `bscr/sql/bscr-edm-raw-export.sql` on the same approved EDM snapshot as
the comparison outputs. It reads source tables only; it does not modify
data or enable database settings. It requires existing SNAPSHOT isolation
or an immutable read-only database/database snapshot. Otherwise it stops.
Use a standalone connection and discard partial results if the batch fails.

Save its six resultsets as UTF-8 CSVs with headers, in a controlled directory
outside Git, for example `$HOME/bscr-edm/snapshot`:

| File | Content and scope |
|---|---|
| `manifest.csv` | Run ID, server/database, UTC start, isolation, four source counts and scopes |
| `schema.csv` | Actual source column types, precision, scale and nullability |
| `accgrp.csv` | All account IDs, entity/treaty marker, branch and underwriter |
| `policy.csv` | Every type-1/type-2 policy ID, account ID and relevant limit/deductible terms |
| `loc.csv` | All location/account IDs, location number, geocode flag, state/country and coordinates |
| `loccvg.csv` | Every peril-1/peril-2 coverage row, values, deductibles, limits and currencies |

Preserve duplicate coverage rows and orphan/unmapped records. Do not use
`DISTINCT`, pre-join the tables, restrict entities, aggregate or apply FX.
The exporter uses literal `\N` for SQL NULL; empty strings are distinct.
Use a CSV writer that quotes commas, quotes and embedded newlines correctly;
do not open and resave the raw files in Excel. Numeric style-3 conversion
requires SQL Server 2016 or later. All four data files carry one run ID.

From the `reporting/` directory, import the six files:

```sh
uv run --no-project --with duckdb --with sqlglot python bscr/tools/edm_local.py import \
  --input "$HOME/bscr-edm/snapshot" \
  --database "$HOME/bscr-edm/snapshot/source.duckdb"
```

The importer checks headers, run IDs, counts and numeric conversions before
publishing a new database. It preserves lexical source values in `raw_*`
tables, creates typed `accgrp`, `policy`, `loc`, `loccvg` views, and stores
the manifest, schema and CSV SHA-256 hashes. Unexported schema columns are
not fabricated as NULL. Existing databases are not overwritten.

Inspect policy counts without joining to locations:

```sh
uv run --no-project --with duckdb --with sqlglot python bscr/tools/edm_local.py query \
  --database "$HOME/bscr-edm/snapshot/source.duckdb" \
  --sql "SELECT policytype, COUNT(*) AS rows, COUNT(DISTINCT policyid) AS distinct_policy_ids FROM policy GROUP BY policytype"
```

Replay an aggregate query locally:

```sh
uv run --no-project --with duckdb --with sqlglot python bscr/tools/edm_local.py replay \
  --database "$HOME/bscr-edm/snapshot/source.duckdb" \
  --query bscr/sql/bscr-output.sql \
  --output "$HOME/bscr-edm/snapshot/current-output.csv"
```

Repeat with `bscr/sql/bscr-output_old_logic.sql` and a different output name
to isolate the policy-side geocode join; that variant is **not** a complete
historical reproduction. `bscr-output-peril1.sql` uses earthquake for all
regions; `bscr-output-all-perils.sql` provides both perils in every region,
including `ALL`. Keep identical source files and parameter values between
runs. Optional `--fx` and `--entity` overrides are recorded alongside the
declared defaults in each output's `.provenance.json`, with source hashes
and engine versions.

Local replay adapts T-SQL to DuckDB; collation and numeric aggregation can
differ from SQL Server. First compare the local current-query output with
the server output from the **same snapshot**. Then change one calculation
dimension at a time: geocode join, policy cap grouping, peril selection,
regional scope. Trace residuals by account/policy/location before approving
a change. `count_policies` remains a grouped-source-row count; distinct
policy IDs are a separate diagnostic, not automatically a contract count.

## Run the two SQL exports

1. In an approved SQL Server client, select the approved EDM database and run
   `bscr/sql/bscr-extract.sql`. Its `peril_selection` selects peril 1
   (earthquake) and 2 (wind) together. Both use the single
   `@policy_type = 1` filter: confirm that policy population is appropriate
   for both perils; the query does not select a separate policy type per peril.
2. Export the raw/source result with these eight headers, in order:
   `pml, accgrpid, uwritrname, state, userid1, cntrycode, is_geocoded, peril_id`.
   These are already capped account/geography aggregates, not location or
   individual-policy detail.
3. Run `bscr/sql/bscr-output.sql` against the **same snapshot** and peril
   selection. It matches policy type to each peril rather than using the
   extract's single `@policy_type`. It independently calculates the source
   exposure; it does not read the raw CSV. Leave `@bscr_entity = NULL` for
   all entities, including unmapped
   NULL entities, or set a quoted value such as `'HIC'`, `'33'`, `'HIG'`,
   `'HSA'`, or `'3624'`.
4. Confirm `@qs_pct_retention` and `@srp_pct_retention` (`0.5` and `0.3333`).
   They are retained fractions, not percentages to divide by 100. A literal
   `_QS` marker in `userid1` takes precedence over `_SRP`; other rows retain
   the full amount.
   Set `@gbp_to_usd` to the approved USD-per-GBP rate (default `1.35`).
   The final SELECT converts gross/net amounts to full USD; counts and
   grouping are unchanged. No division by 1,000,000 is applied in SQL.
5. Export the aggregate result with these eight headers:
   `cntrycode, bscr_entity, region, sum_pml, sum_net, count_policies, is_geocoded, peril_id`.
   `peril_id` is explicit: `1` for earthquake (including `ALL`), `2` for wind.
6. Preserve both SQL files, parameter values, exports, row counts, totals and
   source-snapshot identity together. A successful export does not resolve the
   policy-grain or workbook defects below.

## Understand and reconcile the output

The aggregate grain is country, derived entity, region and geocode status.
There is no final `peril_id` column: the following region routing is part of
the output contract.

| Region | Peril | Current population |
|---|---|---|
| `is_nahu` | 2 — wind | US (all states), CB, TC, BH, JM, VI, MX |
| `is_eu` | 2 — wind | GB, UK, FR, DE, BE, NL, LX, AT, DK, SE, PL, CZ |
| `is_jp` | 2 — wind | JP |
| `is_na_eq` | 1 — earthquake | CA; US California, Washington, Oregon, South Carolina, Tennessee, or NULL state |
| `is_jp_eq` | 1 — earthquake | JP |
| `is_us_all` | 1 — earthquake | US |
| `is_non_us` | 1 — earthquake | Anything other than US, including NULL country |
| `ALL` | 1 — earthquake | All source countries |

These are observed mappings, not approved geography definitions. `LX` is
literal; SQL does not substitute `LU`. Empty US state is not the same as NULL.
Region rows overlap; **never total all regions together**. `ALL` is earthquake
only, not an all-peril or wind control. Wind outside its three regional
populations has no aggregate output row.

- Compare `ALL.sum_pml` to raw `pml * @gbp_to_usd` filtered to `peril_id = 1`,
  using the same entity scope and geocode/country grain. For an entity-filtered
  aggregate, first apply the same entity classification to the raw result.
- Entity classification searches `userid1` case-insensitively in this order:
  HIG, HSA, 33, 3624, HIC. It is substring matching, not an exact portfolio map;
  unmatched values produce NULL. Investigate those rows before filtering.
- Check each wind region separately against the corresponding peril-2 raw
  population after applying the same FX rate. Reconcile gross-to-net movement
  by QS/SRP category.
- `count_policies` is `COUNT_BIG(*)` over contributing source aggregates.
  It is neither distinct policies nor distinct contracts and is not an
  approved Schedule X(f) count.
- The extract retains source currency; the aggregate converts assumed GBP
  amounts to full USD only in its final SELECT. Confirm all source amounts
  are GBP independently: currency is absent from both final exports, and a
  single rate cannot normalize mixed-currency data. Neither query divides
  by 1,000,000.
- The extract still retains the account-only policy rejoin, policy-side
  geocode and cap grouping without `policyid`. The aggregate query corrects
  those joins, matches policies by peril, and applies caps separately per
  policy within each exposure grouping. Raw-to-aggregate differences can
  therefore remain after FX conversion. Obtain independent source and
  before/after-join controls rather than treating the legacy extract as a
  correctness baseline. See BSCR-002 in the
  [discrepancy register](../calculation-discrepancies.md#bscr-schedule-x).

## Load a controlled workbook copy

Use `bscr/workbooks/BSCR_Workings.xlsx` as workings, not as a completed return.
Its current input is a worksheet range, **not an Excel table**, and there is
no configured Power Query connection.

1. Resolve the affected workbook blockers below before a production refresh.
2. Set `Settings!B7` to the entity being prepared. Its validation list contains
   33, HIC, HIG, HSA and 3624. If filtering the SQL, use the same entity value.
3. Load only the **first seven columns of the aggregate**, not the raw export,
   into `BSCR Source Data!A:G` with headers in row 1. Preserve the eighth
   column (`peril_id`) in the CSV for audit; do not paste it into H, which
   contains workbook formulas. Clear stale controlled input
   rows. First adapt the currency formulas as described below; preserve
   unrelated worksheet content.
4. `BSCR Output!C:E` uses `SUMIFS` over source D:F, matching entity, region and
   geocode from output A, B and F, and summing across countries. Those grouping
   keys are a fixed list: ensure every incoming key has an approved output row.
   Recalculation does not create missing groups.
5. Before loading the USD aggregate, remove or bypass the workbook's GBP-to-USD
   multiplication on every gross/net path. Retain division by 1,000,000 only
   where USD millions are required. The checked-in workbook has not been
   updated for this SQL currency change: loading into its existing formulas
   would convert twice. Changing `Settings!B3` alone is insufficient because
   some formulas hard-code `1.35`. Reconcile formula coverage before refresh.
6. Reconcile source → output → pivots → schedule reference cells. Retain a
   reviewed copy and the final-template transfer record.

### Current workbook blockers

- **Japanese perils reversed:** `Schedule X(c)!B7:C7` (earthquake) selects
  `is_jp`, which SQL now defines as wind. `B8:C8` (typhoon) selects `is_jp_eq`,
  which SQL defines as earthquake. Resolve the formula/key mapping before use.
- **Pivot coverage:** the output pivot cache still uses `BSCR Output!A1:J50`,
  excluding rows 51–70 for `is_jp_eq` and `is_non_us`. The source pivot uses
  `BSCR Source Data!A1:K1048576`; neither is a dynamically sized Excel table.
- **FX is not fully settings-driven:** source H:I rows 3–453 and output G
  rows 3–50 use shared formulas containing hard-coded `1.35`. Changing B3
  alone does not update those conversions. Resolve and reconcile all affected
  gross/net paths before applying another rate.
- **Cached data is not a current SQL run:** source rows contain the older six
  region labels, without `is_jp_eq` or `is_non_us`. Workbook instructions and
  audit notes also retain older Python/Power Query wording. Forced
  recalculation on open does not load new data or repair these inconsistencies.

See BSCR-001 and BSCR-007 through BSCR-011 in the
[discrepancy register](../calculation-discrepancies.md#bscr-schedule-x).

## Completion boundary

Schedule X(a) and X(b) require independent approved EP-curve and premium
sources. X(c) contains combined regional exposure references, not all required
premium/limit splits. X(f) needs distinct-contract and modelability sources.
Approve the final template and field-by-field mapping before submission;
files in `bscr/old-process/Workings/` are historical presentation evidence,
not SQL inputs or proof of current template approval.

`bscr/BSCR_UKEU.py` is retained for historical comparison only. Its strict
seven-column source contract rejects the current eight-column extract, and
its aggregation does not implement the current dual-peril routing or the new
region keys. Do not remove `peril_id` and feed combined-peril rows into it.

`bscr/BSCR_UKEU_original.py` preserves the original Marimo application,
also archived at `bscr/old-process/BSCR_UKEU.py`. It connects directly to
SQL Server and runs its embedded earthquake-only query before the Python
aggregation. Its original policy/geocoding calculation defects are preserved,
so its totals are not a correctness baseline for the corrected SQL output.

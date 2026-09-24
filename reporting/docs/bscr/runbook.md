# BSCR — populate the schedules

The reconciliation workbook is [BSCR_Reconciliation.xlsx](../../bscr/reconcile/results/BSCR_Reconciliation.xlsx) in `bscr/reconcile/results/`; the auto-population workbook is [BSCR_Auto_Population.xlsx](../../bscr/workbooks/BSCR_Auto_Population.xlsx) in `bscr/workbooks/`.

[Back to reporting guides](../../README.md)

## Use these files

| Purpose | File |
|---|---|
| Produce current results in SQL Server | [bscr-output.sql](../../bscr/sql/bscr-output.sql) |
| Populate the schedules in Excel | [BSCR_Auto_Population.xlsx](../../bscr/workbooks/BSCR_Auto_Population.xlsx) |
| Review old-versus-new evidence separately | [BSCR_Reconciliation.xlsx](../../bscr/reconcile/results/BSCR_Reconciliation.xlsx) |

The population workbook needs Excel only: no Python, macros, database connection
or external workbook links. Its seven tabs are **Instructions**, **SQL input**,
**33**, **3624**, **HIC**, **HIG** and **HSA**. Each entity tab contains
Schedules X(a), X(b), X(c) and X(f), with navigation links and print breaks.

## Refresh the population workbook

1. Clear the old data on **SQL input**, keeping the header row and table.
2. Paste the new eight-column results from **bscr-output.sql** below the
   headers. The entity tabs populate automatically.

Use the full output for all entities. Excel calculation must be automatic;
if values do not refresh, use **Calculate Now**. Do not leave old data rows
below a shorter replacement.

The input columns, in order, are:

`cntrycode, bscr_entity, region, sum_pml, sum_net, count_policies, is_geocoded, peril_id`

There is no historical-check tab or legacy mode in this population workbook.
Do not paste the legacy query's output into it as a historical comparison;
use the separate reconciliation workbook for that evidence.

## What populates automatically

Green cells are automatic and locked. Blue cells remain manual and start blank:
premiums, EP/model losses, questionnaires and narratives. Blank does not mean zero.
The workbook is a population aid, not a complete or approved regulatory return.

| Population / measure | Agreed mapping |
|---|---|
| Modellable / modelled / detailed exposure | `is_geocoded = 1` |
| Not modellable / not modelled / data deficient | `is_geocoded = 0` |
| US contracts in X(f) | Earthquake `ALL` rows with `cntrycode = 'US'` |
| All other contracts in X(f) | Earthquake `ALL` minus US, using the same geocode selection |
| Count | Sum the supplied `count_policies`; do not scale or apply FX |
| Gross / net exposure | Sum the relevant SQL gross/net values and divide by 1,000,000 |

The geocoding classification is the agreed workbook proxy. It does not reproduce
April's separate manual reallocations. Other modelability categories are zero
under this proxy. Repeated schedule presentations are intentional; do not sum
all regions or schedules into a portfolio total.

The automatic X(a)/X(b) exposure fields are the **all-other-lines** limits,
split between modelled and not modelled. Statutory property-catastrophe fields
require separate manual inputs; the SQL does not identify that classification.

### Regional limits in X(c)

| Schedule region | SQL region | Peril |
|---|---|---|
| Atlantic hurricane | `is_nahu` | Wind, 2 |
| North American earthquake | `is_na_eq` | Earthquake, 1 |
| European windstorm | `is_eu` | Wind, 2 |
| Japanese earthquake | `is_jp_eq` | Earthquake, 1 |
| Japanese typhoon | `is_jp` | Wind, 2 |

`ALL` is earthquake only. Regional populations overlap. Canada is included in
NA earthquake, alongside the selected US states in the current query. NA
hurricane currently includes all US exposure.

## Currency and the preloaded input

The SQL assumes source GBP and applies `@gbp_to_usd` once in its final SELECT
(default **1.35**). It returns **full USD**, not USD millions. The population
workbook divides monetary amounts by one million and does **not** apply FX again.

The initial 737 input rows were copied from the uploaded
[bscr_output_wseq.csv](../../bscr/reconcile/bscr_output_wseq.csv). They are not
sample data or a live query result. We reproduced all 737 rows from the uploaded
EDM tables, with exact counts and monetary differences below one cent. The
initial filename is recorded in the SQL input header comment; it does not
change automatically when new results are pasted.

Two supplied GB wind rows have no recognized entity. They are retained in the
input but not assigned to one of the five entity tabs. Their gross/net exposure
totals approximately USD 26.353bn; this is separate from earthquake `ALL`.

## Reconciliation evidence

[BSCR_Reconciliation.xlsx](../../bscr/reconcile/results/BSCR_Reconciliation.xlsx)
has five tabs: **What this tests**, **Schedule X(f)**, **Counts**, **Gross exposure**
and **Net exposure**. It keeps reconciliation separate from routine population.

The evidence chain is:

**Corrected February templates → old saved output → legacy query → corrected query → new saved output.**

- The template check uses the **33 original** and **3624/HIC/HIG/HSA v2** files
  in `bscr/reconcile/filled in templates/`. All 528 populated count/exposure
  cells tested in the selected X(f) blocks match the old pre-FX output and
  legacy query within rounding. Other fields are not certified by that test.
- Those saved February monetary values are **pre-FX amounts divided by 1,000**,
  despite USD headings. The later workings' **1.35 USD conversion was missing**.
  Currency and thousand/million scaling are separate issues. The reconciliation
  shows the saved value, USD conversion at the same scale, and USD millions.
  Green `MATCH` means agreement **after the stated conversion**, not that the
  original template was already in USD. Counts never receive FX.
- The original SQL and Python aggregation reproduce all **452 historical CSV
  rows**. The retained legacy SQL also matches the **49 groups** in the later
  March USD workings. Counts are exact and monetary residuals are below one cent.
- Fixing only the geocode join explains the whole earthquake `ALL` reduction:
  **USD 4.813bn gross, USD 3.051bn net and 285 grouped rows**, across **184 accounts**
  with both geocode flags. The old join duplicated exposure between buckets;
  source policies were not deleted.
- Policy-ID grouping has no material effect on this snapshot because no account
  has multiple type-1 policies. This is not a rule for other datasets.
- All five April total counts and all 46 populated regional gross/net limits
  match the later historical workings (regional money within USD 1). Rounded
  overall amounts and manually reallocated classification splits can differ.

These checks were local DuckDB replays against saved outputs, not live SQL Server
executions. Case-insensitive source comparisons and legacy Python's case-sensitive
geographic comparisons were distinguished. File dates do not prove submission.

## Legacy query and reference workbooks

Only two SQL scripts are retained:

| Script | Role |
|---|---|
| `bscr-output.sql` | Current calculation and input to the population workbook |
| [bscr-extract-legacy.sql](../../bscr/sql/bscr-extract-legacy.sql) | Full historical aggregate, despite its name; diagnostic only |

The legacy query intentionally retains old geocode duplication, cap grouping
without policy ID, earthquake/policy type 1 for every region, and Python-style
case-sensitive geography. Both queries return eight columns and default to
full USD at FX 1.35. Set legacy FX to 1 only to compare directly with the old
unconverted CSV. The queries differ in more than geocoding; the controlled
reconciliation isolated each change rather than attributing every region's
difference to the join.

`workings_old_report.xlsx` is identical to `Workings_with_geocodingFW.xlsx`.
The earlier workings divide by 1,000; FW divides by 1,000,000. The later
`Workings_with_geocodingFW - Including blanks USD.xlsx` applies FX and restores
US exposure to NA hurricane. Do not reproduce the earlier workbook's US omission
in the current calculation.

The older `bscr/workbooks/BSCR_Workings.xlsx` is **not the current population
workbook**. It has been restored byte-for-byte from Git revision `d6aedfe`
(21 September 2026), the preceding distinct version after a later workbook was
reported corrupt. The restored package/XML and formula/cached-value
loading pass local checks, but native Excel opening still needs confirmation.
Earlier versions' fixed ranges, Japanese peril references and workbook FX
remain historical risks. Use the new eight-column population workbook for the
current route, not this restored reference file.

Historical Python scripts are archived in `bscr/old-process/`:
`BSCR_UKEU.py` is the original Marimo application and
`BSCR_UKEU_offline.py` is the older seven-column CSV workflow. The duplicate
top-level Marimo copy was removed after verifying identical contents. Neither
is the current producer; active local builders remain in `bscr/tools/`.
Source templates, raw workbooks and historical CSVs remain
unchanged as evidence; their cached errors, external links and placeholders do
not constitute approved current inputs.

## Raw source data and verification limits

The six uploaded files in `bscr/sql/edm-parquet/` are **CSV**, despite the folder name:

| File | Verified rows / content |
|---|---:|
| `01_accgrp.csv` | 354,830 |
| `02_policy.csv` | 662,306 |
| `03_loc.csv` | 1,008,151 |
| `04_loccvg.csv` | 1,053,391 |
| `source_metadata.csv` | Database, time, collation and row counts |
| `06_schema.csv` | Source column definitions |

All four source counts match the metadata for
`HISCO_UKEU_01JAN26_010126_ROLLUP_ByLOB_GC_EDM`. Preserve duplicates, native
values and empty strings versus NULL representations. Do not apply FX or
resave the raw CSVs in Excel. The 30 literal `NULL` state markers occur in
French/German locations; raw lexical values were preserved during inspection.

The local builder `bscr/tools/build_population_workbook.py` verifies **630
automatic mappings** with an independent Excel-function engine and writes cached
formula results. Input-change tests covered counts, gross/net, US subtraction,
wind routing and missing-entity warnings. Native Excel rendering/recalculation
was not available locally; the work-laptop review remains necessary.

Remaining controls include the source currency/rate for each new run, policy-cap
allocation grain, grouped-row versus distinct-contract counts, unmapped entities,
manual supplemental inputs and final-template approval. The agreed geocode proxy
is implemented; it is not a claim that all April manual classifications were
reproduced. See [decisions](../decisions.md#bscr-01) and the
[discrepancy register](../calculation-discrepancies.md#bscr-schedule-x).

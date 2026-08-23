# BSCR Schedule V

## Status and source boundary

The repository contains an executable Marimo/Polars transformation in
[`bscr/BSCR_UKEU.py`](../../bscr/BSCR_UKEU.py), its
[guide](../../bscr/bscr_guide.md), and its
[runbook](../../bscr/bscr-runbook.md). The copies under `docs/` are identical
historical notes: [`docs/bscr_guide.md`](../bscr_guide.md) and
[`docs/bscr-runbook.md`](../bscr-runbook.md).

**Workbook availability:** no BSCR Excel workbook is present. A
Git-ignore-disabled search of the current tree found no `.xlsx`, `.xlsm`,
`.xls`, `.xlsb`, `.ods`, or `.csv` file. A case-insensitive, full-history
search of every reachable Git ref found no tracked file with any of those
extensions either. The relevant path history consists only of additions of the
Python and Markdown sources. Consequently, neither a current workbook
nor an earlier workbook can be recovered from this repository's reachable
history.

**Green-output/formula evidence:** the historical
[`docs/readme.md`](../readme.md) (duplicated as
[`docs/readme3.md`](../readme3.md)) names a `PRA_BSCR_Aggs` workbook and says
its green tabs contain slow formulas which split class/Fine Art data into pivot
tables. That note also calls the process the January/February PRA return, while
its header says its purpose is BSCR aggregates. It is therefore evidence that
such a spreadsheet-led workflow was used historically, not evidence of the
workbook's exact BSCR formulas or current suitability. With no workbook to
inspect, this repository does **not** prove the formulas, pivot definitions,
sheet names or colours, external links, calculation settings, or the values on
any final green output sheet. Recover the approved reporting-cycle workbook and
current Schedule V template from outside the repository before the spreadsheet
stage.

## Terminology used in this guide

| Term | Meaning supported by the repository |
| --- | --- |
| BSCR Schedule V | The return and schedule named by the BSCR runbook. The repository does not contain the regulator's template or define its current requirements. |
| EDM | The SQL Server exposure database read by the script, including the `loccvg`, `loc`, `policy`, and `accgrp` tables. |
| Marimo | The notebook-style Python application framework used by `BSCR_UKEU.py`; its cells can also run as one Python application. |
| Polars | The dataframe library used to classify, aggregate, reshape, and export the SQL result. |
| PML | The `pml` amount calculated by the embedded SQL. The repository calls it an aggregate/limit but does not establish the reporting currency or a regulator definition. |
| Gross and net | `sum_pml` is the pre-retention amount; `sum_net` is the amount after the checked-in `_QS` or `_SRP` multiplier. |
| NAHU / NA EQ / JP / EU / US | Names represented by the output flags `is_nahu`, `is_na_eq`, `is_jp`, `is_eu`, and `is_us_all`. Their actual checked-in country/state rules are listed below; the repository does not prove they are current regulatory definitions. |
| Fine Art QS / SRP | Name markers `_QS` and `_SRP` in `userid1`. The sources call them Fine Art retention categories but do not expand the abbreviations. |
| All World excluding US | The historical manual calculation `ALL` minus the `is_us_all` pivot result, also described as “All World xUS.” |

## What the repository process produces

The script reads catastrophe-exposure data from a SQL Server EDM, calculates
property limits/aggregates, assigns entities and geographic flags, applies two
name-based Fine Art retentions, and writes one long-form `output.csv`. Although
the runbook describes five required entity outputs, the code writes one CSV
and distinguishes the five entities in its `bscr_entity` column; it does not
write five files or populate a regulatory workbook.

The workflow is:

```text
annual SQL Server EDM
  -> embedded T-SQL exposure extract
  -> Polars entity/region/Fine Art transformations
  -> output.csv
  -> manual Excel pivots and ALL less US-only difference
  -> approved BSCR Schedule V workbook and review
```

The final two stages are historical/manual procedures. They are not automated
or inspectable here.

## Inputs and prerequisites

Obtain and record all of the following before running:

1. The correct annual SQL Server EDM, in the supplied schema expected by the
   embedded query. [`docs/index.md`](../index.md) warns that the query was
   written for the particular 2026 EDM format and is not generic.
2. SQL Server permission through a trusted Windows/Microsoft connection and an
   installed ODBC driver. The code currently names `ODBC Driver 18 for SQL
   Server`, enables encryption, and trusts the server certificate.
3. Python 3.13+, `uv`, and the dependencies declared in
   [`pyproject.toml`](../../pyproject.toml), including Marimo, Polars,
   SQLAlchemy, pyodbc, and tabulate.
4. The approved BSCR Schedule V template/workbook, reporting instructions,
   sign-off requirements, and any controlled mappings. None is stored here.
5. An approved currency basis and rates. The code explicitly says it does not
   perform currency conversion, and its output has no currency column.
6. Approved entity, geography, geocoding, Fine Art retention, and policy-count
   rules for the reporting cycle. The repository contains hard-coded historical
   values, not evidence of regulator requirements.

The checked-in connection values are historical configuration, not defaults to
accept without review:

- server: `pr0503-14002-00\LMRMSINSURANCE`;
- database: `HISCO_UKEU_01JAN26_010126_ROLLUP_ByLOB_GC_v25_EDM`;
- trusted connection, encrypted connection, trusted server certificate, and a
  30-second timeout.

Do not put credentials in the script. Confirm the EDM snapshot and connection
security with the data owner.

## Run the SQL and Python stages

1. From the repository root, install the locked environment:

   ```bash
   uv sync
   ```

2. Open the notebook and select `bscr/BSCR_UKEU.py`:

   ```bash
   uv run marimo edit bscr/BSCR_UKEU.py
   ```

   The historical runbook also permits running the Python file directly, but
   cell-by-cell Marimo execution makes configuration and intermediate totals
   visible.

3. In the connection cell, replace `SERVER` and `DATABASE` with the approved
   EDM values. Change the driver or certificate settings only through the
   normal controlled connection process. Run the cell; `SELECT 1 AS ok` must
   return `1` or its assertion fails.

4. Review the embedded `query` before executing it. It:

   - selects `peril = 1` from `loccvg` and sums `valueamt` by location and
     deductible/currency/limit fields;
   - sets location PML to zero when summed value is below the deductible, and
     otherwise retains the full summed value;
   - joins `loc`, `accgrp`, and `policy`, derives `is_geocoded` from
     `addrmatch`, and retains US state while blanking state for other countries;
   - selects `policytype = 1`, derives `policy_limit` as zero when
     `blanlimamt = 0` and otherwise uses `partof`, caps account/location PML at
     that value, and returns account-level PML by geography, portfolio name,
     writer, and geocoding status.

5. Run the extraction cell. The implemented path is
   `pl.read_database(query, engine)`. The file header says the historical
   process actually used an XLSX containing the same data, while the runbook
   suggests manually exporting SQL to CSV and replacing the database read with
   `pl.read_csv` when connectivity cannot be established. Neither alternative
   is implemented in the checked-in script, and no source XLSX/CSV is present.
   A fallback therefore requires a controlled code change plus a schema and
   total reconciliation; merely placing a file beside the script will not work.

6. Record the script's printed working directory, selected columns, and raw
   total PML. The extracted working fields are `pml`, `accgrpid`, `uwritrname`,
   `state`, `userid1`, `cntrycode`, and `is_geocoded`.

7. Run the remaining cells in order through the CSV write. `output.csv` is
   written to the process's current working directory and an existing file of
   that name may be replaced.

## Configuration and transformations

### Entity assignment

`LOB_COLUMN` is `userid1`. `which_entity` uppercases it and returns the first
configured code found as a substring, in this order:

| Order | Entity code |
| ---: | --- |
| 1 | `HIG` |
| 2 | `HSA` |
| 3 | `33` |
| 4 | `3624` |
| 5 | `HIC` |

This is substring matching, not an exact controlled mapping. A value containing
more than one code receives the first; a value containing none receives null;
and the short code `33` can match unrelated text. Review all distinct
`userid1` values and explicitly reconcile null, ambiguous, and unexpected
matches before using the output.

### Regional flags

Rows can satisfy more than one flag. The script unpivots every true flag, so
such exposure contributes to each applicable regional total.

| Output region | Checked-in rule |
| --- | --- |
| `is_nahu` | Country in `US`, `CB`, `TC`, `BH`, `JM`, `VI`, `MX`. A US state list is declared (`Florida`, `Texas`, `Louisiana`, `Mississippi`, `Alabama`, `North Carolina`, `South Carolina`, `New Jersey`, `Virginia`, `New York`, `Connecticut`, `Delaware`, `Georgia`), but the current condition never applies that list to a non-null state. In practice every US row passes. |
| `is_na_eq` | All `CA`; `US` only when state is null or one of `California`, `Washington`, `Oregon`, `South Carolina`, `Tennessee`. |
| `is_jp` | Country `JP`. |
| `is_eu` | Country in `GB`, `UK`, `FR`, `DE`, `BE`, `NL`, `LX`, `AT`, `DK`, `SE`, `PL`, `CZ`. These are literal checked-in codes, including `LX`. |
| `is_us_all` | Country `US`. |
| `ALL` | Added separately for every row, independent of the regional flags. |

The dedicated guide warns that the hurricane-region definition may not be fully
accurate. The `is_nahu` control-flow issue above is an additional inspectable
code fact: the declared state whitelist is currently ineffective. Do not change
selection logic during a production run without approval, but do not treat it
as validated merely because it ran.

### Fine Art retention

The code infers treatment solely from the uppercased `userid1` text:

- text containing `_QS`: `net = pml * 0.5`;
- otherwise, text containing `_SRP`: `net = pml * 0.3333`;
- otherwise: `net = pml`.

If both markers occur, `_QS` wins because it is the first branch. The script
does not independently establish that a marked row is Fine Art or that the
percentages are current treaty terms. Reconcile the classification and approved
retentions before handoff.

### Aggregation and CSV schema

Polars first groups by entity, all five regional booleans, geocoding status,
and country. It calculates `sum_pml`, `sum_net`, and `count_policies` using row
count. It then unpivots true regions and appends an independently aggregated
`ALL` region. The final CSV is sorted by region, entity, geocoding status, and
country and contains:

| Column | Meaning in the code |
| --- | --- |
| `cntrycode` | EDM country code |
| `bscr_entity` | Substring-derived entity, possibly null |
| `region` | One of the five flag names or `ALL` |
| `sum_pml` | Sum before Fine Art retention |
| `sum_net` | Sum after the two retention rules |
| `count_policies` | Count of grouped extract rows, not a distinct policy-ID count |
| `is_geocoded` | `addrmatch = 0` gives false; every other value gives true |

## Manual Excel stage and final handoff

The BSCR-specific historical notes say that the operator created three pivot
tables and made a quick difference. The runbook describes the operation only as:

1. copy/import `output.csv` into the BSCR workings workbook;
2. pivot the raw data;
3. subtract the US-only result (`is_us_all` in the CSV) from `ALL` to obtain
   All World excluding US limits and policy counts;
4. transfer the reviewed results to Schedule V.

The notes do not define the three pivot layouts, cell formulas, rounding,
currency treatment, sheet names, or final template mapping. Do not invent them.
Use the recovered, approved workbook and current instructions. Keep the raw CSV
unchanged as evidence, refresh or rebuild the controlled pivots, confirm the
`ALL - is_us_all` difference for both CSV amount measures and the accepted
count measure, and obtain workbook review. A green sheet is not generated by
this script, and colour alone is not a control.

The final handoff should include the exact EDM identity, script revision,
configuration and approved overrides, execution timestamp/operator, raw query
total, immutable `output.csv`, currency treatment, reconciliations, reviewed
workbook, and the submitted Schedule V values.

## Required validations and material limitations

Before treating the result as return-ready:

- **Currency:** `deductcur`/`limitcur` are used in SQL grouping, but currencies
  are dropped before the final extract and no conversion occurs. Aggregating
  mixed currencies and attempting to convert only the final CSV is unsafe
  because the CSV has no currency. Establish a single-currency EDM or apply an
  approved conversion at a stage retaining currency, then reconcile it.
- **Counts:** the SQL final result no longer contains `policyid`, and Polars uses
  `pl.len()`. `count_policies` therefore counts rows at the extract/group grain,
  not distinct policies. The guide warns of potential double counting between
  states and countries, especially in All World. The runbook also calls the
  `ALL - US` method technically incorrect for cross-border policies, although
  it was judged immaterial for historical UKEU data. That historical
  materiality judgement must be reassessed for the current return.
- **Geography:** review all input country/state codes, null states, overlapping
  region membership, the ineffective NAHU US-state list, and the literal EU
  list against approved current definitions.
- **Entity and Fine Art:** reconcile source PML and net PML by each of the five
  entities, investigate null/unexpected entity rows, and independently confirm
  `_QS`/`_SRP` classification and retention percentages.
- **SQL approximations:** the query applies simplified deductible and policy
  limit logic and is coupled to one EDM shape. The BSCR guide says it was
  compared with a RiskLink aggregation and was similar but not identical,
  implying uncaptured policy terms. The spreadsheet/PRA note separately claims
  TSI within 1%; neither historical comparison substitutes for a current-cycle
  reconciliation.
- **Totals and completeness:** reconcile raw EDM/extract totals to the printed
  PML, the `ALL` CSV totals, entity totals, regional totals, geocoded and
  ungeocoded totals, and the workbook pivots. Explain every exclusion,
  duplication, and null bucket. Because regions overlap, regional totals are
  not expected to add to `ALL`.
- **Manual difference:** independently recalculate `ALL - is_us_all`; investigate
  negative or unexpected values and verify the accepted cross-border handling.
- **Final workbook:** inspect formulas, pivots, links, calculation mode, errors,
  currency/units, rounding, mappings, green output sheets, and Schedule V
  transfer in the recovered workbook. None of those controls can be completed
  from the repository alone.

The hard-coded grouping columns noted in [`docs/index.md`](../index.md), the
single fixed output filename, absence of distinct policy IDs and currency in the
CSV, and missing final workbook are material operational constraints, not minor
documentation gaps.

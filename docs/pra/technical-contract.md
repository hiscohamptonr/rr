# PRA technical contract — server export and offline calculation

This reference records the contract for `bscr/BSCR_UKEU.py`, the
server-side query `pra/sql/pra-raw.sql`, and the historical
`PRA_BSCR_Aggs.xlsx` reference workbook. It is not an approved producer,
all-peril population, currency basis, mapping policy, PRA methodology, or
final return; [handoff.md](handoff.md) records the unresolved external
destination.

## Source routes and provenance

The active route is deliberately split: run `pra/sql/pra-raw.sql` on the
approved SQL Server, export one seven-column CSV into a run folder, and run
the Python calculation offline from that folder. Python has no database
connection, database flags, workbook reads, or embedded SQL execution in this
route. The old `pra/sql/aggs-from-edm.sql` and embedded workbook `sql` sheet
are historical query evidence only; they are not active execution steps.

The optional `pra/sql/pra-earthquake.sql` is a direct five-column earthquake
aggregate for comparison. It is not the seven-column `pra-source.csv` input
for the offline script.

Required provenance for each folder is the approved snapshot, EDM database
and roll-up/version, reporting/as-of date, peril and policy codes,
script/query revisions, mapping versions, execution date, operator,
reviewer, row counts, totals, and the controlled metadata/reconciliation
record. A folder is one snapshot and one peril/policy selection.

## Folder and CSV contract

For a PRA run, set `PRA_INPUT_CSV` at the top of the script to the full CSV path; the example filename is:

```text
pra-source.csv
```

Its exact header and seven-column order are:

```text
pml,accgrpid,uwritrname,state,userid1,branchname,cntrycode
```

The Python process writes these exact files to the output directory:

```text
pra-raw.csv
pra-aggregate.csv
```

`pra-raw.csv` retains the seven input columns. `pra-aggregate.csv` has
exactly five columns in this order:

```text
pml,state,userid1,cntrycode,uwritrname
```

The separate BSCR input is `bscr-source.csv` with eight columns
`pml,accgrpid,uwritrname,state,userid1,branchname,cntrycode,is_geocoded`;
it is not valid PRA input. A five-column direct aggregate is not valid raw
input.

Set `OUTPUT_DIR` to a new or empty output folder, `PRA_INPUT_CSV` to the
PRA file path and `BSCR_INPUT_CSV` to `None`; configure both input paths to run
both calculations. At least one is required and filenames are arbitrary.

## Server-side query behaviour

For the selected peril/policy type, `pra/sql/pra-raw.sql`:

1. selects `loccvg` rows for the approved peril;
2. sums `valueamt` by location and deductible/limit grouping fields;
3. sets grouped amount to zero when it is below `deductamt` (it does not
   subtract the deductible; equality retains the amount);
4. groups to account/geography;
5. joins the selected policy type and caps with the query's
   `partof`/`blanlimamt` policy-limit logic; and
6. exports the seven-column raw grain consumed by Python.

The PRA query defaults are `@peril = 2` and `@policy_type = 2`; the BSCR
query defaults are `1/1`. Approval of an all-peril code and population is
unresolved, so defaults are not evidence that a run is all-peril.

The query does not allocate account PML to locations by TIV. Deductible and
limit currencies are grouped but not converted. Null deductible retains the
value; zero `blanlimamt` zeroes the cap branch. Null/negative currency or
limit behaviour requires an approved treatment. Policy-join cardinality and
cross-product risk require review rather than assumption.

## Offline execution

From the repository root, create the calculation environment once:

```text
python -m venv .venv
```

Set `PRA_INPUT_CSV = Path(r"C:\Returns\eq\input\pra-source.csv")`,
`BSCR_INPUT_CSV = None`, and `OUTPUT_DIR = Path(r"C:\Returns\eq\output")`
at the top of the script. On Windows, install the pinned requirements and run with no arguments:

```text
.venv\Scripts\python -m pip install -r bscr/requirements.txt
.venv\Scripts\python bscr/BSCR_UKEU.py
```

On macOS/Linux, use `.venv/bin/python` in place of
`.venv\Scripts\python`:

```text
.venv/bin/python bscr/BSCR_UKEU.py
```

No `uv`, ODBC driver, SQL connection, server flag, database flag, or
workbook is required on the calculation PC. For an all-peril snapshot, use
different input/output folders and the approved source files; never mix it
with an earthquake folder.

After the process, verify the exact headers and expected files, compare row
counts and `pml` totals with the approved extract under the same currency,
unit, and rounding tolerance, and retain both outputs with metadata. A
failure or missing output means load nothing from that folder.

## Current workbook option (optional)

`pra/workbooks/PRA_Aggs.xlsx` is an optional review surface for the
five-column aggregate only, not a calculation prerequisite. An operator may
load approved `pra-aggregate.csv` with headers into `pivot_eq!A1:E`, or
into `pivot_allperil!A1:E` for a separately approved all-peril scope,
after clearing stale input rows, then check table totals and pivot sources.
The workbook has no raw-data or SQL-tab destination; `pra-source.csv` and
`pra-raw.csv` remain offline audit artifacts.

The retained mapping sheets are `region_mappings`, `cds_mapping`, and
`rms_geog`. The optional aggregate labels are P3 total PML/Fine Art, P10
portfolio/country/Fine Art, X10 country/Fine Art, and AC10 CDS class.
Cached pivots, labels, formatting, and `($M)` text do not prove lineage,
currency conversion, source/value field, or final-return destination.

The retained earthquake pivot caches initially reference `Table3`; correct
them to `Table32` before earthquake refresh. All-peril pivots use `Table3`.

The former `PRA_BSCR_Aggs.xlsx` is available in repository history only.
Its raw-data sheet, legacy SQL tab and BSCR helper panels were removed from
the renamed current workbook; CSVs retain the raw calculation evidence.

## Formula, geography, and financial discrepancies

The retained workbook formula surfaces derive Fine Art when `userid1`
contains `_FA_` case-insensitively, derive country/US labels and PRA region
by lookup, derive CDS class by `userid1` lookup, and compute
`Agg_USD = pml * 1.25`. The checked-in pivots sum `pml`, not `Agg_USD`, so a
USD label is not established by the factor alone.

The existing Python calculations remain unchanged, including retention and
geography discrepancies. Review `_SRP` (33% in the removed raw-sheet formulas
versus 0.3333 in Python and 0.33333 in supplementary SQL), materially different NAHU
geography logic, `1.25`, mapping versions, source currency, and intended
value field. A populated CDS/PRA-region `#N/A`, wrong source/value field,
unapproved currency basis, partial file, or missing scope evidence is a stop.

## All-peril boundary

The repository does not identify the confirmed all-peril producer,
population, or scope. Codes `1/1` and `4/4` remain candidates and must not
be promoted by a successful query or Python run. Keep every candidate in a
separate named folder, record its codes and population evidence, and apply
the same header, total, mapping, currency, and tolerance checks.

## Reconciliation and handoff boundary

Reconcile the server export, `pra-raw.csv`, `pra-aggregate.csv`, and any
optional historical workbook comparison using the same currency/unit and
approved rounding tolerance. Record query/script version, source folder,
mapping/rate versions, amount, currency, unit, as-of date, preparer,
reviewer, and review date.

These are reviewed internal calculation outputs, not a completed PRA return.
No final PRA template or approved source-range-to-destination-cell map is
checked in. An operator or LLM must not repair mappings, infer all-peril
scope, treat cached pivots as lineage, or infer a destination from labels or
colour.

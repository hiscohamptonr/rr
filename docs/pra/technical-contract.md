# PRA technical contract — observed mechanics for humans and LLMs

This reference records observed behaviour of `bscr/BSCR_UKEU.py`,
`pra/sql/aggs-from-edm.sql`, and `PRA_BSCR_Aggs.xlsx`. It is the implementation
contract behind [runbook.md](runbook.md), not an approved producer,
all-peril population, currency basis, mapping policy, PRA methodology, or
final return. [handoff.md](handoff.md) contains evidenced lineage and
unresolved external destinations.

## Source routes and provenance

The workbook is a combined calculation workbook: PRA geography/class pivots
and separate BSCR earthquake-split panels. It is not the final PRA submission
template. The Python route produces regeneration candidates. The workbook also
contains a legacy SQL route; the SQL file matches that embedded query family.
Neither route proves how cached tables were populated because no prior run
record is embedded in the workbook.

The legacy route is externally reported as
`HISCO_UKEU_01JAN26_010126_ROLLUP_ByLoB_GC_v25`; Python currently defaults to
`HISCO_UKEU_01JAN26_010126_ROLLUP_ByLOB_GC_v25_EDM`. The workbook does not
evidence the former database. An operator must select the approved database
explicitly and record it; neither name is approval.

Required provenance for each run is server, EDM database and roll-up/version,
reporting/as-of date, peril and policy codes, script/query revision, mapping
versions, execution date, operator, reviewer, row counts, totals, and the
controlled workbook copy.

## CSV contracts and query behaviour

For a selected peril/policy type, Python writes these PRA shapes:

```text
PRA raw A:G:       pml, accgrpid, uwritrname, state, userid1, branchname, cntrycode
PRA aggregate A:E: pml, state, userid1, cntrycode, uwritrname
```

The BSCR-shaped control/source files are separate reads and are context for
the selected parameters; they are not a transactional snapshot or proof that
PRA amounts must match.

The query:

1. selects `loccvg` rows for the approved peril;
2. sums `valueamt` by location and deductible/limit grouping fields;
3. sets the grouped amount to zero when it is below `deductamt` (it does not
   subtract the deductible; equality retains the amount);
4. groups to account/geography;
5. joins the selected policy type and caps with the query's
   `partof`/`blanlimamt` policy-limit logic; and
6. writes either the seven-column raw grain or five-column pivot-input grain.

It does not allocate account PML to locations by TIV. Deductible and limit
currencies are grouped but not converted. Null deductible retains the value;
zero `blanlimamt` zeroes the cap branch. Null/negative currency or limit
behaviour requires owner approval. Policy-join cardinality and cross-product
risk must be reviewed rather than assumed away.

## Workbook sheets, tables, and ranges

| Sheet | Role | Input/table identity |
|---|---|---|
| `region_mappings` | Country/territory to Standard Formula and PRA region | Mapping source |
| `pivot_allperil` | All-peril aggregate, formulas, all-peril pivots | A:E → `Table3`; F:M formulas |
| `pivot_eq` | Earthquake aggregate, formulas, earthquake pivots | A:E → `Table32`; F:M formulas |
| `raw_data_for_bscr_splits_eq` | Earthquake raw input, flags and BSCR panels | A:G → `Table2`; H:P formulas; Q unused |
| `cds_mapping` | Portfolio/CDS class lookup | Formula lookup source |
| `rms_geog` | RMS country/region lookup | Formula lookup source |
| `sql` | Legacy aggregate extraction query (2/2) | Query evidence |

Checked-in January evidence contains 838-row aggregate tables and a
270,675-row earthquake raw input. Those counts are comparison points, not
future fixed sizes. Data rows must be loaded below headers, tables resized to
the exact final row, and no blank table rows or data outside the table left
behind. CSV headers must never be pasted into row 2.

**Destination distinction is material:** the earthquake raw file goes only to
`raw_data_for_bscr_splits_eq!A:G`; the earthquake aggregate goes only to
`pivot_eq!A:E`; and an approved all-peril aggregate goes only to
`pivot_allperil!A:E`. No all-peril raw destination is documented. Do not
create one or use an earthquake destination for all-peril data.

## Formula and pivot behaviour

Input-table formulas derive:

- Fine Art when `userid1` contains `_FA_`, case-insensitively; `uwritrname`
  is not used for this classification;
- country display and US country/state labels;
- PRA region from `region_mappings`;
- CDS class from `cds_mapping`; and
- `Agg_USD = pml * 1.25`.

The `1.25` factor belongs to the workbook calculation. All eight checked-in
pivots sum field 0 (`pml`), not `Agg_USD`; therefore a USD-labelled pivot is
not established by the factor alone. Confirm the intended value field,
currency, and unit before relying on output.

`pivot_eq` currently has four pivots sharing the all-peril cache (`Table3`).
Before use, every earthquake pivot must resolve to `Table32`, every all-peril
pivot to `Table3`, and visible grand totals must equal the approved table
totals. Cached-pivot similarity is not lineage.

`CDSClass` is an unguarded `XLOOKUP` on `userid1`. Any populated CDS/PRA-region
row with `#N/A` is a stop. The checked-in baseline has material CDS-unmapped
exposure. Helper-column errors may be counted separately only when bypassing
them is explicit and approved. The raw `is_na_eq` (Q) column is empty; it
cannot identify North American earthquake rows.

## Earthquake execution and load

Use a new empty output directory. From the repository root:

```bash
uv sync --locked
uv run python bscr/BSCR_UKEU.py \
  --server '<approved-server>' --database '<approved-edm>' \
  --peril 2 --policy-type 2 \
  --output '<run-dir>/bscr-2-2-control.csv' \
  --source-output '<run-dir>/bscr-2-2-source.csv' \
  --pra-raw-output '<run-dir>/pra-eq-raw.csv' \
  --pra-aggregate-output '<run-dir>/pra-eq-aggregate.csv'
```

The command writes files sequentially. If it fails or any expected file is
missing, retain the run record but load nothing. Retain all four CSVs and
metadata. The command's `--help` path does not connect to SQL Server.

In a controlled workbook copy, record formulas, table ranges, pivot sources,
calculation mode, mappings, and pre-refresh totals. Clear only old input rows
in `raw_data_for_bscr_splits_eq!A:G`; preserve headers, H:P, right-hand
panels, formatting, and Q. Validate the header, paste data rows in existing
order starting at A2, fill H:P through the final row, and inspect blanks and
Excel errors.

Clear only old input rows in `pivot_eq!A:E`; validate the aggregate header,
paste data rows at A2, fill F:M, and resize `Table2` and `Table32` exactly to
the loaded ranges. Reconcile raw `pml`, grouped aggregate `pml`, and completed
input-table totals before any pivot refresh.

In Excel, point every `pivot_eq` pivot at `Table32`, verify that it covers the
complete earthquake input, and refresh only the intended pivots. Check that
all-peril pivots point to `Table3`. Use **Data > Refresh All** only when
unapproved external connections cannot update. Recalculate, inspect
`#REF!`, `#N/A`, and `#VALUE!`, and compare before/after values.

The checked-in January earthquake source total is
`233,586,155,482.80`. A same-snapshot reproduction must reconcile to its
approved source in the defined currency/unit and rounding tolerance. A new
period is not required to equal January; it requires independently approved
population, mappings, controls, and tolerance.

## All-peril execution and load

The repository does not contain the confirmed all-peril producer or population.
Codes `1/1` are only a candidate. If the owner approves that scope, run:

```bash
uv run python bscr/BSCR_UKEU.py \
  --server '<approved-server>' --database '<approved-edm>' \
  --peril 1 --policy-type 1 \
  --output '<run-dir>/bscr-1-1-control.csv' \
  --source-output '<run-dir>/bscr-1-1-source.csv' \
  --pra-raw-output '<run-dir>/pra-allperil-raw-candidate.csv' \
  --pra-aggregate-output '<run-dir>/pra-allperil-candidate.csv'
```

Do not load merely because this command succeeds. Confirm that 1/1 is the
approved all-peril scope and retain both PRA files, both control/source files,
and full metadata. For a same-snapshot reproduction, compare the candidate
with the checked-in all-peril cached-input total `255,773,631,164.60` under
approved currency/unit and tolerance. A new period may differ from January
but must have independently approved population, mappings, currency, controls,
and tolerance.

Only after that approval, clear old data rows in `pivot_allperil!A:E`, paste
aggregate data rows (never the header) at A2, fill F:M, resize `Table3` exactly,
confirm each all-peril pivot source, refresh/recalculate, and reconcile. There
is no documented all-peril raw load; the candidate raw file is retained as
evidence/control, not assigned a workbook destination.

## Geography, BSCR panels, and known discrepancies

The raw sheet identifies HIG, `_QS`, `_SRP`, and North American hurricane rows,
but its empty `is_na_eq` does not calculate a North American earthquake panel.
Its panels overlap the separate Python/BSCR-workings route and are incomplete
BSCR aids, not final BSCR values. In this workbook `_QS` is 50% and `_SRP` is
33%.

Resolve or explicitly approve the `_SRP` difference between 33% here, 0.3333
in Python, and 0.33333 in supplementary SQL, and the materially different
NAHU geography logic. Confirm `1.25`, mapping versions, source currency, and
whether the intended pivot field is `pml` or `Agg_USD`. Stop on populated CDS
or PRA-region mapping errors, wrong source/value fields, table size/range
mismatch, unapproved currency basis, partial files, or missing scope evidence.

## Reconciliation and handoff boundary

Reconcile raw input, grouped aggregate, formula columns, table totals, pivots,
and any final return values using the same currency/unit and approved
rounding tolerance. Record producer outputs and how each aggregate table was
populated. Preserve formulas, table definitions, pivot sources, validation,
formatting, and all non-input cells.

`pivot_eq` and `pivot_allperil` are reviewed calculation outputs, not a final
PRA submission. No final PRA template is checked in; destination workbook and
cell addresses remain unresolved until a controlled template and approved
source-to-destination map are supplied. For every transferred value, retain
query/script version, source workbook/range, mapping/rate versions, destination
workbook/cell, amount, currency, unit, as-of date, preparer, reviewer, and
review date. An LLM must not repair mappings, infer all-peril scope, use cached
pivots as lineage, or infer a destination from colour.

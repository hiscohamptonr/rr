# PRA handoff trace

## Status

**Blocked — no approved final PRA return handoff.** This trace records
observable internal lineage only. The final PRA template and approved
source-to-destination map are not checked in. The calculation handoff ends
with the folder-based SQL export and offline Python outputs described in
[runbook.md](runbook.md) and [technical-contract.md](technical-contract.md).

## Evidenced execution lineage

| Stage | Artifact or location | Contract |
|---|---|---|
| Server export | `pra/sql/pra-raw.sql` on the approved SQL Server | One snapshot and peril/policy selection exported as `pra-source.csv` with seven columns: `pml,accgrpid,uwritrname,state,userid1,branchname,cntrycode` |
| Offline raw output | `<output-dir>/pra-raw.csv` | Same seven-column raw grain; no database or workbook access |
| Offline aggregate output | `<output-dir>/pra-aggregate.csv` | Five columns: `pml,state,userid1,cntrycode,uwritrname` |
| Current workbook option | `pra/workbooks/PRA_Aggs.xlsx` | Optional five-column aggregate review in `pivot_eq!A:E` or separately approved `pivot_allperil!A:E`; no raw or SQL-tab destination |
| Optional comparison route | `pra/sql/pra-earthquake.sql` | Direct five-column earthquake aggregate only; not the raw input to Python |
| Former workbook reference | `PRA_BSCR_Aggs.xlsx` in repository history | Removed raw/SQL/panel surfaces are historical evidence only, not current input destinations |

The BSCR source is separate (`bscr-source.csv`, eight columns including
`is_geocoded`) and must not be substituted for PRA input. Each all-peril
snapshot has separate input and output folders; `1/1` and `4/4` remain
unresolved candidates and are not promoted to approved scope.

Set `PRA_INPUT_CSV` at the top of the script to the full raw CSV path and
filename, set `OUTPUT_DIR`, and leave `BSCR_INPUT_CSV = None` for PRA only.
`pra-source.csv` is an example name, not a required basename.

## Checks and retention

Before review, retain the server export, both PRA outputs, exact headers,
row counts, `pml` totals, query/script revisions, snapshot and peril/policy
metadata, mappings, currency/unit basis, and reconciliation/tolerance
record. Stop on missing or partial files, malformed headers, unexplained
totals, mapping errors, unapproved currency/unit, or policy-join
cardinality/cross-product risk.

The existing retention and geography discrepancies remain in force,
including `_SRP` rates (33% in the removed raw-sheet formulas, 0.3333 Python, 0.33333 supplementary
SQL), NAHU geography, CDS/PRA-region lookup errors, and the unresolved
`pml` versus `Agg_USD = pml * 1.25` value-field question. These caveats do
not establish a completed return.

## Workbook notes

The current `pra/workbooks/PRA_Aggs.xlsx` can be retained for optional
five-column aggregate review only: `pivot_eq!A:E` is the earthquake surface
and `pivot_allperil!A:E` is a separate all-peril surface. The former
`PRA_BSCR_Aggs.xlsx` raw sheet `raw_data_for_bscr_splits_eq!A:G`, `sql` tab,
and BSCR panels are historical evidence, not current destinations.
The retained pivot titles are P3 total PML/Fine Art, P10 portfolio/country/Fine Art,
X10 country/Fine Art, and AC10 CDS class; cached
pivots, panels, formatting, and `($M)` text prove neither lineage nor final
destination. Raw CSVs remain offline audit artifacts.

## Missing evidence and contract IDs

- **COMMON-01:** approved snapshot, execution record, mappings/rate versions,
  and reviewer-controlled output directory are missing.
- **PRA-01:** confirmed all-peril producer/population and all-peril scope are
  missing; `1/1` and `4/4` are only regeneration candidates.
- **PRA-02:** approved pivot source/value fields, currency basis, mapping-error
  treatment, NAHU/retention alignment, and table/range change record are
  missing.
- **PRA-03:** final PRA template and approved source-range → destination-cell
  map, including measure/currency/unit/reviewer, are absent.

The trace therefore ends at reconciled internal CSV outputs and optional
historical workbook candidates; no final PRA return value can be transferred
from repository evidence alone.

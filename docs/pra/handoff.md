# PRA handoff trace

## Status

**Blocked — no approved final PRA return handoff.** This trace records
observable internal lineage only. The final PRA template and approved
source-to-destination map are not checked in. Use the [production
runbook](runbook.md), [technical contract](technical-contract.md), [operating
controls](../operating-controls.md), [decisions](../decisions.md), and
[discrepancy register](../calculation-discrepancies.md).

## Evidenced internal lineage

| Stage | Observed source/range | Observed measure or transformation | Next internal stage |
|---|---|---|---|
| Python route | `bscr/BSCR_UKEU.py`, approved EDM snapshot and peril/policy parameters | PRA raw seven-column grain and aggregate five-column grain; query groups/caps without subtracting deductible | `pra-eq-raw.csv` / `pra-eq-aggregate.csv` (or separately approved all-peril candidates) |
| Legacy route | `pra/sql/aggs-from-edm.sql`, embedded `sql` sheet | Separate SQL extraction route; no run record proves it populated cached tables | Must not be substituted for Python without owner approval |
| Raw workbook input | EQ raw CSV → `raw_data_for_bscr_splits_eq!A:G`, `Table2` | Earthquake input; formulas `H:P` derive flags/classifications and BSCR aids | Raw-derived flags/panels; the aggregate table is loaded separately from the EQ aggregate CSV |
| Aggregate workbook input | `pivot_eq!A:E`, `Table32` | Five-column `pml` aggregate input; formulas `F:M` derive workbook measures | Earthquake pivots on `pivot_eq` |
| All-peril workbook input | `pivot_allperil!A:E`, `Table3` | Checked-in all-peril cache and formulas `F:M`; producer/population is not evidenced | All-peril pivots only after approved source and pivot correction |
| Mapping helpers | `region_mappings`, `cds_mapping`, `rms_geog` | XLOOKUP/classification helpers; populated `#N/A` is a stop | Internal pivot labels/values, not external return cells |

Memory-efficient OOXML inspection observed `pivot_eq` and `pivot_allperil`
worksheet dimensions of `A1:AD120045` and the raw earthquake sheet dimension
`A1:AJ270675` in the checked-in workbook. These dimensions are evidence of the
snapshot only, not fixed future load sizes. Cached pivot values do not prove
which route produced them.

## Candidate outputs and unresolved handoff

`pivot_eq` and `pivot_allperil` are candidate internal report outputs. Their
visible geographic/classification labels may support a proposed mapping review,
but no external PRA return template, destination range, approved value field,
currency/unit basis, or reviewer approval is present. Do not infer a final
cell from label position, formatting, cached similarity, or the overlapping
BSCR panels. No `final-cell-map.csv` is created or implied.

The checked-in January earthquake and all-peril totals are historical
comparison evidence. A same-snapshot reproduction should reconcile to its
approved source; a future reporting period is controlled by independently
approved population, mappings, currency, controls, and tolerance and need not
equal January.

## Missing evidence and contract IDs

- **COMMON-01:** approved snapshot, execution record, mappings/rate versions,
  and reviewer-controlled output directory are missing.
- **PRA-01:** confirmed all-peril producer/population and all-peril scope are
  missing; `1/1` is only a regeneration candidate.
- **PRA-02:** approved pivot source/value fields, currency basis, mapping-error
  treatment, NAHU/retention alignment, and table/range change record are
  missing.
- **PRA-03:** final PRA template and approved source-range → destination-cell
  map, including measure/currency/unit/reviewer, are absent.

The trace therefore ends at reconciled internal workbook candidates; no final
PRA return value can be transferred from repository evidence alone.

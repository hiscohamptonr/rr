# BSCR handoff trace

## Status

**Blocked — no approved Schedule X handoff.** This trace records internal
lineage that is observable in the checked-in script/workbooks. It is not a
final cell map and does not turn candidate matches into approved destinations.
Use the [production runbook](runbook.md), [technical contract](technical-contract.md),
[operating controls](../operating-controls.md), [decisions](../decisions.md),
and [discrepancy register](../calculation-discrepancies.md).

## Evidenced internal lineage

| Stage | Observed source/range | Observed measure or transformation | Next internal stage |
|---|---|---|---|
| Query/script | `bscr/BSCR_UKEU.py`; EDM `loccvg`, `loc`, `policy`, `accgrp` | Grouped gross/net output with entity, region, `count_policies`, and geocode classifications | `bscr-source.csv` and seven-column `bscr-output.csv` |
| Workings input | `Workings_with_geocodingFW - Including blanks USD.xlsx`, `Sheet1!A:G` | Script output grain; formulas in `Sheet1!H:K` are filled over the loaded range | Formula columns `Sheet1!H:K` |
| Workings formulas | `Sheet1!H:K` | Observed converted and USD-million formula family; exact formula coverage must be checked per run | `piv` local pivot and static bridge |
| Static bridge | `output!A:F` | Observed static entity/region/geocode rows, not a refreshable link from `Sheet1` | `output!G:J`, then `piv` |
| Consolidation | `output!G:J`, `piv` | `1.35` conversion and `/1,000,000` scaling are workbook mechanics; currency/rate approval remains open | Internal reviewed values only |

The memory-efficient OOXML inspection found dimensions `piv!A2:L78`,
`output!A1:J82`, and `Sheet1!A1:W453` in the checked-in workings file.
These are snapshot dimensions, not approved future load ranges.

The checked-in `output!A:F` rows and `piv` therefore cannot prove lineage after
loading `Sheet1`. An approved bridge must specify key, aggregation, clear/paste,
formula coverage, and reconciliation before refresh.

## Candidate HIC label matches (not approved destinations)

OOXML inspection of `2026 BSCR - UKEU - HIC.xlsx` shows labels for Schedules
X(a), X(b), X(c), and X(f), including region/peril sections in X(c) for
Atlantic Basin Hurricane, North American Earthquake, European Windstorm, and
Japanese Earthquake. The labels are candidate semantic matches for reviewed
`piv` exposure views only. The checked-in workbooks do **not** evidence which
cells are editable for this cycle, which measures are required, or that `piv`
provides EP curves, premiums, model versions, narratives, or X(f) counts.
Never select a destination from label position, fill colour, cached similarity,
or a prior workbook.

A proposed map may be reviewed only when it names the source workbook/range,
measure, currency/unit, as-of date, destination cell, preparer, reviewer, and
approval ID. No such approved map is present, so no HIC cell is approved here.

## Missing evidence and contract IDs

- **COMMON-01:** approved snapshot, parameters, mappings, FX, output directory,
  reviewer, and reproducible run record are missing.
- **BSCR-01:** policy-level grain, join diagnostics, distinct contract count,
  and geography/retention decisions are unresolved.
- **BSCR-02:** no approved `Sheet1` → `output!A:F` static bridge exists.
- **BSCR-03:** HIC mapping and supplemental sources (EP curves, premiums,
  narratives, model classifications, and X(f) methodology/counts) are absent.
- **BSCR-04:** HIC `#REF!` formulas, old external links, and current-cycle
  template defects are unresolved.

Until those artifacts and decisions are supplied, the internal trace ends at
reviewed workings/pivots; it does not continue to a final Schedule X cell.

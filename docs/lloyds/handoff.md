# Lloyd's supplementary handoff trace

## Status

**Blocked — external Lloyd's/RDS template and approved destination map are
absent.** This trace records internal workbook lineage and observed candidate
matches only. It does not infer a final cell from labels, formatting, cached
values, or structural similarity. Use the [production runbook](runbook.md),
[technical contract](technical-contract.md), [operating controls](../operating-controls.md),
[decisions](../decisions.md), and [discrepancy register](../calculation-discrepancies.md).

## Evidenced internal lineage

| Return area | Observed input and range | Observed calculation/output | Handoff status |
|---|---|---|---|
| RoW/global | `lloyds/workbooks/UKEU - Supplementary Info - RDL - Jan26 - Workings - ROW.xlsx`; four extract sheets A:K, scale L, formula M; checked-in pivot sources end row 4,988 | `3. RoW Exposure Monitoring`; M uses `TSI_NET` × scale while labels say USD; fixed source ranges and identical cached perils are observed | Candidate internal report only; source column, unit, scale evidence, dynamic range, and proxy approval missing |
| South Africa EQ | `Core data!A:R`, scale S, T, U; OOXML dimension `A1:U53` | `05 South Africa EQ Aggs`; T uses gross source `TSI` × scale; U derives two-digit zone and report uses `SUMIF` | Candidate CRESTA report only; gross/net, currency, blank-zone quarantine, and range procedure missing |
| California wildfire | `Core data!A:M`, helper N; OOXML dimension `A1:U67` | `06 California Wildfire Aggs`; N normalises county and report aggregates USD-net M | Candidate county report only; wildfire proxy/source and report-date approval missing |
| EU EQ/FL CRESTA | `Core data EQ!A:R` and `Core data FL!A:R`, scale S, T, U; dimensions `A1:V8703` and `A1:V8699` | `11 LIC EU CRESTA` (dimension `B2:O1885`) uses whole-column `SUMIFS`; EQ observed T uses USD-net × scale, flood T formulas mix source-net and USD-net, U applies `Fx!C7` | Candidate CRESTA outputs only; uniform formula, FX direction/date, formula coverage, and unmapped-key treatment missing |

The received S33 workbook and email are provenance/source evidence, not direct
inputs to these calculation sheets: they do not supply every SQL-shaped field
(county, CRESTA, portfolio, or separate EU peril). The handoff therefore needs
an approved SQL branch or approved transformation branch with row-level and
aggregate reconciliation.

## Candidate matches (not approved destinations)

Internal report labels—country/peril totals, South Africa two-digit CRESTA,
California county, and EU CRESTA—are semantic candidates for a future RDS
mapping review. They are not external destination cells. Lloyd's templates,
guidance, and final approved submission are outside the repository. No final
cell map, green/yellow input map, or `final-cell-map.csv` exists here.

A proposed map may be reviewed only when it names the source workbook/tab or
saved query result, report range, measure, currency/unit, as-of date, destination
cell, preparer, reviewer, and approval ID. Never select a destination from
label position, fill colour, cached arithmetic, or a prior cycle.

## Missing evidence and contract IDs

- **COMMON-01:** approved snapshot, run metadata, controlled output hashes,
  reviewer, and shared FX/units controls are missing.
- **LLOYDS-01:** approved producer/transformations, portfolio/proxy decisions,
  and source lineage from S33 evidence to each core sheet are missing.
- **LLOYDS-02:** RoW source measure/unit/scale, South Africa gross/net and
  currency, California wildfire proxy/date, EU uniform measure and FX basis,
  and all exception quarantines are unresolved.
- **LLOYDS-03:** external Lloyd's/RDS template, guidance, and approved
  source-range → destination-cell map are absent.

The trace ends at internal report candidates and cannot authorize transfer to a
final Lloyd's return.

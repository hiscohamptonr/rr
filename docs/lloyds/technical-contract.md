# Lloyd's supplementary technical contract — LLM reference

**LLM reference / observed implementation record.** This document preserves the
technical facts needed to inspect or operate the four calculation workbooks. It
is not a second human procedure and does not provide missing methodology,
proxy, transformation, mapping, or rate approvals. The [operator runbook](runbook.md)
is the short human entry point; [handoff trace](handoff.md) records evidenced
lineage and unresolved external destinations.

## Scope and evidence

The received source workbook is `lloyds/source/Supplementary Info UKEU S33.xlsx`.
It contains `Weather`, `Quake`, and `EU exposure - weather & quake` tabs plus
27 event/location columns. It is source evidence, not a directly loadable
calculation input. It has no California county field, no CRESTA field for South
Africa or EU, and no separate EU earthquake population. The companion
provenance/instruction email is
`lloyds/source/RE RDS Supplementary Information - UKEU 33.msg`.

The checked-in SQL files are the three files under `lloyds/sql/`; the four
calculation workbooks are under `lloyds/workbooks/`. Lloyd's templates,
guidance, and the final approved submission are external. A structurally
matching S33 tab is not proof of an approved transformation or cached-data
lineage.

The saved message was received on 22 January 2026 and forwards instructions
sent on 9 January 2026 for the 1 January reporting date:

| Return section | Instructed source |
|---|---|
| RoW/global country-peril aggregates | `Weather`; proxy exposures where required |
| South Africa earthquake by CRESTA | `Quake` |
| California wildfire by county | Weather exposure, followed by review |
| Europe/Brussels earthquake and flood by CRESTA | `EU exposure - weather & quake` (not directly loadable) |
| Canada climate reporting | `Weather` |
| OFSI Canada earthquake | `Quake` |

The same email gives 2026 rates: `1 GBP = 1.35 USD`, `1 GBP = 1.15 EUR`, and
`1 GBP = 1.84 CAD`. It says wildfire is not monitored separately and that the
proxy/PML requires discussion. No proxy may be silently selected or reused.

The S33 shared formula is:

```text
HIS net QS = Share Insured Value USD * (1 - RI Cession PC / 100)
```

`RI Cession PC = 50` therefore means 50%, not a decimal multiplier of 50.

## Branch schemas and workbook mechanics

### RoW / country-peril

Workbook: `lloyds/workbooks/UKEU - Supplementary Info - RDL - Jan26 - Workings - ROW.xlsx`.
Purpose: country/peril exposure totals on `3. RoW Exposure Monitoring` for
reviewed transfer to the Lloyd's template. It contains `UKEU Exposure scale
factors`, four peril-specific extracts, a checked-in SQL text sheet, and the
report sheet. Exact input sheets are:

- `EQ Extract - Open Market`
- `FR Extract  - Open Market` (two spaces before the hyphen)
- `FL Extract - Open Market`
- `WS Extract - Open Market`

Each extract expects SQL-shaped columns A:K: portfolio, reclassification,
country code, country, account IDs, currency, and gross/net TSI fields. Column
L is the approved row scale factor. Column M is the scaled exposure consumed by
pivot/report logic. The current M formula is `TSI_NET` (column I) multiplied by
L, despite the header `TSI_USD_Scaled`; the report is labelled USD while this
uses source-currency net. USD-net is column K.

Populated input rows end at 4,988, matching the four pivot sources
`A1:M4988`. A larger load is omitted unless those ranges change. Helper
formulas extend beyond the inputs: EQ M to row 5,679, FR M to 5,676, and FL
L:M to 5,676. FL rows 4,989–5,676 contain 688 `#N/A` values in each helper
column. Current pivots exclude them; expanding ranges without reviewing stale
helpers can introduce errors. Review these rows under the approved range-change
procedure rather than blindly preserving or copying them.

The scale-factor sheet contains only a note, not an approved mapping. Cached
country totals are identical across the four perils and require proxy approval.

Observed loading controls: clear only old A:K source rows below row 1; preserve
headers, L:M, formulas and pivots; paste in row-1 header order; populate the
approved L factor for each row and fill M through the full source range; inspect
connections and each pivot source; resize/replace fixed ranges to exactly the
new rows; refresh only approved pivots, never **Data > Refresh All** against
stale links; reconcile every country/peril report total to its refreshed pivot.

The checked-in RoW SQL is not a complete four-peril producer: it is fixed to
`PERIL = 3` and `POLICYTYPE = 3`, while the workbook requires distinct EQ, FR,
FL, and WS inputs. Do not reuse one result across all four sheets. Retain the
exact query or parameter changes for each extract. Stop until source column,
unit, scale-factor derivation, four-peril producer, and dynamic/fixed range
maintenance are approved.

### South Africa earthquake

Workbook: `lloyds/workbooks/UKEU - Supplementary Info - Workings - South Africa EQ - Jan 2026.xlsx`.
Purpose: South Africa earthquake by two-digit CRESTA zone on `05 South Africa EQ Aggs`.
`SouthAfrica_Aggs.sql` returns the 18 source columns expected by `Core data!A:R`.
It filters the named January 2026 EDM to `PERIL = 1`, `POLICYTYPE = 1`, South
Africa, and portfolios matching S33/3624.

Column S holds the row scale factor, T calculates scaled TSI, and U derives a
two-digit zone from `Zone3Name`. The report aggregates with `SUMIF`. Current T
is gross source-currency `TSI` (column O) × S, although the report is labelled
USD. Blank/space zones do not match a report row and disappear. Current source
rows fit within the row-53 `SUMIF` range; a larger load requires fixed ranges
to be extended.

Observed loading controls: select an approved SQL or transformation producer
(the S33 `Quake` tab lacks required CRESTA/schema fields); if SQL, verify the
database named on line 1 and run in the approved SQL client; retain server,
EDM, codes, row count, and source total; review `AUDIT_SUMMARY`, `Cat Class Mapping`,
`Notes`, and `Fx`; clear only `Core data!A:R` below row 1; paste all 18 columns
in existing order; confirm S and fill T:U through every row; press
**Ctrl+Alt+F9**; reconcile report total plus quarantined unmapped-zone total to
the approved core measure.

Stop until the owner selects gross/net and currency measure, unmapped-zone
amounts are quarantined/reconciled, range maintenance is approved, and the
January 2026 workbook/report/FX labels are confirmed for the current cycle.
Structural SQL-to-sheet matching does not prove cached-row lineage.

### California wildfire

Workbook: `lloyds/workbooks/UKEU - Supplementary Info - RDL - Jan26 - Workings - California WF.xlsx`.
Purpose: California wildfire by county on `06 California Wildfire Aggs`.
`FA_California_Aggs.sql` returns the 13 columns expected in `Core data!A:M`,
ending in `TSI_USD_NET`. Helper column N removes the word `County` from the
source name; the report sums column M by that normalised county.

Current cached arithmetic reconciles, but execution is blocked by the owner
wildfire source/proxy decision and a report-date mismatch. The S33 workbook
cannot supply county; do not infer it. Obtain approval for the wildfire source
and proxy/PML; if SQL is selected, verify the database named in
`FA_California_Aggs.sql`, run in the approved SQL client, and retain server,
EDM, codes, row count, and source total. Review `AUDIT_SUMMARY`; clear only
`Core data!A:M` below row 1; preserve N/report formulas; paste 13 columns in
header order; fill N through every row and inspect blanks/errors from unexpected
county text; press **Ctrl+Alt+F9**; reconcile `06 California Wildfire Aggs` to
`Core data!M:M`.

Stop until proxy/PML approval, source lineage, and report date are resolved.
Schema match and cached arithmetic alone do not establish approval.

### EU EQ / FL CRESTA

Workbook: `lloyds/workbooks/UKEU - Supplementary Info - RDL - Jan26 - Workings - EU Cresta.xlsx`.
Purpose: separate European earthquake and flood totals by CRESTA on
`11 LIC EU CRESTA`. It contains `Core data EQ`, `Core data FL`, `Cat Class Mapping`,
`Notes`, and `Fx`. Both core sheets expect 18 source columns A:R. Column S is
the row scale factor; T calculates scaled USD exposure; U applies `Fx!C7` to
produce EUR used by the CRESTA report. The report uses whole-column `SUMIFS`,
so formula coverage—not a fixed report range—is the load control.

The received EU tab is not directly loadable. Prepare separately approved EQ
and FL extracts from an approved transformation (or another documented
producer); no matching SQL or Python producer is checked in. Retain producer,
date, peril, row count, source total, currency basis, and FX for both. Review
`AUDIT_SUMMARY`, `Cat Class Mapping`, `Notes`, and `Fx`; clear only A:R below row
1 on both core sheets; preserve S:U/report formulas; paste each 18-column
extract in existing order.

EQ T uses USD-net × S. Populated FL T formulas inconsistently use source
`TSI_NET` (P) or USD-net (R), then U = T × `Fx!C7`; do not fill down the current
flood formulas. After owner approval of one formula pattern, confirm S and fill
T:U through every row on both sheets, audit that no populated formula departs
from the pattern, press **Ctrl+Alt+F9**, and reconcile each peril report total
to its core sheet.

Populated FL inputs end at row 7,891, but T:U formulas continue to row 8,699
with cached zeros on blank source rows. Include this stale tail in the
approved formula/range review; worksheet dimensions are not input-row counts.

`Fx!C7` is `1.25 / 1.21 = 1.0330578512`, not the email's GBP/EUR 1.15 rate.
It may be an intentional cross-rate or stale logic; do not silently replace it.
Stop until formula, base currency, rate direction/effective date, report date,
formula coverage, and unmapped CRESTA treatment are approved.

## SQL and transformation controls

Select exactly one approved branch and retain its evidence:

```text
SQL branch: exact approved query/version, parameters, snapshot, schema, headers
Transformation branch: approved producer, mapping versions, grouping keys,
                      source-to-output reconciliation, exception treatment
```

The checked-in SQL joins policy via `ACCGRPID`; policy/portfolio multiplicity
may multiply coverage before aggregation. It multiplies `VALUEAMT` by
`blanlimamt` when nonzero; prove this is an approved dimensionless factor, not
a monetary limit. It reads FX dynamically, uses broad portfolio
`LIKE '%33%' OR LIKE '%3624%'`, and current `_QS`/`_SRP` `LIKE` patterns use `_`
as a wildcard. Before use, validate:

1. source row/TIV totals before and after each policy/portfolio join;
2. one approved policy grain and allowed portfolio list;
3. literal suffix/retention matching and decimal-rate precision;
4. frozen FX snapshot, source/target currency, and unit; and
5. output headers, row count, and total against target workbook schema.

## Reconciliation and diagnostic hard stops

For each peril/report define the eligible predicate and enforce:

```text
included report total + approved excluded/unmapped total = approved core total
```

Record grouping key, key normalisation, report/range end row, source and target
units/currency, rate, scale factor, expected class allocation, and absolute and
relative tolerance. Hard-stop on missing county/CRESTA/peril/classification,
unmatched report key, mixed formula pattern, stale link, `#REF!`, absent formula
coverage, or identical cross-peril fingerprint without proxy approval.

Establish whether each core/extract tab came from S33, a documented SQL run, or
another source. Confirm as-of date, portfolio scope, gross/net basis, units,
currency, FX, and scale-factor derivation; reconcile after refresh/recalculation.
Use one controlled, access-restricted working copy per run and writer. Retain
input/output hashes and provenance; never commit regulated extracts.

## Controlled external handoff record

For every transferred value retain source workbook/tab or saved SQL result,
calculation workbook and report cell/range, mapping/scale-factor/FX versions,
destination template and approved mapped cell, value/basis/unit/currency/as-of date,
preparer, reviewer, review date, and approval identifier. Do not overwrite
formulas, validation, template structure, or non-input cells without an
explicitly approved controlled template change. No external input-cell colour
map is supplied by this repository.

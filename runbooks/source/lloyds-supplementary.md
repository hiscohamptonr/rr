# Lloyd's supplementary information

## Summary

- **Sources:** S33 source workbook/email plus approved California, South Africa, RoW, and EU extracts.
- **Calculation:** four workbooks under `lloyds/`.
- **Final workbook/output:** RoW, South Africa, California, and EU report sheets; the final RDS template is external.
- **Time estimate:** 1 day.

## Data sources

- Received source workbook: `lloyds/source/Supplementary Info UKEU S33.xlsx`, with `Weather`, `Quake`, and `EU exposure - weather & quake` tabs.
- Companion instruction/provenance email: `lloyds/source/RE RDS Supplementary Information - UKEU 33.msg`.
- Checked-in SQL: the three query files under `lloyds/sql/`.
- Calculation workbooks: the four `.xlsx` files under `lloyds/workbooks/`.
- Lloyd's templates, guidance, and final approved submission: held outside this repository.

For exact observed workbook formulas, schemas, range limits, and validation
gates, see [lloyds-supplementary-for-llm.md](lloyds-supplementary-for-llm.md).
It records current implementation defects as well as mechanics; it is not an
approved reporting methodology.

See the repository [calculation discrepancy register](../../docs/calculation-discrepancies.md)
for the exact evidence and owner decisions.

## Instructions from the 2026 email

The email dated 22 January 2026 gives the following source instructions:

| Return section | Instructed source |
|---|---|
| RoW/global country-peril aggregates | `Weather`; use proxy exposures where required |
| South Africa earthquake by CRESTA | `Quake` |
| California wildfire by county | Weather exposure, followed by review |
| Europe/Brussels earthquake and flood by CRESTA | `EU exposure - weather & quake` (not directly loadable) |
| Canada climate reporting | `Weather` |
| OFSI Canada earthquake | `Quake` |

The same email sets 2026 Lloyd's rates to `1 GBP = 1.35 USD`, `1 GBP = 1.15 EUR`, and `1 GBP = 1.84 CAD`.

The email also says wildfire is not monitored separately and the proxy/PML requires discussion. Do not silently choose a proxy or reuse another peril without owner approval.

## Rest of World

**Workbook:** `lloyds/workbooks/UKEU - Supplementary Info - RDL - Jan26 - Workings - ROW.xlsx`

**Purpose:** produce country/peril exposure totals on `3. RoW Exposure Monitoring` for reviewed transfer to the Lloyd's template.

### Current blocker

Do not use the current RoW report for a USD handoff until the owner approves
the source column and report unit. Its column M formula is `TSI_NET * scale
factor` (source currency), while the report is labelled USD; the USD-net column
is K. The current sources end at row 4,988, exactly matching the four pivot
sources, but a larger future load would be omitted unless those fixed ranges
are changed. The scale-factor sheet contains only a note, not an approved mapping.
The identical cached country totals across the four perils also require explicit
proxy approval. The procedure below is therefore a loading/review procedure,
not approval to produce a final return.

The workbook contains `UKEU Exposure scale factors`, four peril-specific extract sheets, a checked-in SQL text sheet, and the final report sheet. The four input sheets are:

- `EQ Extract - Open Market`
- `FR Extract  - Open Market` (the workbook contains two spaces before the hyphen)
- `FL Extract - Open Market`
- `WS Extract - Open Market`

Each extract sheet expects the same SQL-shaped columns in A:K: portfolio, reclassification, country code, country, account IDs, currency, and gross/net TSI fields. Column L holds the approved row scale factor. Column M calculates the scaled exposure used by the sheet's pivot and report logic.

### Procedure

1. Confirm the reporting date, portfolio scope, currency basis, and approved peril/policy code for each of EQ, FR, FL, and WS.
2. Run and retain a separate approved extract for every sheet. Record the server, EDM, query file/version, peril code, policy type, row count, and total for each result.
3. Open the RoW workbook and review `AUDIT_SUMMARY` and `UKEU Exposure scale factors` before replacing data.
4. On each extract sheet, clear only the old source rows in A:K below row 1. Do not clear the headers, scale factors, formulas, or pivots to the right.
5. Paste the matching extract into A:K, preserving the column order shown by row 1.
6. Populate or confirm the approved scale factor in column L for every pasted row, then fill the column M formula through the full source range.
7. Inspect connections and each pivot source first. Resize/replace every fixed
   source range to include exactly the new rows, then refresh only approved
   pivots; do not use **Data > Refresh All** against stale links.
8. Review `3. RoW Exposure Monitoring` by country and peril, then reconcile each report total to its refreshed extract pivot before handoff.

The checked-in RoW SQL is not a complete four-peril producer. It is fixed to `PERIL = 3` and `POLICYTYPE = 3`, while the workbook requires distinct EQ, FR, FL, and WS inputs. Do not reuse that one result across all four sheets. Preserve the exact query or parameter changes used for each extract.

The current column M formula multiplies `TSI_NET` by the row scale factor even
though its header says `TSI_USD_Scaled`. Stop until the approved calculation
states whether it uses source-currency `TSI_NET` or USD-net `TSI_USD_NET`, and
the report label and pivot measure agree. Do not rely on the header alone.

## South Africa earthquake

**Workbook:** `lloyds/workbooks/UKEU - Supplementary Info - Workings - South Africa EQ - Jan 2026.xlsx`

**Purpose:** produce South Africa earthquake exposure by two-digit CRESTA zone on `05 South Africa EQ Aggs`.

`SouthAfrica_Aggs.sql` returns the 18 source columns expected in `Core data!A:R`. It filters the named January 2026 EDM to `PERIL = 1`, `POLICYTYPE = 1`, South Africa, and portfolios matching S33/3624. In the workbook, column S holds the row scale factor, column T calculates scaled TSI, and column U derives the two-digit zone from `Zone3Name`. The report aggregates those results with `SUMIF`.

### Current blocker

The report is labelled USD but column T currently calculates gross source
currency `TSI * scale factor`, not net USD. Blank/space zones do not match a
report row and are omitted. The current source ends within the row-53 `SUMIF`
range, but a larger future load requires those fixed ranges to be extended.
Stop until an owner selects the gross/net and currency measure, unmapped-zone
amounts are quarantined/reconciled, and the range maintenance procedure is
approved.

### Procedure

1. Select an approved SQL or transformation producer. The S33 `Quake` tab is not directly loadable because it lacks required CRESTA/schema fields; retain evidence of the selected producer.
2. If SQL is used, verify the database named on line 1, run it in the approved SQL client, and record the server, EDM, codes, row count, and source total.
3. Open the South Africa workbook and review `AUDIT_SUMMARY`, `Cat Class Mapping`, `Notes`, and `Fx` before loading data.
4. Clear only the old source rows in `Core data!A:R` below row 1. Preserve columns S:U and all report formulas.
5. Paste the 18 source columns into `Core data!A:R` in the existing header order.
6. Populate or confirm the scale factor in column S, then fill formulas in T:U through every pasted row.
7. Use **Ctrl+Alt+F9** to force a full recalculation.
8. Review `05 South Africa EQ Aggs` and reconcile `report total + quarantined
   unmapped-zone total` to the approved core measure before handoff.

The workbook is labelled January 2026, but its report and FX labels require confirmation against the current cycle. The SQL-to-sheet match is structural; the workbook contains no run record proving that its cached rows came from the current SQL. Confirm the date, FX, units, and lineage before use.

## California wildfire

**Workbook:** `lloyds/workbooks/UKEU - Supplementary Info - RDL - Jan26 - Workings - California WF.xlsx`

**Purpose:** produce California wildfire exposure by county on `06 California Wildfire Aggs`.

`FA_California_Aggs.sql` returns the 13 columns expected in `Core data!A:M`, ending in `TSI_USD_NET`. It filters the named January 2026 EDM to `PERIL = 4`, `POLICYTYPE = 4`, California, and portfolios matching S33/3624. Helper column N removes the word `County` from the source name, and the report sums column M by the normalized county.

The current cached arithmetic reconciles, but execution remains blocked until
the owner approves the wildfire source/proxy and resolves the report-date
mismatch. Do not derive a county from the S33 workbook: it does not contain the
required county field.

### Procedure

1. Obtain owner approval for the wildfire exposure source and proxy/PML decision described in the January email.
2. If SQL is approved, verify the database named in `FA_California_Aggs.sql`, run it in the approved SQL client, and record the server, EDM, codes, row count, and source total.
3. Open the California workbook and review `AUDIT_SUMMARY` before loading data.
4. Clear only the old source rows in `Core data!A:M` below row 1. Preserve helper column N and all report formulas.
5. Paste the 13 SQL-shaped columns into `Core data!A:M` in the existing header order.
6. Fill the county formula in column N through every pasted row and review blanks/errors caused by unexpected county text.
7. Use **Ctrl+Alt+F9** to force a full recalculation.
8. Review `06 California Wildfire Aggs` and reconcile its county total to `Core data!M:M` before handoff.

The report date does not match the January 2026 SQL source. The schema match does not prove cached-data lineage. Resolve the date and retain the proxy approval before the result is used.

## EU CRESTA

**Workbook:** `lloyds/workbooks/UKEU - Supplementary Info - RDL - Jan26 - Workings - EU Cresta.xlsx`

**Purpose:** produce separate European earthquake and flood exposure totals by CRESTA on `11 LIC EU CRESTA`.

The workbook contains `Core data EQ`, `Core data FL`, `Cat Class Mapping`, `Notes`, and `Fx`. Both core sheets expect source columns A:R. Column S holds the row scale factor, column T calculates scaled USD exposure, and column U applies `Fx!C7` to produce the EUR amount used by the report's CRESTA aggregation.

### Current blocker

Do not execute the EU procedure as a EUR calculation. The populated flood T
formulas inconsistently reference source `TSI_NET` and USD-net columns, so the
aggregate mixes currencies before applying `Fx!C7`. That rate is not the email's
GBP/EUR 1.15 rate. An owner must approve one uniform source column, rate
direction/effective date, every T/U formula, and treatment of unmapped CRESTA
values before output is used. The report uses whole-column `SUMIFS`; formula
coverage—not a fixed report range—is the load control.

### Procedure

1. Prepare and retain separately approved earthquake and flood extracts from an approved transformation of `EU exposure - weather & quake` or another documented source. The received tab is not directly loadable.
2. Record the producer, reporting date, peril, row count, source total, currency basis, and FX for both extracts. There is no matching SQL or Python producer checked in.
3. Open the EU workbook and review `AUDIT_SUMMARY`, `Cat Class Mapping`, `Notes`, and `Fx` before loading data.
4. Clear only the old source rows in A:R below row 1 on `Core data EQ` and `Core data FL`. Preserve columns S:U and all report formulas.
5. Paste the matching 18-column extract into each sheet in the existing header order.
6. After the owner has supplied the approved formula pattern, populate or
   confirm the scale factor in column S and fill formulas in T:U through every
   pasted row on both sheets. Audit that no populated formula departs from that
   pattern; do not fill down the current flood formulas.
7. Use **Ctrl+Alt+F9** to force a full recalculation.
8. Review earthquake and flood results on `11 LIC EU CRESTA` and reconcile each peril total to its core sheet before handoff.

The report date does not match the January 2026 cycle. `Fx!C7` is `1.25 / 1.21 = 1.0330578512`, which is not the email's 2026 EUR rate of `1.15`. Confirm whether `Fx!C7` is an intentional cross-rate or stale logic before using the output.

## Received S33 workbook

`Supplementary Info UKEU S33.xlsx` is source evidence rather than a final return
template. Its EU tab is named `EU exposure - weather & quake`, not `EU exposure
- S33`. Its 27-column event/location tabs do not supply the SQL-shaped
portfolio, county, CRESTA, or separate EU earthquake/flood fields required by
the calculation workbooks. Do not paste it directly or infer those fields; use
an approved transformation producer. Its shared formula calculates:

```text
HIS net QS = Share Insured Value USD * (1 - RI Cession PC / 100)
```

Keep the workbook and companion message together to preserve source instructions and provenance.

## Mandatory checks

- Establish whether each current core/extract tab came from the received S33 workbook, a documented SQL run, or another source; matching columns alone do not prove lineage.
- Record the exact peril/policy codes and scale-factor derivation for every RoW extract.
- Resolve the California wildfire proxy/PML decision with the owner.
- Resolve the non-current dates in the South Africa, California, and EU workbooks.
- Confirm units, gross/net basis, currency, FX, as-of date, and portfolio scope before any template handoff.
- Reconcile each final report total to its source/core data after refresh or recalculation.

## Controlled handoff

For every value transferred to the external Lloyd's template, record:

- source workbook/tab or saved SQL result;
- calculation workbook and report cell/range;
- mapping, scale-factor, and FX versions;
- destination template and green cell;
- value, unit, currency, and as-of date;
- preparer, reviewer, and review date.

Do not overwrite formulas, validation, template structure, or non-green cells unless a controlled template change is explicitly approved.

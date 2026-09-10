# Lloyd's supplementary information

[Start here](../../README.md) · [Run checklist](../operating-controls.md) ·
[Detailed LLM reference](technical-contract.md)

**Result:** four calculation reports for transfer to a separate Lloyd's/RDS
template. The approved final template and destination-cell map are not supplied.
Each branch also has unresolved calculation decisions, listed below.

## 1. Get the source pack

Keep these together:

- `lloyds/source/Supplementary Info UKEU S33.xlsx`
- `lloyds/source/RE RDS Supplementary Information - UKEU 33.msg`

The S33 tabs are **source evidence, not ready-to-paste extracts**. Use an
approved SQL query or transformation with the fields each workbook needs.
Complete the [run checklist](../operating-controls.md) before loading data.

## 2. Prepare each branch

All calculation workbooks below are in `lloyds/workbooks/`. Work on copies.
Paste data **without headers**, starting at row 2; preserve helper/formula columns.

### Rest of World — country/peril

Workbook: `UKEU - Supplementary Info - RDL - Jan26 - Workings - ROW.xlsx`

- Source: S33 `Weather` evidence plus four approved peril extracts/transformations.
- Load A:K on `EQ Extract - Open Market`, `FR Extract  - Open Market`
  (two spaces before the hyphen), `FL Extract - Open Market` and `WS Extract - Open Market`.
- Preserve scale L and formula M. Report: `3. RoW Exposure Monitoring`.
  Review stale helper rows too: the flood sheet has `#N/A` below the current inputs.
- **Stop:** approve the source measure/currency, scale factors and pivot ranges.
  The checked-in SQL is fixed to `3/3`; do not reuse it unchanged for all perils.

### South Africa — earthquake CRESTA

Workbook: `UKEU - Supplementary Info - Workings - South Africa EQ - Jan 2026.xlsx`

- Source: approved `lloyds/sql/SouthAfrica_Aggs.sql` or transformation; S33 `Quake`
  lacks the required CRESTA fields.
- Load `Core data!A:R`; preserve scale S and formulas T:U.
- Report: `05 South Africa EQ Aggs`.
- **Stop:** approve gross/net and currency basis, report date, range maintenance
  and treatment of blank/unmapped CRESTA zones.

### California — wildfire county

Workbook: `UKEU - Supplementary Info - RDL - Jan26 - Workings - California WF.xlsx`

- Source: owner-approved wildfire exposure/proxy. If using SQL, approve
  `lloyds/sql/FA_California_Aggs.sql`; do not invent county from S33.
- Load `Core data!A:M`; preserve helper N.
- Report: `06 California Wildfire Aggs`.
- **Stop:** approve the wildfire proxy/PML and resolve the report-date mismatch.

### Europe — earthquake/flood CRESTA

Workbook: `UKEU - Supplementary Info - RDL - Jan26 - Workings - EU Cresta.xlsx`

- Source: separately approved EQ and FL extracts. S33 `EU exposure - weather & quake`
  needs a transformation; no matching producer is checked in.
- Load A:R on `Core data EQ` and `Core data FL`; preserve scale S and formulas T:U.
- Report: `11 LIC EU CRESTA`.
- **Stop:** approve uniform formulas, FX direction/date and unmapped-zone treatment.
  **Do not fill down the current flood formulas:** they mix source and USD amounts.

## 3. Load, recalculate and check

Once the relevant stops are resolved:

1. Review `AUDIT_SUMMARY`, mappings, FX, formulas and links in each working copy.
2. Check extract headers/order. Replace old input rows only; extend approved
   helpers/formulas and source ranges to all new rows, leaving no stale data.
3. Refresh approved pivots only and recalculate in Excel. Do not blindly update external links.
4. Reconcile each report plus approved exclusions to its source total.
   Investigate missing geography, formula errors and unexplained differences.

## 4. Transfer and review

Use an approved report-range-to-final-cell map—not cell colour or label matching.
Log transfers and obtain reviewer sign-off using the run checklist.

For formulas and detailed checks, use the [technical reference](technical-contract.md).
For decisions and missing final mappings, see [LLOYDS-01–03](../decisions.md#lloyds-01)
and the [handoff trace](handoff.md).

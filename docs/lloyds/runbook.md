# Lloyd's supplementary — SQL and Excel

## Start here

1. Open working copies of the required calculation workbooks in `lloyds/workbooks/`.
2. Keep `lloyds/source/Supplementary Info UKEU S33.xlsx` and its accompanying `.msg` correspondence as source evidence, not ready-to-paste extracts.
3. Obtain the matching extract for each branch below and check its headers against the workbook before loading it.
4. Clear old input rows only and paste **data without headers from row 2**, preserving the existing headers, scale factors, formulas and report areas.

## Rest of World — country and peril

Workbook: `UKEU - Supplementary Info - RDL - Jan26 - Workings - ROW.xlsx`

1. Obtain separate EQ, FR, FL and WS extracts using the S33 Weather evidence and confirmed transformations; the checked-in `lloyds/sql/Supplementary Info - Workings - ROW Aggs - SQL.sql` is fixed to `3/3`, not all four perils.
2. Paste A:K from row 2 into `EQ Extract - Open Market`, `FR Extract  - Open Market`, `FL Extract - Open Market` and `WS Extract - Open Market`, respectively (FR has two spaces before the hyphen).
3. Preserve scale column L, extend the correct formulas in M and remove stale input/helper rows, including the flood sheet's old `#N/A` rows.
4. Confirm the measure, currency, scales and pivot ranges before refreshing the report `3. RoW Exposure Monitoring`.

## South Africa — earthquake CRESTA

Workbook: `UKEU - Supplementary Info - Workings - South Africa EQ - Jan 2026.xlsx`

1. Run the confirmed `lloyds/sql/SouthAfrica_Aggs.sql` extraction or matching transformation; the S33 Quake tab alone lacks the required CRESTA fields.
2. Paste into `Core data!A2`, filling A:R only, preserve scale column S and extend the correct formulas in T:U.
3. Confirm gross/net treatment, currency, report date, source ranges and blank/unmapped CRESTA treatment before refreshing `05 South Africa EQ Aggs`.

## California — wildfire county

Workbook: `UKEU - Supplementary Info - RDL - Jan26 - Workings - California WF.xlsx`

1. Confirm the wildfire exposure/proxy and PML before using `lloyds/sql/FA_California_Aggs.sql`; do not invent county data from S33.
2. Paste into `Core data!A2`, filling A:M only, and preserve helper column N.
3. Resolve the report-date mismatch before reviewing `06 California Wildfire Aggs`.

## Europe — earthquake and flood CRESTA

Workbook: `UKEU - Supplementary Info - RDL - Jan26 - Workings - EU Cresta.xlsx`

1. Obtain separately confirmed EQ and FL extracts; the S33 `EU exposure - weather & quake` tab needs a transformation and no matching producer is checked in.
2. Paste into `Core data EQ!A2` and `Core data FL!A2`, filling A:R only and preserving scale S and formulas T:U.
3. Resolve the mixed source/USD flood formulas before filling down, and confirm FX direction/date and unmapped-zone treatment before reviewing `11 LIC EU CRESTA`.

## Finish each branch

1. Extend only confirmed formulas and source ranges through the new data, refresh the relevant pivots and recalculate in Excel without blindly updating external links.
2. Reconcile report totals and agreed exclusions to the extract and resolve formula errors, missing geography and unexplained differences.
3. Save the workbook, extract and reconciliation together; transfer values only when the final template and destination cells have been agreed.

**To return to later:** obtain the final Lloyd's/RDS template and agreed destination cells; these are calculation reports, not completed submission forms.

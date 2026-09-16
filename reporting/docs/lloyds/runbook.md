# Lloyd's — quick steps

Use working copies from `lloyds/workbooks/`; match the filename endings below.
Clear old input rows first, paste **without headers from row 2**, and keep formulas and scale factors intact.

## South Africa

1. Run `lloyds/sql/SouthAfrica_Aggs.sql` and export the results.
2. In the workbook ending `South Africa EQ - Jan 2026.xlsx`, paste into `Core data!A2` (A:R), preserve S and fill the correct T:U formulas down.
3. Refresh `05 South Africa EQ Aggs` and check its totals against the export.

## California

1. Confirm the wildfire proxy/PML, then run `lloyds/sql/FA_California_Aggs.sql` and export the results.
2. In the workbook ending `California WF.xlsx`, paste into `Core data!A2` (A:M), preserving N.
3. Check the report date and totals on `06 California Wildfire Aggs`.

## Rest of World

1. Obtain separate EQ, FR, FL and WS extracts; the existing ROW SQL is fixed to `3/3`, not all four perils.
2. In the workbook ending `ROW.xlsx`, paste A:K into the matching `EQ`, `FR`, `FL` and `WS Extract - Open Market` sheets from A2, preserve L and fill the correct M formulas down.
3. Update the pivot ranges, refresh `3. RoW Exposure Monitoring` and check totals.

## Europe

1. Obtain separate earthquake and flood extracts; no matching producer is supplied yet.
2. In the workbook ending `EU Cresta.xlsx`, paste A:R into `Core data EQ!A2` and `Core data FL!A2`, preserving S:U.
3. Correct the mixed source/USD flood formulas before filling down or refreshing `11 LIC EU CRESTA`.

## Finish

1. Check currency, units, scales, dates, missing geography and formula errors; do not blindly refresh external links.
2. Reconcile each report and agreed exclusions to its extract, then save the workbook and CSV together.

**Still needed:** the final Lloyd's submission template and destination cells.

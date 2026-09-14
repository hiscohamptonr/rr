# PRA — SQL and Excel

## Earthquake

1. Run `pra/sql/pra-earthquake.sql` against the correct EDM database with `@peril = 2` and `@policy_type = 2`.
2. Export the results as a CSV with these headers: `pml, state, userid1, cntrycode, uwritrname`.
3. Open a working copy of `pra/workbooks/PRA_Aggs.xlsx` and select `pivot_eq`.
4. Clear the old data in A:E below row 1, leaving formulas F:M and the report areas untouched.
5. Paste the CSV contents **with headers into A1**, filling A:E only.
6. Use **Table Design → Resize Table** to extend `Table32` from A1 through column M to the last pasted row.
7. Select F2:M through the last pasted row and press **Ctrl+D** to fill the correct first-row formulas down.
8. Check that the input row count and column A total match the SQL results, and resolve any formula errors.
9. Click each earthquake PivotTable, choose **PivotTable Analyze → Change Data Source**, and set it to **`Table32`**, not `Table3`.
10. Confirm the pivot value field and currency, then right-click each earthquake PivotTable and select **Refresh**—not Refresh All.
11. Check the pivot totals against the corresponding input totals and save the workbook with the CSV.

## All-peril

Use `pivot_allperil` and `Table3` only with a separately confirmed all-peril export; follow the same paste, formula-fill and total checks.
Do not copy the earthquake results into this sheet or guess the all-peril query codes.

**To return to later:** find the final PRA submission template; this workbook contains the calculated aggregates, not the submission form.

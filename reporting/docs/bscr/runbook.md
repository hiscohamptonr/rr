# BSCR runbook

[Population workbook](../../bscr/workbooks/BSCR_Auto_Population.xlsx) · [Reconciliation workbook](../../bscr/reconcile/results/BSCR_Reconciliation.xlsx) · [Reconciliation notes](reconciliation.md)

## 1. Get and run the SQL

Open [bscr-output.sql](../../bscr/sql/bscr-output.sql) in your SQL client and select
the approved EDM snapshot. Leave `@bscr_entity = NULL` for all entities and check
the FX and retention parameters. Run the complete script.

The result has eight columns:

`cntrycode, bscr_entity, region, sum_pml, sum_net, count_policies, is_geocoded, peril_id`

Amounts are **full USD**, with FX already applied. Use the current script—not
the legacy comparison query.

## 2. Populate the workbook

Open [BSCR_Auto_Population.xlsx](../../bscr/workbooks/BSCR_Auto_Population.xlsx).

1. Clear the old data on **SQL input**, keeping the headers and table.
2. Paste the new eight-column results below the headers. The entity tabs populate automatically.

Do not leave stale rows below a shorter replacement. Use **Calculate Now** if
Excel does not refresh. No Python or macros are required.

## 3. Review and save

- Review the **33, 3624, HIC, HIG and HSA** tabs.
- Green cells are automatic; complete the blue manual fields, including premiums and EP losses.
- Money is displayed in USD millions. **Do not apply FX again.**
- Geocoded means modelled/modellable; ungeocoded means not modelled/not modellable. Non-US is total minus US.
- `ALL` is earthquake only. Do not add overlapping regional totals together.
- Resolve unmapped entities; counts are grouped rows, not verified distinct contracts.

Save the workbook with the SQL results and source/parameter record. Review before submission.

The preloaded data are the 737 uploaded rows from
[bscr_output_wseq.csv](../../bscr/reconcile/bscr_output_wseq.csv), not a live database connection.
Historical comparisons are kept in the [separate reconciliation](reconciliation.md).

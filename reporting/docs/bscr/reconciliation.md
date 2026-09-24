# BSCR reconciliation

[Reconciliation workbook](../../bscr/reconcile/results/BSCR_Reconciliation.xlsx) · [Operating runbook](runbook.md)

**What we tested:** templates → old saved output → legacy query → corrected query → new saved output.

## 1. Match the historical templates

We used **33's original** and **3624/HIC/HIG/HSA v2** files in
[filled in templates](../../bscr/reconcile/filled%20in%20templates/).
All **528 populated count/exposure cells tested in Schedule X(f)** match the
[old saved CSV](../../bscr/output/bscr-output.csv), with appropriate scaling.

**Currency finding:** the templates contain pre-FX amounts divided by 1,000,
despite USD headings. The later workings' **1.35 conversion was missing**.
Currency conversion and million scaling are separate steps; counts need neither.

For HIC L12: **121,743,087.31 saved → ×1.35 → 164,353,167.87 USD at the same scale → ÷1,000 → 164,353.168 USD million**.

The later April templates match the historical total counts and all **46 populated
regional gross/net limits** after conversion. Their rounded totals and manual
classification splits can differ. Premiums and EP losses were not reconciled.

## 2. Reproduce the old output

We replayed the [original Marimo calculation](../../bscr/old-process/BSCR_UKEU.py)
on the uploaded EDM data. **All 452 historical CSV rows reproduce**, with exact
counts and monetary differences below one cent.

[bscr-extract-legacy.sql](../../bscr/sql/bscr-extract-legacy.sql) preserves that
workflow, including the old geocode join, earthquake-only selection and
case-sensitive geography. It returns a full aggregate, normally converted to USD.

## 3. Isolate the geocoding correction

We changed **only the geocode join**, holding the other calculation rules fixed.
The old join could assign the same exposure to both geocode buckets. Correcting
it explains the entire earthquake `ALL` reduction across **184 accounts**:

| Entity | Old count | Corrected count | Gross change, USDm |
|---|---:|---:|---:|
| 33 | 5,341 | 5,121 | -3,515.320 |
| 3624 | 36 | 27 | -2.230 |
| HIC | 173,687 | 173,683 | -9.338 |
| HIG | 1,970 | 1,938 | -938.972 |
| HSA | 90,052 | 90,032 | -347.102 |
| **Total** | **271,086** | **270,801** | **-4,812.963** |

Net exposure falls by **USD 3,050.632m**. These are **285 fewer grouped rows**, not
285 policies deleted. Policy-ID grouping has no material effect on this snapshot.

## 4. Explain the other differences

- **Perils:** legacy uses earthquake throughout; current Europe, NA hurricane and Japan typhoon use wind.
- **US states:** original Python misses uppercase US state names in NA earthquake; current SQL matches them case-insensitively. Canada is included in both.
- **Workbooks:** February workings omitted US from NA hurricane; the old CSV and later March/April workbooks include it.
- **Extra views:** current `is_non_us` and `is_jp_eq` rows overlap existing exposure; do not add them to `ALL`.
- **Unmapped entity:** two current GB wind rows contain approximately USD 26.353bn gross/net without an entity assignment. They are outside earthquake `ALL`.

## 5. Reproduce the new output

[bscr-output.sql](../../bscr/sql/bscr-output.sql) reproduces all **737 rows** of
[bscr_output_wseq.csv](../../bscr/reconcile/bscr_output_wseq.csv): exact counts,
with every monetary difference below one cent.

The raw data are in `bscr/sql/edm-parquet/` as CSVs. Their account, policy,
location and coverage counts match the supplied source metadata. Comparisons
used the same snapshot and currency basis, without removing source records.

**Scope:** local replays checked against saved outputs—not live SQL Server tests
or proof of a historical submission. The reconciliation workbook records the
detailed checks; matching after conversion does not validate the original
currency labels, manual classifications or every policy-term assumption.

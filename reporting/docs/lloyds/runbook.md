---
Report: RDS
Time: 3d
---

# Lloyd's — RDS and supplementary reports

[Back to reporting guides](../../README.md)

## RDS events

### 1. Open the event list and reporting workbook

- [Event IDs](../../lloyds/rds/eventids_for_rds.xlsx) — which model events to extract.
- [RDS workbook](../../lloyds/rds/2026%20Lloyds%20RDS%20UKEU%20Retail.xlsx) — where the results go.

Choose the correct period: the workbook contains **`1.1.26 RDS Input`** and
**`1.4.2026 RDS Input`** tabs. Do not overwrite another period.

### 2. Extract the model losses

Use the approved reporting-period ELTs and portfolios/classes.

| Model | Selection key |
|---|---|
| Verisk / AIR / Touchstone | **Event AND Year** from the event list |
| RMS / Risklink | The corresponding RMS event ID |

Do not select AIR events by event number alone: numbers repeat across years.
For example, the Northeast Hurricane selection is **Event 1, Year 103**.
Confirm the event mapping applies to the model version being used.

**UK flood needs its selection supplied:** it is absent from the event-ID list,
and its model-ID cells in `EventDetails` are blank. The checked-in
`rds-event-select.sql` is also empty; it is not a runnable extraction query.

### 3. Apply the agreed model blend

Put model losses on the same class, financial-term and currency basis first.
Where a blend applies, use:

**Blended loss = Verisk weight × Verisk loss + Risklink weight × Risklink loss.**

The recorded EU windstorm approach is **100% Risklink**: use the Risklink loss.
For other perils, obtain the agreed weights; do not assume 50/50 or add both
models at full weight. The January 2026 notes say only EU windstorm and UK flood
were refreshed then—do not assume the other cached events are current.

### 4. Update and check the RDS rows

Match each result to **Event + Class** in the chosen `RDS Input` tab.
Enter losses under **Gross Loss**, check **Currency**, and keep **Aggregate**
(exposure) and **Gross Reinstatement Premium Recoveries** separate. Do not paste
losses into exposure columns or overwrite the scenario labels.

Check every required event/class, currency and blend against the source extracts.
Keep the extracts and weights with the completed working copy; obtain review
before submission.

## Supplementary exposure reports

Use working copies from [lloyds/workbooks/](../../lloyds/workbooks/).
SQL files are in [lloyds/sql/](../../lloyds/sql/). Confirm the database/report date
before running them: they contain fixed database, peril and portfolio settings.
Paste **data only below existing headers**, preserving helper columns.

| Report | Source | Paste into | Preserve / report |
|---|---|---|---|
| South Africa | `SouthAfrica_Aggs.sql` | South Africa EQ workbook, `Core data!A2` (A:R) | S:U; `05 South Africa EQ Aggs` |
| California | `FA_California_Aggs.sql` | California WF workbook, `Core data!A2` (A:M) | N; `06 California Wildfire Aggs` |
| Rest of World | Separate EQ, FR, FL and WS extracts | ROW workbook, matching extract sheet `A2` (A:K) | L:M; `3. RoW Exposure Monitoring` |
| Europe | Separate EQ and FL extracts | EU Cresta workbook, `Core data EQ!A2` / `Core data FL!A2` (A:R) | S:U; `11 LIC EU CRESTA` |

### Resolve these before using the reports

- **South Africa:** the SQL labels currency from `VALUECUR` but joins FX on
  `LIMITCUR`. Confirm the currency/scaling basis and unmapped CRESTA treatment.
- **California:** confirm the wildfire proxy and as-of date; the cached report
  says 2025 while the SQL database is January 2026.
- **ROW:** the supplied query selects only peril/policy type **3/3**, not four
  perils. Existing `M = I*L` uses source-currency net despite its USD label;
  USD-net is in K. Agree the measure before filling formulas.
- **Europe:** no producer query is supplied. Flood helpers mix source and USD
  measures, apply old FX and extend beyond the input rows. Resolve the formula
  and currency basis before refreshing.

For each report, clear stale input rows, check helper/pivot coverage and unmapped
geography, then reconcile totals before refreshing or transferring figures.
Detailed defects are in the [discrepancy register](../calculation-discrepancies.md#lloyds-supplementary-information).
Contingency/weather workbooks are a separate workflow, not covered here.

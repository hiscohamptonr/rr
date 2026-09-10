# Dataiku OED aggregation

[Start here](../../README.md) · [Run checklist](../operating-controls.md) ·
[Detailed LLM reference](current-technical-guide.md)

**Result:** provisional exposure totals from OED, split by peril and geography.
This is **not** the PRA, BSCR or Lloyd's return process, despite those output labels.

## 1. Confirm the inputs

Use `dataiku/Dataiku-Aggs.sql` in the approved Dataiku/Databricks SQL environment.
It selects OEDIDs **42 (UK)** and **44 (EU)** and reads:

- `prod_group_kairos_sandbox.dataiku.ukeu_validator_oed`
- `prod_group_kairos_sandbox.dataiku_temp.RETAILROLLUPDATA_map_lob_mapping_gc`
- `prod_group_kairos_sandbox.dataiku_temp.RETAILROLLUPDATA_map_fx_rates`

Confirm the snapshot, OED IDs, LOB mappings, FX, participation scale, Fine Art
cession, peril scope and geography rules with the owner before running.
Record the exact query revision and job/output location.

## 2. Run and choose the right output

Execute the query using your approved SQL job/client. There is no repository
CLI command for connecting to the warehouse.

| Output label | Available levels |
|---|---|
| `Aggs`, `Lloyds` | Country, US state and postcode |
| `PRA` | Country and US state |
| `BSCR` | Country, US state and overlapping regional views, including `ALL` |

`PRA_REGION`, `CRESTA` and `ACCOUNT` are not emitted. Only enabled EQ, FL, WS
and FR flags produce rows. **Choose one use case, level and peril before totaling**;
do not add overlapping views together.

## 3. Check before using totals

The query calculates TIV, then gross after deductibles/limits, then net after
participation and Fine Art retention. It also converts those measures to GBP.

- Reconcile detail to grouped totals at your chosen level.
- Review row/account/location counts and TIV, participation and LOB exceptions.
- Check every currency has a usable positive FX rate. **Zero/negative rates can
  leave GBP amounts null without increasing `InvalidFXRowCount`.** Check null
  converted amounts independently; zero exceptions do not prove complete conversion.
- Investigate missing geography or mappings before relying on the output.

Keep the query, source snapshot, output dataset, checks and reviewer sign-off.
The [FX decision](../decisions.md#dataiku-01) remains open.

For exact levels, grouping keys, formulas and controls, use the
[current technical guide](current-technical-guide.md). The
[historical contract](technical-contract.md) and [plan](historical-plan.md)
describe an earlier uncapped design, **not this query**.

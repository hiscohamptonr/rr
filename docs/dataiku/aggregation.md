# Dataiku — OED aggregation

## Run the query

1. Open `dataiku/Dataiku-Aggs.sql` in the approved Dataiku/Databricks SQL environment, not a SQL Server client.
2. Confirm the source snapshot and OED IDs (the query selects 42 for UK and 44 for EU), plus LOB mappings, FX, participation, Fine Art cession, peril and geography rules.
3. Check access to `prod_group_kairos_sandbox.dataiku.ukeu_validator_oed`, `prod_group_kairos_sandbox.dataiku_temp.RETAILROLLUPDATA_map_lob_mapping_gc` and `prod_group_kairos_sandbox.dataiku_temp.RETAILROLLUPDATA_map_fx_rates`.
4. Run the SQL using the approved job or client and retain the query revision and output dataset location.
5. Select **one use case, one level and one peril** before adding up results, using the available views below.
6. Reconcile detail to grouped totals and check row/account/location counts, TIV, participation and LOB exceptions.
7. Check that every currency has a positive, usable FX rate and investigate null GBP amounts independently of the exception count.
8. Resolve missing geography, mappings and unexplained differences, then retain the output and reconciliation together.

## Choose the output view

| Output label | Available levels |
|---|---|
| `Aggs`, `Lloyds` | Country, US state, postcode |
| `PRA` | Country, US state |
| `BSCR` | Country, US state, overlapping regional views including `ALL` |

Only enabled EQ, FL, WS and FR flags produce rows; `PRA_REGION`, `CRESTA` and `ACCOUNT` levels are not emitted.
Do not add overlapping views together.

**Stop if FX is missing, zero or negative:** GBP values can be null without increasing `InvalidFXRowCount`, so a zero exception count does not prove conversion is complete.

These are provisional exposure totals, not the PRA, BSCR or Lloyd's returns despite the output labels.

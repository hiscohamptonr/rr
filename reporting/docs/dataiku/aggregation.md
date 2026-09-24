# Dataiku — OED aggregation

## Run the query

1. Open `dataiku/Dataiku-Aggs.sql` in the approved Dataiku/Databricks SQL
   environment, not a SQL Server client. The repository contains no universal
   CLI, connection, or source-snapshot command.
2. Confirm the approved source snapshot and the query's selected OED metadata:
   OEDID `42` is labelled `UK` with participation scale `100.0`, and OEDID
   `44` is labelled `EU` with scale `1.0`. These checked-in values are not
   approval of the reporting-period inputs.
3. Confirm access and lineage for
   `prod_group_kairos_sandbox.dataiku.ukeu_validator_oed`,
   `prod_group_kairos_sandbox.dataiku_temp.RETAILROLLUPDATA_map_lob_mapping_gc`,
   and `prod_group_kairos_sandbox.dataiku_temp.RETAILROLLUPDATA_map_fx_rates`.
4. Review the SQL for the current policy-term precedence, peril flags and
   limits, participation scale, Fine Art cession, LOB mappings, FX basis, and
   country-based geography rules. Confirm those assumptions with the
   responsible owners; labels such as `PRA` and `BSCR` do not make the
   result an approved return.
5. Record the exact query revision, environment/job identity, source snapshot,
   parameters, and complete output dataset location. No repository artifact
   proves that the checked-in query has executed successfully.
6. Select **one use case, one level, and one `PerilCode`** before adding
   results. Reconcile source/detail to grouped totals and check source rows,
   distinct accounts/locations, TIV, gross/net measures, participation,
   retention, LOB and FX exception counts.
7. Check that every currency has one positive usable distinct FX rate; duplicate
   records are acceptable only when the parsed rate is identical. Investigate
   null GBP measures independently of the exception count.
8. Resolve missing geography, mappings, invalid TIV/participation, and
   unexplained differences, then retain the output and reconciliation
   together. Stop if any production prerequisite or SQL compilation issue is
   unresolved.

## Choose the output view

| Output label | Active levels |
|---|---|
| `Aggs`, `Lloyds` | Country, US state, postcode |
| `PRA` | Country, US state |
| `BSCR` | Country, US state, overlapping regional views including `ALL` |

The query emits rows only for enabled `EQ`, `FL`, `WS`, and `FR` flags and
splits output by `PerilCode`, `IsFloodRe`, currency, geography, and the other
final grouping dimensions. `PRA_REGION`, `CRESTA`, and `ACCOUNT` are declared
or discussed in the SQL/docs but are not emitted as active levels. `STATE`
rows are US-only; unknown postcodes are excluded.

The measures are policy-term measures: `TIV_SOURCE` is ground-up TIV,
`GROSS_SOURCE` is after applicable deductible and peril limit, and
`NET_SOURCE` additionally applies participation and Fine Art retention.
GBP measures are `TIV_GBP`, `GROSS_GBP`, and `NET_GBP`. Exception counts are
post-level-expansion aggregates, not necessarily source-population counts.

BSCR regional views overlap by design. Do not add country, state, regional,
`ALL`, peril, or use-case rows together. In particular, one US row can occur
in `NA_HU`, `NA_EQ`, `US_ALL`, and `ALL`.

**Stop if FX is missing, zero, negative, conflicting, or otherwise unusable:**
GBP values can be null without increasing `InvalidFXRowCount`, so a zero
exception count does not prove conversion is complete. These are provisional
exposure totals, not the PRA, BSCR, or Lloyd's returns despite the output
labels.

# BSCR SQL — legacy versus current

## Executive summary

**Use `bscr-output.sql` for the current calculation; use `bscr-extract-legacy.sql` only for historical reconciliation.** Both produce final regional aggregates, despite the legacy file's “extract” name.

The current query uses wind data for wind regions, removes policy-side geocode duplication, and separates policies before applying caps. It also adds Japanese earthquake and non-US earthquake views. **Different totals are expected**, not automatically a reconciliation failure.

Both default to **full USD**, not USD millions. `ALL` remains **earthquake-only**, and `count_policies` is **not a distinct-policy count**.

[Legacy SQL](../../bscr/sql/bscr-extract-legacy.sql) · [Current SQL](../../bscr/sql/bscr-output.sql) · [Runbook](runbook.md) · [Reconciliation evidence](reconciliation.md)

## Main differences

| Area | Legacy | Current |
|---|---|---|
| Coverage selection | Peril 1 only | Perils 1 and 2 |
| Policy selection | Policy type 1 only | Types 1 and 2, matched to coverage peril |
| Policy join | Account only | Account and peril |
| Geocode | Policy-side rows expanded by an exposure join | Original exposure-side classification |
| Cap grouping | Omits `policyid` | Includes `policyid` |
| Regional views | Six labels, all using earthquake data | Eight labels with explicit peril routing |
| Geography matching | Binary comparisons in several geographic tests and the US-state lookup | Applicable database/column collation |

## Region-to-peril routing

| Region | Legacy | Current |
|---|---|---|
| `is_nahu` — NA hurricane | Earthquake (1) | Wind (2) |
| `is_eu` — European windstorm | Earthquake (1) | Wind (2) |
| `is_jp` — Japanese wind/typhoon | Earthquake (1) | Wind (2) |
| `is_na_eq` | Earthquake (1) | Earthquake (1) |
| `is_jp_eq` | Not emitted | Japanese earthquake (1) |
| `is_us_all` | Earthquake (1) | Earthquake (1) |
| `is_non_us` | Not emitted | Non-US earthquake (1), including NULL country |
| `ALL` | Earthquake (1) | Earthquake (1) |

**Do not sum overlapping regions or add them to `ALL`.** `ALL` is not an earthquake-plus-wind total.

## Why amounts can change

### Geocode duplication

Legacy joins policies to exposure, then rejoins on account alone. An account's exposure can therefore appear in both geocode buckets.

Illustrative example: one policy, the same geography, 100 ungeocoded plus 200 geocoded, and a non-binding cap. Legacy can assign 300 to each bucket (**600 total**); current retains **100 + 200 = 300**.

### Policy caps

Legacy can group separate policies together when their other grouping fields and limits match. Current includes `policyid`, caps each policy's exposure grouping separately, then rolls up the results.

**This is not necessarily one worldwide cap per policy.** The cap also groups by peril, state, country and geocode. Multiple policies on an account still each receive matching account exposure.

### Geography matching

Legacy's binary US-state lookup does not match `CALIFORNIA` to `California`. Current can match them under a case-insensitive database collation. Not every legacy country lookup join specifies binary collation, so legacy matching is not uniformly case-sensitive.

## What stays the same

- Eight output columns: `cntrycode, bscr_entity, region, sum_pml, sum_net, count_policies, is_geocoded, peril_id`. Legacy's peril ID is always 1; current emits 1 or 2.
- GBP-to-USD conversion at the final SELECT, default `@gbp_to_usd = 1.35`; no million scaling. Do not apply workbook FX again.
- QS retention `0.5`, SRP retention `0.3333`, with QS taking precedence.
- All US states included in NA hurricane; the same entity substring rules and optional entity filter.
- `count_policies` counts grouped source rows, not distinct policies or contracts.
- Deductible threshold: below deductible → zero; otherwise retain the full value rather than subtracting the deductible.

For a historical source-currency CSV comparison, set legacy FX to **1**. Compare the same snapshot, entity scope and currency basis, then separate changes caused by geocoding, policy caps, peril selection and geography. The linked reconciliation records snapshot-specific results; this page explains the SQL rules, not production approval.

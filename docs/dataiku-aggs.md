# Dataiku OED aggregates

## Status and scope

This document describes the single canonical query:

- `dataiku/Dataiku-Aggs.sql`

The former separate policy-terms and `querylong` copies have been consolidated
into that path. The query is a provisional OED aggregation. It is not an
approved final PRA, BSCR, or Lloyd's regulatory calculation.

The query reads OEDIDs 42 (`UK`) and 44 (`EU`) and applies the configured OED
policy terms, participation, Fine Art QS retention, peril split, FX conversion,
and geography views. Current source mappings and geography sets remain
provisional and require run-specific approval.

## Use cases and active levels

| Use case | Active aggregation levels | Output meaning |
|---|---|---|
| Core Aggs (`Aggs`) | `COUNTRY`, `STATE`, `POSTCODE` | Peril-split OED exposure after the query's configured terms |
| PRA | `COUNTRY`, `STATE` | Provisional OED-derived geography view; not the PRA workbook route |
| BSCR | `COUNTRY`, `STATE`, `NA_HU`, `NA_EQ`, `JP`, `EU`, `US_ALL`, `ALL_EX_US`, `ALL` | Overlapping provisional regional views; not Schedule X output |
| Lloyds (`Lloyds`) | `COUNTRY`, `STATE`, `POSTCODE` | Generic geography view; not the Lloyd's supplementary process |

`PRA_REGION` and `CRESTA` remain inactive. `ACCOUNT` is not emitted by the
canonical query. The active levels are expanded explicitly in `level_rows` and
then checked against `aggregation_levels`.

Use cases and levels overlap. Consumers must filter one use case and one level;
they must not add different use cases, levels, or peril rows together.

## Inputs and enrichment

The physical sources are defined in the input CTEs:

- OED data from `prod_group_kairos_sandbox.dataiku.ukeu_validator_oed`;
- GC LOB mapping from
  `prod_group_kairos_sandbox.dataiku_temp.RETAILROLLUPDATA_map_lob_mapping_gc`;
- FX rates from `prod_group_kairos_sandbox.dataiku_temp.RETAILROLLUPDATA_map_fx_rates`.

The query normalizes LOB keys, rejects ambiguous LOB mappings from monetary
joins, validates FX cardinality, derives country/state/postcode fields, and
records mapping and FX exceptions.

## Calculation behavior

For each source row and selected peril:

```text
TIV       = BuildingTIV + ContentsTIV + BITIV + OtherTIV
GROSS     = TIV after the configured deductible and peril limit
NET       = GROSS * participation factor * Fine Art retention factor
GBP value = source value * validated RateToGBP
```

Policy-term precedence is:

1. peril deductible;
2. otherwise blanket deductible;
3. otherwise Building, Contents, and BI coverage deductibles;
4. peril limit applied after deductible treatment.

The query emits `EQ`, `FL`, `WS`, and `FR` rows only when the corresponding
peril flag is enabled. A source row with no enabled peril flag is not emitted.
Do not sum different `PerilCode` values unless an approved non-overlapping
population rule exists.

`LocParticipation` is interpreted using the configured OED-specific
`ParticipationScale`; null participation defaults to 1 and invalid values are
flagged. Fine Art QS cession is taken from the configured OED field. These are
implementation rules, not approval of the regulatory methodology.

## Country and geography keys

`AggregationValue` is the normalized country code for `COUNTRY` levels. To
prevent source labels from fragmenting totals, `AggregationCountry` is also set
to the canonical country code in country, state, and postcode rows. Thus source
labels such as `AUS` and `AUSTRALIA` under country code `AU` aggregate together
and appear as `AU` in the output.

For US rows, `STATE` uses `County`, then `AreaCode`, as the current geography
approximation. Non-US rows do not receive a state row. `POSTCODE` excludes null
or blank postcodes represented as `UNKNOWN`.

The BSCR sets are country-based approximations and overlap. For example, a US
row can contribute to `NA_HU`, `NA_EQ`, `US_ALL`, and `ALL`. They are not
mutually exclusive regulatory regions.

## Output grain and controls

The final result is grouped by the selected use case and level plus the
following control dimensions:

```text
OEDID, DatasetLabel, UseCase, AggregationLevel, AggregationValue,
AggregationCountry, AggregationState, AggregationRegion, AggregationPostcode,
ReportingEntity, ReportingLOB, PerilCode, CountryCode, IsGeocoded,
SourceCurrency, RateToGBP, DeductibleBasis, IsFloodRe, FACFlag,
GeographyMappingBasis
```

It emits source-row, account, and location counts; TIV, gross, and net source
and GBP measures; and invalid TIV, participation, LOB, and FX counts.

Review these controls before relying on totals:

1. policy terms are OED-field approximations, not approved modeled PML;
2. source rows can expand across perils and overlapping levels;
3. invalid participation and invalid FX can produce null monetary measures;
4. missing or malformed TIV components can invalidate a whole source row;
5. source-row and distinct-ID counts are post-enrichment aggregates;
6. `ALL`, regional BSCR levels, and country levels must not be added together;
7. the query does not itself prove source-period, mapping, FX, or owner approval;
8. the output is not a substitute for the PRA, BSCR, or Lloyd's runbooks.

## Relationship to the runbooks

- `runbooks/source/pra.md` documents the controlled PRA/Python/workbook route.
- `runbooks/source/bscr.md` documents the separate BSCR Schedule X route.
- `runbooks/source/lloyds-supplementary.md` documents the separate Lloyd's
  supplementary processes.
- `runbooks/source/run-checks.md` defines evidence, reconciliation, and stop
  conditions for every controlled run.
- `dataiku/.plan.md` and `docs/dataiku-aggs-for-llm.md` describe the earlier
  uncapped-baseline design contract; they are not approval of this policy-terms
  query.

Before execution, record the exact query revision, OED IDs, source snapshot,
peril scope, mappings, FX basis, row counts, totals, exception counts, and
reconciliation evidence.

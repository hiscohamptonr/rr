# Dataiku OED aggregates

## Status and scope

This document describes the checked-in `dataiku/Dataiku-Aggs.sql` at commit
`d264675`. A newer script is known to exist outside this repository, so this is
a current-repository baseline rather than documentation of that pending
version. Revalidate and update this document when the newer script is added.

For a machine-oriented implementation and validation contract for the planned
revision, see [Dataiku-Aggs-for-llm.md](dataiku-aggs-for-llm.md). That companion
does not describe behavior implemented by the current SQL.

Verified current discrepancies and their owner decisions are in the repository
[calculation discrepancy register](calculation-discrepancies.md).

The checked-in query reads OEDIDs 42 (`UK`) and 44 (`EU`) and creates reusable
geography views of uncapped OED exposure. It does **not** reproduce the final
PRA, BSCR, or Lloyd's regulatory calculations described in `runbooks/source/`.

## Use cases

| Use case | Active aggregation levels | What the checked-in query produces | Regulatory status |
|---|---|---|---|
| Core Aggs (`Aggs`) | `ACCOUNT`, `COUNTRY`, `STATE`, `POSTCODE` | Ground-up OED TIV in source currency and GBP | Provisional uncapped exposure view |
| PRA | `COUNTRY`, `STATE` | The same ground-up TIV population grouped by the available geography | Not PRA PML: no peril/policy selection, deductible, policy limit, PRA region, CDS class, or workbook calculation |
| BSCR | `COUNTRY`, `STATE`, `NAHU`, `NA_EQ`, `JP`, `EU`, `US_ALL`, `ALL_XUS`, `ALL` | Overlapping country-based regional views with a derived BSCR entity | Not Schedule X output: no deductible, policy limit, participation, or QS/SRP net calculation; regional mappings are provisional |
| Lloyd's (`Lloyds`) | `COUNTRY`, `STATE`, `POSTCODE` | Generic geography aggregates from the same OED population | Not the Lloyd's supplementary outputs: no peril split, CRESTA, California/South Africa scope, scale factors, or report-specific calculations |

`PRA_REGION` and `CRESTA` are configured as inactive. CRESTA also has no
implemented row-generation branch, so changing its active flag alone would not
produce CRESTA output.

## Inputs and enrichment

The physical sources are defined near the top of the SQL:

- OED data from `prod_group_kairos_sandbox.dataiku.ukeu_validator_oed`;
- GC LOB mapping from
  `prod_group_kairos_sandbox.dataiku_temp.RETAILROLLUPDATA_map_lob_mapping_gc`;
- FX rates from
  `prod_group_kairos_sandbox.dataiku_temp.RETAILROLLUPDATA_map_fx_rates`.

The query derives `ModelledLOB`, `BSCREntity`, geography values, geocoding
status, and a source-currency-to-GBP rate before expanding each source row into
the active aggregation levels.

## Measures

For each enriched source row, the checked-in calculation is:

```text
Ground-up TIV = BuildingTIV + ContentsTIV + BITIV + OtherTIV
GBP TIV       = Ground-up TIV * RateToGBP
```

The final columns call these amounts `GrossTIVSourceCurrency` and
`GrossTIVGBP`, but they are more accurately interpreted as **ground-up,
uncapped TIV**. The query does not apply:

- `LocParticipation`;
- deductibles or policy limits;
- policy share or policy-level capping;
- `_QS` or `_SRP` retention;
- peril or policy-type filters.

It must therefore not be described as capped exposure, gross/net regulatory
PML, or modeled PML.

## Output shape

The nominal aggregation level is only part of the final grain. A row is grouped
by:

```text
OEDID, DatasetLabel, UseCase, AggregationLevel, AggregationValue,
AggregationSortOrder, BranchName, ModelledLOB, BSCREntity, CountryCode,
IsGeocoded, SourceCurrency, SourceCurrencyRateToGBP, RateRecordCount
```

Consequently, `BSCR/ALL` is not necessarily one grand-total row,
`BSCR/EU` is not necessarily one EU row, and an account can have several
`Aggs/ACCOUNT` rows. Consumers should filter one `UseCase` and one
`AggregationLevel`, then aggregate only dimensions appropriate to their
purpose. Different use cases or aggregation levels must not be added together.

The output also contains source-row, distinct-account, distinct-location, and
unmapped-LOB counts. Its FX exception field is based on the selected `MAX`
rate, not a complete raw-FX validity control; it can miss conflicting,
malformed, non-positive, or null records when another positive rate is chosen.

## Current geography behavior

- `COUNTRY` normally uses the source country name, with country code as a
  fallback.
- `STATE` uses US `County`, then `AreaCode`; non-US records use
  `NOT_APPLICABLE`. This is an approximation, not an approved state mapping.
- `POSTCODE` trims the source postcode and substitutes `UNKNOWN` for blank or
  null values.
- BSCR `NAHU` and `NA_EQ` are currently country-based approximations. Every US
  row enters both categories.
- BSCR regional levels overlap. For example, a US row can contribute to
  `NAHU`, `NA_EQ`, `US_ALL`, and `ALL`; these levels are not mutually exclusive.

## Known controls and limitations

Before relying on an output, address or quantify these points:

1. A LOB mapping key that resolves to several `ModelledLOB` values can multiply
   source exposure through the join. Whitespace-normalisation happens at join
   time rather than before deduplication, so duplicate normalised keys can also
   multiply a row even when they map to the same LOB.
2. FX records are reduced with `MAX(RateToGBP)`; conflicting positive rates are
   not rejected, and negative rates are not marked invalid.
3. Null, malformed, or out-of-range TIV components are converted to zero by
   `TRY_CAST` plus `COALESCE` without separate invalid-TIV counts.
4. `UnmappedLOBRowCount` counts null mappings, but not non-null LOBs that fail
   BSCR entity classification.
5. `DistinctLocationCount` counts `LocNumber` alone, which may undercount if a
   location number is unique only within an account.
6. A missing FX rate creates a separate null-rate group whose GBP aggregate is
   null. It is not safely interpretable as zero or as a partial total; review
   the selected-rate exception count alongside every GBP total.
7. `IsGeocoded` is false only for null, blank, or the literal string `0`.
   Unexpected nonblank values are treated as geocoded and split the output.
8. Distinct account/location counts ignore null identifiers and source-row
   counts are post-LOB-join; none may be summed across output levels.

These are stop-and-review conditions where they prevent reconciliation, as set
out in `runbooks/source/run-checks.md`.

## Relationship to the runbooks

- `runbooks/source/pra.md` documents the controlled PRA/Python/workbook route,
  including peril and policy selection, deductible treatment, policy capping,
  PRA mappings, and workbook pivots.
- `runbooks/source/bscr.md` documents the seven-column BSCR gross/net output,
  retention calculation, workbook conversion, and Schedule X handoff.
- `runbooks/source/lloyds-supplementary.md` documents the separate RoW, South
  Africa, California, and EU CRESTA processes.
- `dataiku/.plan.md` describes proposed improvements to make this query a
  controlled uncapped exposure producer. Its required measures and controls are
  planned behavior, not behavior of the checked-in SQL.

## Revalidation when the updated script arrives

When the pending script is committed:

1. record its commit and replace the baseline revision above;
2. compare inputs, selected OEDIDs, active levels, output columns, and final
   grain;
3. confirm whether participation and QS/SRP retention are implemented;
4. confirm LOB cardinality, FX validity, and invalid-TIV controls;
5. confirm geography codes, especially `NA_EQ` versus the planned canonical
   `NAEQ`, and whether state, PRA region, or CRESTA mappings were added;
6. reconcile row counts and monetary totals against a preserved output from
   this baseline before changing the status statements in this document.

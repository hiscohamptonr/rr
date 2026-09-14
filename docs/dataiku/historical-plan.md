# Dataiku aggregates — historical plan

[Start here](../../README.md) · [Current query documentation](aggregation.md)

The companion [historical technical contract](technical-contract.md) defines
the earlier baseline's proposed handling of final grain, eligibility,
normalisation, controls, and reconciliation. Read it with this plan; neither
document is the execution contract for the current canonical query.

## Current status

- `Dataiku-Aggs.sql` is the single canonical Dataiku query.
- It supersedes the former separate policy-terms and `querylong` copies.
- It reads OEDIDs 42 and 44 and emits provisional policy-term, peril,
  participation, retention, FX, and geography aggregates.
- The design below documents the earlier uncapped-baseline contract. It remains
  useful for comparison and controls, but is not a complete description of the
  canonical query.

## Historical baseline objective

The following sections describe the earlier uncapped OED baseline design. They
are retained for comparison and control requirements; they are not a complete
specification of the current policy-terms query.

The historical objective was to make the existing query a controlled, reusable
**uncapped OED exposure** aggregation using only columns and mapping sources
already referenced by the script.

The historical result was intended to support provisional Aggs, PRA, and BSCR
geography views. It was not intended to claim capped exposure or modeled PML.

## Constraints

- Keep the implementation in one Databricks/Dataiku SQL script using CTEs.
- Do not assume unavailable columns or introduce joins to hypothetical tables.
- Do not modify or depend on the Excel workbooks.
- Do not implement PRA region, CDS class, or CRESTA until approved mappings or
  source fields are available.
- Do not add generated Dataiku outputs to Git.
- Preserve current output columns where practical so comparisons remain easy.

## Available calculation inputs

Use the fields already selected by `input_oed`, including:

```text
OEDID
LocNumber
AccNumber
BranchName
Country / CountryCode
County / AreaCode / PostalCode
AddressMatch
BuildingTIV / ContentsTIV / BITIV / OtherTIV
LocCurrency
LocParticipation
LocUserDef1
AccUserDef2-5
```

Continue using the existing LOB mapping and FX sources to derive
`ModelledLOB` and `RateToGBP`.

## Required measures

Calculate the following before expanding rows into aggregation levels:

```text
GroundUpExposureSource = BuildingTIV + ContentsTIV + BITIV + OtherTIV

GrossExposureSource = GroundUpExposureSource * ParticipationFactor

NetExposureSource = GrossExposureSource * RetentionFactor

GroundUpExposureGBP = GroundUpExposureSource * RateToGBP

GrossExposureGBP = GrossExposureSource * RateToGBP

NetExposureGBP = NetExposureSource * RateToGBP
```

Use `CalculationBasis = 'UNCAPPED_OED_EXPOSURE'` in the output.

### Participation

- Treat `LocParticipation` as a decimal factor in the range 0 to 1.
- Use `1.0` for null participation, but count and expose those defaulted rows.
- Do not silently normalize values greater than 1 as percentages.
- Flag values below 0 or above 1 as invalid; do not silently use them in
  monetary totals.

### Retention

Derive retention from normalized `ModelledLOB`:

```text
suffix _QS  -> 0.5000
suffix _SRP -> 0.3333
otherwise   -> 1.0000
```

Use exact suffix logic, such as a suitable Databricks regular expression. Do
not use an unescaped SQL `LIKE` underscore as though it were a literal.

## CTE changes

Keep the current broad structure, but make these focused changes:

1. Add a small `run_parameters` CTE for calculation basis and participation
   convention.
2. Normalize LOB mapping keys before deduplication.
3. Add a mapping-cardinality CTE that identifies keys resolving to more than
   one `ModelledLOB`.
4. Do not join ambiguous LOB mappings in a way that multiplies exposure.
5. Replace arbitrary FX selection with controls for one positive valid rate per
   currency. Expose conflicting-rate counts rather than silently trusting
   `MAX(RateToGBP)`.
6. Add numeric validity flags before coalescing TIV components. Distinguish
   genuine null values from malformed non-null values.
7. Calculate participation, retention, and the six exposure measures in the
   normalized/calculated row layer.
8. Carry those measures through `level_rows`, `active_level_rows`, and the final
   aggregation.

Mapping CTEs should have stable schemas so their `VALUES` or current query
bodies can later be replaced with controlled mapping tables without changing
downstream calculation CTEs.

## Geography scope

For the first comparison, retain the existing active aggregation levels:

```text
Aggs:   ACCOUNT, COUNTRY, STATE, POSTCODE
PRA:    COUNTRY, STATE
BSCR:   COUNTRY, STATE, NAHU, NAEQ, JP, EU, US_ALL, ALL_XUS, ALL
Lloyds: COUNTRY, STATE, POSTCODE
```

Use `NAHU` and `NAEQ` as the canonical aggregation-level codes. These are
domain codes rather than snake-case field names. A legacy BSCR export may map
them to `is_nahu` and `is_na_eq` respectively, but the Dataiku aggregation
codes should not mix `NAHU` with `NA_EQ`.

Keep `PRA_REGION` and `CRESTA` inactive.

The current source does not contain a confirmed state field. Preserve the
existing County/AreaCode-derived value for the first run, but expose
`GeographyMappingBasis = 'CURRENT_OED_COUNTRY_AREA_APPROXIMATION'`. Do not
describe it as an approved state mapping.

Likewise, retain current country-based NAHU and NAEQ membership for the first
comparison, but label it as approximate. Do not present these results as final
BSCR classifications.

## Final output columns

Retain the existing identifying and count columns, and ensure the final result
contains at least:

```text
OEDID
DatasetLabel
UseCase
AggregationLevel
AggregationValue
AggregationSortOrder
CalculationBasis
GeographyMappingBasis
BranchName
ModelledLOB
BSCREntity
CountryCode
IsGeocoded
SourceCurrency
SourceCurrencyRateToGBP
RateRecordCount
SourceRowCount
DistinctAccountCount
DistinctLocationCount
GroundUpExposureSourceCurrency
GrossExposureSourceCurrency
NetExposureSourceCurrency
GroundUpExposureGBP
GrossExposureGBP
NetExposureGBP
UnmappedLOBRowCount
UnmappedEntityRowCount
AmbiguousLOBMappingRowCount
MissingParticipationRowCount
InvalidParticipationRowCount
InvalidTIVRowCount
MissingOrInvalidFXRowCount
ControlStatus
```

Do not add `GrossPML`, `NetPML`, or capped-exposure columns in this iteration.

## Output use

- Filter `UseCase = 'Aggs'` for general account and geography exposure views.
- Filter `UseCase = 'PRA'` for provisional country and area-level PRA inputs.
- Filter `UseCase = 'BSCR'` for provisional regional gross/net exposure views.
- Never sum different use cases or aggregation levels together.
- PRA and BSCR outputs remain provisional until their mappings and policy-term
  requirements are confirmed.

## Validation before running

Review the SQL diff and confirm:

- no new physical source tables were invented;
- no mapping join can multiply source rows;
- monetary totals exclude invalid participation and invalid FX rows rather than
  silently treating them as valid;
- null/default and invalid counts are visible in the final output;
- all output amounts state their currency and uncapped basis.

## First Dataiku run

Run the revised script for the existing configured OEDIDs 42 and 44. Preserve:

- exact query revision;
- OED IDs and labels;
- execution date;
- complete output dataset;
- source row, account, and location counts;
- source and GBP totals for all three measures;
- mapping, participation, TIV, and FX exception counts.

## Comparison with EDM/Python

First validate Dataiku measures against preserved Dataiku detail at the approved
uncapped grain: source population/reporting period; row, account, and location
counts; valid/exception populations; and totals by country, entity, geocoding,
and available regional views.

The current `BSCR_UKEU.py` output is **not** a common uncapped comparator: it
selects peril/policy type, applies a deductible threshold and policy cap, does
not read `LocParticipation`, and derives its net amount from capped PML. Compare
only independently aligned population dimensions unless an approved common
detail extract/reconciliation bridge explicitly defines ground-up,
participation-adjusted, and retention-adjusted measures. Record deductible,
limit, policy-join, source-population, FX, mapping, entity, and retention-rule
effects as separate reconciliation categories.

## Acceptance criteria

- The query executes successfully for OEDIDs 42 and 44.
- Source exposure is not multiplied by LOB or FX joins.
- Ground-up equals the sum of valid TIV components.
- Gross equals ground-up times participation.
- Net equals gross times retention.
- Source-to-GBP conversion reconciles using the selected valid rate.
- All missing, invalid, ambiguous, and unmapped populations are quantified.
- Each output row is explicitly identified as uncapped and provisional where
  mappings are approximate.

## Deferred work

Only add these when confirmed data or controlled mappings exist:

- policy-level deductible and limit calculations;
- capped exposure or historical PML-compatible measures;
- peril and policy-type dimensions;
- approved state and catastrophe-region mappings;
- PRA region and CDS class;
- CRESTA;
- final regulator-template handoff outputs.

# Dataiku aggregates — historical plan

[Start here](../../README.md) · [Current query documentation](aggregation.md)

This plan preserves an earlier uncapped-baseline proposal and must not be
merged with current query behavior or treated as an execution record. The
canonical checked-in SQL is the current reference; the proposal below is
retained only as historical design intent, comparison context, and control
evidence. No approval, successful run, or current-period source lineage is
established by this page.

## Current status

- `Dataiku-Aggs.sql` is the single checked-in canonical Dataiku query.
- It supersedes the former separate policy-terms and `querylong` copies.
- It selects OEDIDs 42 and 44 and proposes policy-term, peril, participation,
  retention, FX, and geography aggregates, subject to source and execution
  approval.
- The design below documents the earlier uncapped-baseline contract. It is not
  a complete description of the current policy-terms query.

## Current-query differences that must not be back-applied

The checked-in query currently includes deductible precedence, peril limits,
enabled peril row expansion, participation, Fine Art retention, and the
`TIV_SOURCE`/`GROSS_SOURCE`/`NET_SOURCE` measure names. Its active regional
codes are `NA_HU`, `NA_EQ`, and `ALL_EX_US`, not the historical proposal's
`NAHU`, `NAEQ`, and `ALL_XUS`. The current query also splits output by
`PerilCode`, `IsFloodRe`, and other grouping dimensions. These are observed
source differences, not evidence that the current methodology is approved.

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

## Historical baseline measures (proposed, not current output)

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

## Historical proposed CTE changes (not a current implementation checklist)

Keep the current broad structure, but make these focused changes:

1. Add a small `run_parameters` CTE for calculation basis and participation
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

## Historical proposed geography scope

For the first comparison, retain the existing active aggregation levels:

```text
Aggs:   ACCOUNT, COUNTRY, STATE, POSTCODE
PRA:    COUNTRY, STATE
BSCR:   COUNTRY, STATE, NAHU, NAEQ, JP, EU, US_ALL, ALL_XUS, ALL
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

## Historical proposed final output columns

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
GroundUpExposureSourceCurrency
GrossExposureSourceCurrency
NetExposureSourceCurrency
GroundUpExposureGBP
GrossExposureGBP
NetExposureGBP
UnmappedLOBRowCount
UnmappedEntityRowCount
MissingParticipationRowCount
InvalidParticipationRowCount
InvalidTIVRowCount
MissingOrInvalidFXRowCount
ControlStatus
```

Do not add `GrossPML`, `NetPML`, or capped-exposure columns in this iteration.

## Historical proposed output use
- Filter `UseCase = 'Aggs'` for general account and geography exposure views.
- Filter `UseCase = 'PRA'` for provisional country and area-level PRA inputs.
- Filter `UseCase = 'BSCR'` for provisional regional gross/net exposure views.
- Never sum different use cases or aggregation levels together.
- PRA and BSCR outputs remain provisional until their mappings and policy-term
  requirements are confirmed.

## Historical proposed validation before running

Review the SQL diff and confirm:

- no mapping join can multiply source rows;
- monetary totals exclude invalid participation and invalid FX rows rather than
  silently treating them as valid;
- null/default and invalid counts are visible in the final output;
- all output amounts state their currency and uncapped basis.

## Historical proposed first-run evidence

Run the revised script for the existing configured OEDIDs 42 and 44. Preserve:

- exact query revision;
- OED IDs and labels;
- execution date;
- complete output dataset;
- source row, account, and location counts;
- mapping, participation, TIV, and FX exception counts.

## Historical proposed comparison with EDM/Python

First validate Dataiku measures against preserved Dataiku detail at the approved
uncapped grain: source population/reporting period; row, account, and location
counts; valid/exception populations; and totals by country, entity, geocoding,
and available regional views.

The historical database-connected `bscr/old-process/BSCR_UKEU.py` output is
**not** a common uncapped comparator: its SQL selects peril/policy type and
applies a deductible threshold and policy cap; its Python derives net from
capped PML without `LocParticipation`. The current BSCR SQL-only route is
documented separately in the [BSCR runbook](../bscr/runbook.md).
Compare only independently aligned population dimensions unless an approved
common detail extract/reconciliation bridge explicitly defines ground-up,
participation-adjusted, and retention-adjusted measures. Record deductible,
limit, policy-join, source-population, FX, mapping, entity, and retention-rule
effects as separate reconciliation categories.

## Historical proposed acceptance criteria

- The query executes successfully for OEDIDs 42 and 44.
- Source exposure is not multiplied by LOB or FX joins.
- Ground-up equals the sum of valid TIV components.
- Gross equals ground-up times participation.
- Net equals gross times retention.
- Source-to-GBP conversion reconciles using the selected valid rate.
- All missing, invalid, ambiguous, and unmapped populations are quantified.
- Each output row is explicitly identified as uncapped and provisional where
  mappings are approximate.

## Historical deferred work at plan time

At the time of this historical plan, only add these when confirmed data or
controlled mappings exist:

- policy-level deductible and limit calculations;
- capped exposure or historical PML-compatible measures;
- peril and policy-type dimensions;
- approved state and catastrophe-region mappings;
- PRA region and CDS class;
- CRESTA; and
- final regulator-template handoff outputs.

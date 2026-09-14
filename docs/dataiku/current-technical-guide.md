# Dataiku OED aggregates — current technical guide

[Start here](../../README.md) · [Human guide](aggregation.md) ·
[Shared controls](../operating-controls.md) · [Historical contract](technical-contract.md)

This document describes the current canonical query, `dataiku/Dataiku-Aggs.sql`,
for LLM interpretation, review, and controlled execution. It is a provisional
policy-terms/peril implementation. It is not an approved final PRA, BSCR, or
Lloyd's calculation. The historical [technical contract](technical-contract.md)
and [historical plan](historical-plan.md) describe the earlier uncapped baseline
and must not be merged with current behavior.

## Canonical query and physical inputs

The former separate policy-terms and `querylong` copies are consolidated into
`dataiku/Dataiku-Aggs.sql`. Execute that exact SQL in the approved
Dataiku/Databricks SQL environment; this repository does not define a universal
CLI wrapper or warehouse connection command. Record the environment-specific
command or job identity, query revision, and complete output location.

The query hard-codes selected OED metadata:

| OEDID | DatasetLabel | ParticipationScale |
|---:|---|---:|
| 42 | `UK` | 100.0 |
| 44 | `EU` | 1.0 |

The only physical source CTEs are:

- `prod_group_kairos_sandbox.dataiku.ukeu_validator_oed` (OED rows);
- `prod_group_kairos_sandbox.dataiku_temp.RETAILROLLUPDATA_map_lob_mapping_gc`
  (GC LOB mapping);
- `prod_group_kairos_sandbox.dataiku_temp.RETAILROLLUPDATA_map_fx_rates`
  (FX rates).

The query's run parameters set `MissingFineArtCessionDefault` to `0.0` and
`GeographyMappingBasis` to `CURRENT_OED_COUNTRY_AREA_APPROXIMATION`. The former
is retained as a parameter in the query; the current measure logic defaults a
missing Fine Art cession to retention factor `1.0`.

## Active levels and row expansion

`aggregation_levels` declares these active levels:

| Use case | Active levels |
|---|---|
| `Aggs` | `COUNTRY`, `STATE`, `POSTCODE` |
| `PRA` | `COUNTRY`, `STATE` |
| `BSCR` | `COUNTRY`, `STATE`, `NA_HU`, `NA_EQ`, `JP`, `EU`, `US_ALL`, `ALL_EX_US`, `ALL` |
| `Lloyds` | `COUNTRY`, `STATE`, `POSTCODE` |

`CRESTA` and `PRA_REGION` are declared but inactive. `ACCOUNT` is not emitted.
`level_rows` explicitly expands each complete source/peril row into the active
use-case/level populations, and `active_rows` filters the expansion through
`aggregation_levels`. A source row can therefore produce many output rows.
Consumers must choose one use case and one level before totaling.

The output is split by `PerilCode`. Enabled flags are recognized when the
trimmed, upper-cased flag is `1`, `TRUE`, `Y`, or `YES`; the query emits `EQ`,
`FL`, `WS`, and `FR` rows only when the corresponding flag is enabled. A row
with no enabled peril is absent. Different `PerilCode` values must not be
summed unless an approved non-overlapping population rule exists.

## Enrichment and mapping controls

OED country code is upper-cased and trimmed. Country name uses the reference
country name when recognized, otherwise a nonblank source country, otherwise
country code, otherwise `UNKNOWN`. The supported reference includes AT, BA,
BE, BG, BR, CA, CH, CZ, DE, DK, EE, ES, FI, FR, GB, GR, HR, HU, IE, IT, JP,
LU, NL, NO, PL, PT, RO, SE, SI, SK, and US.

LOB keys are normalized with `UPPER(TRIM(COALESCE(value, '__NULL__')))` for
`AccUserDef2`, `AccUserDef3`, `AccUserDef4`, `AccUserDef5`, `BranchName`, and
`LocUserDef1`. Non-null `modelled_lob` values are trimmed; normalized mapping
rows are distinct. `lob_cardinality` counts distinct modelled LOBs per key.
Only cardinality one enters `valid_lob_mapping`; zero is `UNMAPPED`, one is
`MAPPED`, and greater than one is `AMBIGUOUS`. Ambiguous mappings are not joined
to monetary rows, but source rows are retained and counted in
`AmbiguousLOBRowCount`; the final output does not expose the internal status.

FX currency codes are upper-cased and trimmed, and rates are `TRY_CAST` to
`DECIMAL(24,12)`. Per currency, the query records total rows and distinct rates.
`RateToGBP` is usable only when exactly one distinct parsed rate exists and it
is between `0.000000000001` and `999999999999.0`. The separate status CASE uses
counts only: zero parsed rates → `INVALID`, multiple distinct rates →
`CONFLICTING`, multiple records with one distinct rate → `DUPLICATE_CONSISTENT`,
otherwise → `VALID`. An unmatched currency becomes `MISSING`.

**Observed control gap:** a single parsed zero or negative rate has a null
`RateToGBP` but status `VALID`. Repeated identical non-positive rates instead
get `DUPLICATE_CONSISTENT`. Neither status contributes to `InvalidFXRowCount`,
so GBP measures can be null even when that count is zero. Independently check
rate positivity and null converted measures; do not rely on the exception
count alone. Invalid/missing FX is not converted to zero at row level, but
aggregate sums can omit null measures and therefore understate incomplete totals.

## Numeric normalization and policy terms

TIV components, deductibles, peril deductibles, and peril limits use
`TRY_CAST(... AS DECIMAL(38,6))`. A non-null component that fails the cast sets
`InvalidTIVFlag`. Invalid TIV makes `TIV` null; otherwise null components are
coalesced to zero:

```text
TIV = COALESCE(BuildingTIV, 0) + COALESCE(ContentsTIV, 0)
    + COALESCE(BITIV, 0) + COALESCE(OtherTIV, 0)
```

`LocParticipation` and `PolUserDef5` are cast to `DECIMAL(20,8)`. The
participation factor is `1` when raw participation is null. Otherwise it is
`RawParticipation / ParticipationScale` only when between zero and one;
otherwise it is null and `InvalidParticipationFlag` is true. A null raw value
sets `ParticipationDefaultedFlag`.

For each selected peril, deductible precedence is:

1. a nonzero peril deductible;
2. otherwise a nonzero blanket deductible;
3. otherwise Building, Contents, and BI coverage deductibles independently.

With a peril or blanket deductible, `TIVAfterDeductible` is
`GREATEST(TIV - deductible, 0)`. Without one, it is the sum of
`GREATEST(BuildingTIV - BuildingDeductible, 0)`, equivalent Contents and BI
terms, and `OtherTIV` without a deductible. A nonzero peril limit then caps the
post-deductible amount with `LEAST`; otherwise it is unchanged.

```text
GROSS = TIVAfterDeductible, capped by the selected peril limit when nonzero
```

Fine Art is true when modelled LOB matches `(^|_)FA(_|$)` or trimmed
`AccUserDef4`/`AccUserDef5` equals `FINE ART`. For Fine Art, null `PolUserDef5`
means retention factor `1`; a cession in `[0,1]` gives `1 - cession`; another
value gives null. Non-Fine-Art rows always have retention factor `1`.

```text
NET = GROSS * ParticipationFactor * RetentionFactor
```

## Currency and control measures

When `RateToGBP` is non-null, the query calculates:

```text
TIV_GBP   = TIV   * RateToGBP
GROSS_GBP = GROSS * RateToGBP
NET_GBP   = NET   * RateToGBP
```

A missing or invalid rate makes each GBP measure null; source-currency measures
remain available subject to their own eligibility. Null participation defaults
to one, while invalid participation can make `NET` and `NET_GBP` null. Invalid
TIV can make all derived monetary measures null for that row. These are
implementation behaviors, not approval of the regulatory methodology.

`IsGeocoded` is false for null, blank, or string `0` `AddressMatch`; true
otherwise. `IsFloodRe` is true when `LocUserDef2` is a trimmed, upper-cased
`1`, `TRUE`, `Y`, or `YES`. `FACFlag` uses the same rule on `LocUserDef3`.

## Geography and reporting fields

For every `COUNTRY` row, `AggregationValue` and `AggregationCountry` are the
canonical country code, or `UNKNOWN` when absent. `STATE` rows exist only for
US rows and use trimmed `County`, then `AreaCode`, then `UNKNOWN`; their value
is `US_` plus upper-cased non-alphanumeric characters replaced by underscores.
Non-US rows have no state value. `POSTCODE` uses trimmed postal code or
`UNKNOWN`; rows with `UNKNOWN` postcode are excluded. A postcode value is
country plus `_` plus upper-cased non-alphanumeric characters removed.

BSCR regional views are country-based approximations and intentionally overlap:

- `NA_HU`: `US`, `CB`, `TC`, `BH`, `JM`, `VI`, `MX`;
- `NA_EQ`: `US`, `CA`;
- `JP`: `JP`;
- `EU`: `GB`, `UK`, `FR`, `DE`, `BE`, `NL`, `LU`, `AT`, `DK`, `SE`, `PL`, `CZ`;
- `US_ALL`: `US`;
- `ALL_EX_US`: every country other than `US` (including `UNKNOWN`);
- `ALL`: every complete row.

Thus one US row can contribute to `NA_HU`, `NA_EQ`, `US_ALL`, and `ALL`.
These populations are not mutually exclusive regulatory regions. For BSCR,
`ReportingEntity` is derived from `BSCREntity`; for other use cases it is
`BranchName`. `ReportingLOB` is null for BSCR and `ModelledLOB` otherwise.
`ReportingCountryCode` is null for BSCR regional levels and otherwise the
country code. `BSCREntity` is assigned by modelled LOB substring precedence:
`HIG`, `HSA`, `3624`, `33` for `S33`, `HIC`, then `UNMAPPED`.

## Final output grain and measures

The final `GROUP BY` is:

```text
OEDID, DatasetLabel, UseCase, AggregationLevel, AggregationValue,
AggregationSortOrder, AggregationCountry, AggregationState, AggregationRegion,
AggregationPostcode, ReportingEntity, ReportingLOB, PerilCode, CountryCode,
IsGeocoded, SourceCurrency, RateToGBP, DeductibleBasis, IsFloodRe, FACFlag,
GeographyMappingBasis
```

The query emits `SourceRowCount`, `DistinctAccountCount`,
`DistinctLocationCount`, `TIV_SOURCE`, `GROSS_SOURCE`, `NET_SOURCE`,
`TIV_GBP`, `GROSS_GBP`, `NET_GBP`, `InvalidTIVRowCount`,
`InvalidParticipationRowCount`, `MissingParticipationRowCount`,
`AmbiguousLOBRowCount`, `UnmappedLOBRowCount`, and `InvalidFXRowCount`.
Counts are post-enrichment and post-level-expansion aggregates, not necessarily
source-population counts.

## Review and evidence requirements

Before execution, record exact query revision, OED IDs and labels, source
snapshot, peril scope, mappings, FX basis, participation scales, Fine Art
cession, geography basis, and owner approvals. Preserve output row counts,
source and GBP totals for all three measures, and mapping, participation, TIV,
and FX exception counts.

Review invalid participation, ambiguous/unmapped LOB and invalid TIV counts.
Check FX rates and null GBP measures independently because `InvalidFXRowCount`
does not cover every unusable rate. Reconcile source/detail totals to grouped
totals at one selected use case and level. Do not add country, regional, `ALL`,
peril, or use-case rows. The output does not itself prove source-period,
mapping, FX, or owner approval and is not a substitute for the PRA, BSCR, or
Lloyd's runbooks.

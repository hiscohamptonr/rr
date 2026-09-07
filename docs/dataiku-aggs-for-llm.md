# Dataiku OED aggregates — LLM implementation contract

This document records the earlier **uncapped OED baseline contract**. The
current canonical query is `dataiku/Dataiku-Aggs.sql`, which is a separate
policy-terms/peril implementation and does not claim to satisfy every
uncapped-baseline field below. Do not claim that either route produces a final
regulatory return.

## Historical baseline facts

- Input is OEDIDs 42/44. Ground-up source TIV is
  `BuildingTIV + ContentsTIV + BITIV + OtherTIV`, with `TRY_CAST` and nulls
  coalesced to zero.
- The current query applies neither participation nor QS/SRP retention. It
  selects FX with `MAX(RateToGBP)`, then groups on that rate.
- The exact current aggregate key is
  `OEDID, DatasetLabel, UseCase, AggregationLevel, AggregationValue,
  AggregationSortOrder, BranchName, ModelledLOB, BSCREntity, CountryCode,
  IsGeocoded, SourceCurrency, SourceCurrencyRateToGBP, RateRecordCount`.
- `SourceRowCount` is post-LOB-join. `DistinctAccountCount` and
  `DistinctLocationCount` ignore null IDs. `IsGeocoded` is false only for
  null/blank/`"0"` AddressMatch values.
- Entity assignment and BSCR regional membership are hard-coded, overlapping,
  and not interchangeable with `bscr/BSCR_UKEU.py`.

## Required design decisions before coding

Do not invent a rule for any item below. Obtain owner approval and record the
mapping/rate version in the output or run record.

1. **Normalised LOB key:** specify trim, case folding, blank-to-null behaviour,
   composite fields, and null-safe equality. Deduplicate *after* normalisation;
   never use a possible business value as a null sentinel.
2. **LOB ambiguity:** an input key resolving to zero or multiple normalised LOBs
   must not multiply an OED row. Define whether it is quarantined or emitted as
   a controlled exception, and count its row and monetary populations.
3. **Entity and retention:** define normalisation, exact markers, precedence,
   and treatment of both/no marker. Do not silently assume Python's substring
   logic or the planned suffix logic is authoritative.
4. **Geography:** publish each country set (including NAHU, NAEQ, EU), mapping
   version, approximation status, and unmatched-country treatment.
5. **Final grain:** state the complete `GROUP BY`, including whether calculation
   basis, geography basis, FX status, and control status split rows. State which
   identities are source-row versus aggregate invariants.

## Eligibility matrix required in the implementation

Define and test this matrix before emitting monetary totals. At minimum:

| Condition | Ground-up source | Gross source | Net source | GBP measures | Required control |
|---|---|---|---|---|---|
| Null participation | Include | Use 1.0 | Include | Convert only with valid FX | default count |
| Malformed / <0 / >1 participation | Owner-defined; do not silently coerce | Exclude or quarantine | Exclude or quarantine | Same eligibility as each measure | invalid count |
| Missing / invalid FX | Include source-currency measures | Include source-currency measures | Include source-currency measures | Null or quarantine; never zero | missing/invalid and conflict counts |
| Malformed non-null TIV component | Owner-defined whole-row rule | Same | Same | Same | invalid-TIV count |
| Ambiguous LOB mapping | Do not multiply | Do not multiply | Do not multiply | Do not multiply | ambiguous count |

`ControlStatus` needs an explicit finite vocabulary and precedence. A null
participation is not the same state as malformed participation. A valid selected
FX rate does not erase evidence of conflicting, malformed, null, zero, or
negative raw FX records.

## Equations for an approved uncapped revision

```text
GroundUpSource = sum(valid TIV components)
GrossSource    = GroundUpSource * ParticipationFactor
NetSource      = GrossSource * RetentionFactor
GroundUpGBP    = GroundUpSource * RateToGBP
GrossGBP       = GrossSource * RateToGBP
NetGBP         = NetSource * RateToGBP
```

Each equality is a row-level identity. At an aggregate grain, reconcile using
the sum of the eligible row measures; do not expect a single aggregate
participation factor to reproduce it.

## Mandatory validation

- Prove one output source row per OED input row before level expansion; report
  row/account/location counts before and after every join.
- Validate one positive, non-conflicting FX rate per currency, with raw record,
  valid-rate, conflict, and exception counts.
- Test null, malformed, negative, out-of-range, duplicate-normalised mapping,
  and conflicting-FX fixtures.
- Emit a versioned compatibility decision if replacing `NA_EQ` with `NAEQ`.
- Compare only genuinely common populations/measures with EDM/Python. The
  current Python route is peril-selected, deductible-thresholded, policy-capped
  PML and has no participation measure; it is not an uncapped comparator.

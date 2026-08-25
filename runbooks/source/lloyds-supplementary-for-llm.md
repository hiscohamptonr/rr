# Lloyd's supplementary — LLM calculation and workbook validation contract

This is a technical record of the checked-in workbooks and source evidence. It
does not supply the missing approved methodology, proxy, source transformation,
mapping, or rate decision. Follow the stop conditions in
[lloyds-supplementary.md](lloyds-supplementary.md).

## Source contract

The received S33 workbook is evidence, not a direct input. Its sheets are
`Weather`, `Quake`, and `EU exposure - weather & quake`; they contain 27
event/location columns, not the 13/18 SQL-shaped columns expected by the
calculation workbooks. It has no source county for California, no CRESTA field
for South Africa/EU, and no separate EU earthquake population. Never invent
these values. Select one approved branch:

```text
SQL branch: exact approved query/version, parameters, snapshot, schema and headers
Transformation branch: approved producer, mapping versions, grouping keys,
                       source-to-output reconciliation and exception treatment
```

The S33 shared formula uses a percentage-point cession:

```text
HIS net QS = Share Insured Value USD * (1 - RI Cession PC / 100)
```

For example, 50 means 50%, not a decimal factor of 50.

## Observed workbook mechanics and hard stops

| Workbook | Current observed calculation | Do not proceed until |
|---|---|---|
| RoW | M = `TSI_NET` (I) × L, yet M/report are labelled USD; four pivots end at row 4,988 | source column/unit, scale-factor source, and dynamic pivot range are approved |
| South Africa EQ | T = gross source `TSI` (O) × S; report labelled USD; blank zones vanish; `SUMIF` ends at row 53 | gross/net and currency source, dynamic range, and unmapped-zone quarantine are approved |
| California WF | M is USD-net and current cached arithmetic reconciles | wildfire proxy/source and non-current report date are approved |
| EU CRESTA | EQ T uses USD-net × S; populated flood T rows inconsistently use source net (P) or USD net (R), then U = T × `Fx!C7`; report `SUMIFS` are whole-column | one uniform formula, FX direction/date, full formula coverage and CRESTA exception treatment are approved |

`Fx!C7` is `1.25 / 1.21`, not the email's GBP/EUR 1.15 rate. It cannot be
silently substituted: obtain the approved base currency and rate direction.
Do not fill down an arbitrary existing EU flood formula.

## SQL implementation controls

The checked-in SQL joins policy via `ACCGRPID`; policy/portfolio multiplicity
can multiply coverage before aggregation. It multiplies `VALUEAMT` by
`blanlimamt` when nonzero, which must be proven to be an approved dimensionless
factor rather than a monetary limit. It reads FX dynamically, uses broad
portfolio `LIKE '%33%' OR LIKE '%3624%'`, and current `_QS`/`_SRP` `LIKE`
patterns use wildcard `_`. Before use, validate:

1. source row/TIV totals before and after each policy/portfolio join;
2. one approved policy grain and allowed portfolio list;
3. literal suffix/retention matching and decimal rate precision;
4. frozen FX snapshot, source/target currency and unit; and
5. query output headers, row count and total against target workbook schema.

## Required per-report reconciliation

For each peril/report, define the eligible predicate and enforce:

```text
included report total + approved excluded/unmapped total = approved core total
```

Record grouping key, key normalisation, report/range end row, source and target
units/currency, rate, scale factor, expected class allocation, absolute and
relative tolerance. Any missing county/CRESTA/peril/classification, unmatched
report key, mixed formula pattern, stale link, `#REF!`, no formula coverage, or
identical cross-peril fingerprint without proxy approval is a hard stop.

Use one controlled, access-restricted working copy per run and writer. Retain
input/output hashes and provenance, never commit regulated extracts, and record
every external-template transfer with source range, target green/yellow input,
value, basis, unit, currency, preparer, reviewer, and approval identifier.

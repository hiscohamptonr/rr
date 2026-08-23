# Lloyd's supplementary returns

## Scope and evidence

The repository implements this workflow as four root-level T-SQL files to run
directly against a SQL Server exposure data model (EDM). The queries return
aggregated result sets; they do not create or update a workbook.

- [`Supplementary Info - Workings - ROW Aggs - SQL.sql`](../../Supplementary%20Info%20-%20Workings%20-%20ROW%20Aggs%20-%20SQL.sql)
- [`Supplementary Info - Workings - South Africa EQ - SQL.sql.txt`](../../Supplementary%20Info%20-%20Workings%20-%20South%20Africa%20EQ%20-%20SQL.sql.txt)
- [`SouthAfrica_Aggs.sql`](../../SouthAfrica_Aggs.sql)
- [`FA_California_Aggs.sql`](../../FA_California_Aggs.sql)

The two South Africa files are byte-for-byte identical (SHA-256
`41d18412e0e46c8ab6a62613e23adcee09f18e07f4a9d448b3f4f57b90d1459a`),
so run one of them, not both. Reachable Git history contains only their initial
repository commit dated 2026-08-21; it supplies no older query version. No
`.xlsx`, `.xlsm`, `.xls`, `.xlsb`, `.ods` or `.csv` file is present in the
working tree, including ignored files, or in reachable Git history. The
approved supplementary workbook, its mappings and its final-output logic are
therefore external prerequisites and cannot be verified here.

The ROW and California file comments are dated `11.2.2026` and say the scripts
were edited for the 2026 EDM to apply Fine Art QS based on portfolio name. The
executable code in all four files also contains the SRP branch documented
below; the South Africa copies contain no equivalent edit comment.

The filenames and output aliases are not evidence of regulator definitions.
In particular, the repository does not define what the numeric peril/policy
codes, portfolio fragments, currency factors or geography fields mean. Obtain
approval against the current EDM data dictionary, reporting instructions and
return scope before using the results.

### Terminology used in this guide

| Term | Meaning established by the available evidence |
| --- | --- |
| EDM | The annual SQL Server exposure data model database named by each script's `USE` statement |
| FX | Foreign-exchange factors read from `RMS_USERCONFIG.dbo.currfx` |
| TSI fields | SQL output aliases `TSI`, `TSI_NET`, `TSI_GBP` and `TSI_USD_NET`; the repository does not define the expansion of “TSI” |
| QS / SRP | Fine Art factor categories identified only by `PORTNUM` patterns and script comments; the abbreviations and business terms are not defined here |
| Supplementary workbook | The external, controlled workbook into which reviewed query results are copied; it is not in the repository |

### Reporting-cycle values requiring approval

| Value | What must be approved before the run |
| --- | --- |
| Source database | The SQL Server, annual EDM name, as-of date, roll-up and schema/version; the two hard-coded database variants must not be assumed equivalent |
| Selection codes | Numeric `PERIL` and `POLICYTYPE` meaning for the chosen extract |
| Entity scope | Legal entities/portfolios actually selected by the `33` and `3624` substring matches |
| Geography | Current inclusion/exclusion rule, especially a complete country rule for ROW |
| FX basis | Rate-set date, uniqueness, factor direction, USD base and GBP/source-currency factors |
| Fine Art net factors | Which `PORTNUM` values are QS, SRP or other, and approval of `0.5`, `0.33333` and `1.0` |
| Blanket-limit factor | Intended unit and treatment of zero, null, negative and other `pol.blanlimamt` values |
| Workbook handoff | Approved workbook/template version, SQL-to-input mapping, downstream calculation/refresh behavior and final cells |
| Controls | Independent source totals, reporting precision, reconciliation tolerance and named approver |

## Choose the query

| Intended extract | File to execute | Hard-coded EDM database | Active selection |
| --- | --- | --- | --- |
| Rest of World (ROW) | `Supplementary Info - Workings - ROW Aggs - SQL.sql` | `HISCO_UKEU_01JAN2026_010126_ROLLUP_KEEP_EDM` | `PERIL = 3`; `POLICYTYPE = 3`; `PORTNAME` contains `33` or `3624`; **no active geographic predicate** |
| South Africa | Either South Africa file (they are identical) | `HISCO_UKEU_01JAN26_010126_ROLLUP_ByLOB_GC_v25_EDM` | `PERIL = 1`; `POLICYTYPE = 1`; `loc.cntrycode = 'ZA'`; `PORTNAME` contains `33` or `3624` |
| California | `FA_California_Aggs.sql` | `HISCO_UKEU_01JAN26_010126_ROLLUP_ByLOB_GC_v25_EDM` | `PERIL = 4`; `POLICYTYPE = 4`; `loc.cntrycode = 'US'`; `loc.statecode = 'CA'`; `PORTNAME` contains `33` or `3624` |

The portfolio predicate is exactly
`PORTNAME LIKE '%33%' OR PORTNAME LIKE '%3624%'`. It is a substring match, not
an enumerated legal-entity list. The meanings and continued validity of `33`
and `3624` are not recorded. In the South Africa query, the commented-out
portfolio exclusions and United States predicate are inactive.

The ROW label is especially important to challenge: the SQL does not exclude
South Africa, California, the United States or any other geography. Its inner
join to the geography database only requires `loc.COUNTRY` to match an
`RMS_GEOGRAPHY.dbo.country.ISO2A` row; that is not a ROW exclusion rule. Do not
use it as a ROW return until an approved geographic definition has been
reconciled to the selected countries.

## Shared joins and calculations

All three distinct queries join:

```text
loccvg -> loc (LOCID) -> property (LOCID) -> accgrp (ACCGRPID)
                                      accgrp -> policy (ACCGRPID)
                                      accgrp -> portacct (ACCGRPID)
                                      portacct -> portinfo (PORTINFOID)
loccvg.LIMITCUR -> RMS_USERCONFIG.dbo.currfx.CODE
```

ROW and South Africa also inner-join `RMS_GEOGRAPHY.dbo.country` on
`geo.ISO2A = loc.COUNTRY`; California does not use that table. These are inner
joins, so unmatched location, account, policy, portfolio, currency or (where
used) geography records disappear from the result.

For each joined row, define only as shorthand for the literal SQL:

```text
B = loccvg.VALUEAMT * CASE WHEN pol.blanlimamt = 0
                           THEN 1 ELSE pol.blanlimamt END
FGBP = currfx.XFACTOR from the separate row where CODE = 'GBP'
FCUR = currfx.XFACTOR from the row where CODE = loccvg.LIMITCUR
Q = 0.5     when portnum matches both '%_QS'  and '%_FA_%'
    0.33333 when portnum matches both '%_SRP' and '%_FA_%'
    1.0     otherwise
```

Every script then calculates:

| Output | Literal calculation | Interpretation requiring approval |
| --- | --- | --- |
| `TSI` | `SUM(B)` | Unconverted/gross-labelled amount at the query's currency grain |
| `TSI_NET` | `SUM(B * Q)` | Source-currency amount after only the scripted Fine Art factor |
| `TSI_GBP` | `SUM(B * FGBP / FCUR)` | GBP-labelled amount; the `currfx.XFACTOR` basis is not documented |
| `TSI_USD_NET` | `SUM(B / FCUR * Q)` | USD/net-labelled amount; the USD-base interpretation is not established by the repository |

`Q` affects `TSI_NET` and `TSI_USD_NET`, but not `TSI` or `TSI_GBP`. The factors
are exact script constants, not documented treaty terms. Approve `0.5` for QS
and `0.33333` for SRP for the reporting period. The SQL `LIKE` underscore is a
single-character wildcard, not a literal underscore, so `'%_QS'` and
`'%_FA_%'` can match more portfolio numbers than their visual spelling
suggests. Profile the actual `PORTNUM` values assigned to each factor.

The variable named `@GBPUSD` actually receives the `XFACTOR` for `CODE = 'GBP'`.
The scripts do not pin the currency table to a date or rate set. Confirm that
there is exactly one approved GBP row, exactly one non-null/non-zero row for
every selected `LIMITCUR`, and that the table's factor direction supports both
published output labels. A duplicate GBP row makes the scalar subquery fail;
duplicate currency-code rows can multiply results through the join.

## Query inventory

### Rest of World

**Selection and dependencies.** This query uses the `...ROLLUP_KEEP_EDM`
database, unqualified codes `PERIL = 3` and `POLICYTYPE = 3`, and the common
portfolio predicate. It uses both `RMS_USERCONFIG.dbo.currfx` and
`RMS_GEOGRAPHY.dbo.country`. It has no geographic `WHERE` condition.

**One result row is grouped by:**

- `poi.PORTNAME`;
- location country code and the matched geography-country label;
- `accgrp.ACCGRPID` and `accgrp.ACCGRPNUM`; and
- `loccvg.LIMITCUR`.

**Output fields, in order:** `PORTNAME`, blank `Reclassification`,
`Countrycode` (`loc.country`), `COUNTRY` (geography label), `accgrpid`,
`ACCGRPNUM`, `Currency` (`LIMITCUR`), `TSI`, `TSI_NET`, `TSI_GBP`, and
`TSI_USD_NET`. Results are ordered by portfolio, country code and geography
country label.

### South Africa

**Selection and dependencies.** Both copies use the `...ByLOB_GC_v25_EDM`
database, unqualified codes `PERIL = 1` and `POLICYTYPE = 1`, the common
portfolio predicate, and `loc.cntrycode = 'ZA'`. They use both shared reference
databases. The geography join nevertheless uses `loc.COUNTRY`, not
`loc.cntrycode`.

**One result row is grouped by the following expressions:**

- `poi.PORTNAME`, `loc.COUNTRY`, and `geo.Country`;
- `prop.ACCGRPID`, unqualified `ACCGRPNUM`, unqualified `ACCGRPNAME`,
  `accgrp.USERTXT2`, and unqualified `CEDANTID`;
- latitude, longitude, CRESTA, city, state, address-match value, county and
  `Zone3Name`; and
- unqualified `LIMITCUR` plus `loccvg.VALUECUR`.

Several group keys are not returned, so separate groups can look identical in
an export. `ACCGRPNAME`, `CEDANTID` and `LIMITCUR` are unqualified and depend on
the annual schema resolving them as intended. The selected field labelled
`LIMITCUR` is actually `loccvg.VALUECUR`, while the FX join uses
`loccvg.LIMITCUR`; both are group keys. Confirm that distinction before using
the currency column.

**Output fields, in order:** `PORTNAME`, blank `Reclassification`,
`Countrycode` (`loc.country`), `COUNTRY` (geography label), `CITY`, `cresta`,
`COUNTY`, `STATE`, `latitude`, `longitude`, `ADDRMATCH`, `Zone3Name`,
`ACCGRPNAME` (`accgrp.USERTXT2`), `LIMITCUR` (actually `loccvg.VALUECUR`),
`TSI`, `TSI_NET`, `TSI_GBP`, and `TSI_USD_NET`. Results are ordered by
portfolio, country code and geography-country label.

### California

**Selection and dependencies.** This query uses the `...ByLOB_GC_v25_EDM`
database, unqualified codes `PERIL = 4` and `POLICYTYPE = 4`, the common
portfolio predicate, and the combined location predicate
`loc.statecode = 'CA' AND loc.cntrycode = 'US'`. It uses the currency database
but has no geography reference-table join.

**One result row is grouped by:**

- `poi.PORTNAME`;
- `loc.cntrycode`, `loc.COUNTRY`, `loc.statecode`, `loc.county` and
  `loc.cresta`;
- `accgrp.ACCGRPID` and `accgrp.ACCGRPNUM`; and
- `loccvg.LIMITCUR`.

**Output fields, in order:** `PORTNAME`, `cntrycode`, `COUNTRY`, `statecode`,
`county`, `cresta`, `accgrpid`, `ACCGRPNUM`, `Currency` (`LIMITCUR`), `TSI`,
`TSI_NET`, `TSI_GBP`, and `TSI_USD_NET`. The script defines no `ORDER BY`, so
result order is not guaranteed.

## Material query risks

- **Annual database names are hard-coded and inconsistent.** ROW points to a
  `01JAN2026 ... ROLLUP_KEEP` database; South Africa and California point to a
  `01JAN26 ... ByLOB_GC_v25` database. A successful run does not prove either
  is the approved reporting-period EDM.
- **Code semantics are unverified.** The repository proves the numeric
  `PERIL`/`POLICYTYPE` values and string predicates, not their business meaning
  or regulatory suitability.
- **ROW is not geographically bounded.** Its name must not substitute for an
  explicit, approved inclusion/exclusion set.
- **Joins can multiply exposure.** `property`, `policy` and `portacct` are
  joined through location/account keys before aggregation. If any relationship
  is one-to-many, independent child rows may form a many-to-many product and
  inflate the sums. The repository contains no cardinality rule proving that
  this is safe, and `GROUP BY` does not undo multiplied amounts.
- **Reference inner joins can omit data.** Missing or mismatched FX/geography
  codes silently remove source rows; duplicate reference rows can multiply
  them.
- **Blanket-limit behavior needs validation.** A zero `blanlimamt` becomes a
  multiplier of one; every other value is used directly as a multiplier. The
  repository does not explain the units or intended treatment of null,
  negative or non-unit values.
- **Currency labels may overstate what is proven.** Rate date, factor direction
  and USD base are not encoded. South Africa also labels `VALUECUR` as
  `LIMITCUR` while joining FX on the actual `LIMITCUR`.
- **Portfolio `LIKE` patterns are broad.** Entity fragments and Fine Art
  patterns are substring/wildcard tests rather than controlled lookup tables.
- **Floating-point calculations and `0.33333` are approximate.** Agree the
  reporting precision and rounding treatment before workbook handoff.

## Controlled execution procedure

### Pre-run

1. Obtain the current Lloyd's instructions, approved supplementary workbook,
   reporting date, entity/geography scope and reviewer-approved tolerance. Do
   not infer them from a filename.
2. Select exactly one query from the table above. Record its repository commit
   and file hash. For South Africa, designate one duplicate as the controlled
   copy and do not combine their outputs.
3. In SQL Server, confirm the approved annual EDM database and schema. Treat
   each hard-coded `USE` name as a value to approve for this run, not as a
   permanent default. Confirm access to `RMS_USERCONFIG` and, for ROW/South
   Africa, `RMS_GEOGRAPHY`.
4. Approve the numeric peril/policy codes, the actual portfolios matched by
   `33`/`3624`, the geographic predicate, the Fine Art `PORTNUM` assignments
   and the QS/SRP factors. For ROW, supply and evidence the expected included
   and excluded countries before execution.
5. Snapshot or otherwise evidence the approved currency-rate set. Check one
   GBP row and one non-null, non-zero `currfx` row per selected `LIMITCUR`.
6. Measure source rows, distinct locations/accounts/policies/portfolios, and
   row counts after each join. Resolve unmatched reference records and any
   unexplained join expansion before summing.

### Run

1. Open the controlled file as a complete batch in an approved SQL Server query
   client connected to the server hosting the annual EDM. Do not paste together
   clauses from different extracts.
2. After the pre-run approvals, execute the batch. The script performs only
   `USE`, `DECLARE`, `SET` and `SELECT`; capture the full result set, SQL
   messages, execution time, server/database identity and row count.
3. Preserve the raw output without manual sorting, deduplication or adjustment.
   Because the California script has no guaranteed order, use field names and
   keys rather than row position in downstream handling.

### Post-run and workbook handoff

1. Complete the reconciliation checklist below and obtain reviewer approval.
2. Obtain the controlled supplementary workbook externally. Verify its
   reporting period, input tab/column mapping, formulas, pivots or queries,
   calculation mode and final-output cells; none can be inspected in this
   repository.
3. Copy/import only the reviewed raw result into the mapped input area. Record
   any transformation or manual adjustment separately; do not overwrite the
   raw SQL evidence.
4. Recalculate/refresh the workbook, trace samples from SQL rows to final
   reported cells, reconcile workbook inputs and outputs to the approved SQL
   totals, and obtain final sign-off.
5. Archive the exact SQL, raw result, run metadata, rate evidence,
   reconciliations, approved workbook and submission evidence together under
   the applicable records policy. See [Controls and evidence](controls.md).

## Evidence and reconciliation checklist

Do not copy results into the supplementary workbook until each applicable item
is evidenced and approved:

- [ ] Server, hard-coded/resolved EDM database, EDM as-of date and roll-up
      version match the reporting period.
- [ ] `PERIL`, `POLICYTYPE`, `PORTNAME`, `PORTNUM` factor class and entity scope
      are approved from a source independent of the filenames.
- [ ] South Africa contains only the approved ZA population; California only
      the approved US/CA population; ROW countries agree to an explicit
      approved inclusion/exclusion list.
- [ ] Source-to-joined row counts, distinct locations/accounts/policies and
      portfolio memberships show no unexplained loss or multiplication.
- [ ] Unmatched and duplicate geography/FX codes are zero or explained, and
      the South Africa `VALUECUR`/`LIMITCUR` distinction is resolved.
- [ ] `TSI` totals reconcile independently by portfolio, geography, account and
      source currency to approved EDM/RiskLink controls.
- [ ] The gross-to-net movement reconciles by actual Fine Art QS (`0.5`), SRP
      (`0.33333`) and other (`1.0`) portfolio class; unexpected wildcard
      matches are resolved.
- [ ] `TSI_GBP` and `TSI_USD_NET` are independently recalculated from the
      captured, approved rates and agree at the approved precision.
- [ ] Detail rows sum to each required return total, with duplicate-looking
      South Africa groups and California's non-deterministic order handled by
      keys rather than visual position.
- [ ] Raw SQL row count and control totals equal the rows/values imported into
      the workbook; workbook formulas, refreshes and final output reconcile to
      those inputs.
- [ ] All differences are within a tolerance approved for this reporting cycle
      and have a documented explanation and reviewer sign-off.

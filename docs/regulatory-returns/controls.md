# Controls and evidence

## Data sources

- The exact SQL Server EDM snapshot recorded for the run.
- Any reference databases, mappings, rate sets, and controlled workbooks used by the selected process.
- Current regulator instructions and approved return templates held outside this repository.


Use this checklist for every regulatory-return execution. It does not replace
the regulator's current instructions or the team's approved control framework.

## Run record

Record these items before execution:

| Field | Required evidence |
| --- | --- |
| Return and reporting period | Return name, reporting date and template version |
| Operator and reviewer | Names and execution/review dates |
| Source EDM | SQL Server, database name, roll-up/version identifier and as-of date |
| Code | Repository commit and exact script path |
| Scope | Entities, portfolios, peril/policy codes and geography |
| Assumptions | Approved FX basis, retention factors, mappings and manual adjustments |
| Destination | Output path and final controlled workbook path |

Never put credentials or connection secrets in the run record or commit them to
this repository.

## Pre-run review

- Confirm the script points to the intended annual EDM. A successful connection
  is not evidence that the database is the correct period or version.
- Confirm `loccvg.PERIL` and `policy.POLICYTYPE` values against the current EDM
  data dictionary or an approved control total. The repository does not define
  the business meaning of the numeric codes.
- Confirm the entity/portfolio selection against the current return scope.
- Confirm geography using both code and expected row counts. Labels such as
  "Rest of World" or "South Africa EQ" do not make the SQL predicate correct.
- Confirm the currency table date/basis and the intended currencies for each
  output field.
- Confirm Fine Art QS/SRP retentions with the current reinsurance arrangement.
- For BSCR and PRA, freeze the approved working copies and inspect formulas,
  named ranges, pivot sources, external links, calculation mode, and green cells before use.

## Extract controls

Capture results at the following grains before relying on a grand total:

1. source coverage rows and distinct locations;
2. distinct accounts and policies;
3. rows after each one-to-many join, especially `property`, `policy`,
   `portacct` and `portinfo`;
4. gross and net amount by entity/portfolio;
5. amount by source currency and converted currency;
6. amount by report geography;
7. missing or unexpected entity, geography, FX and geocoding values.

A large increase in row count after an account-level join may multiply exposure.
Investigate it; do not assume the final `GROUP BY` removes duplication.

## Reconciliation

At minimum, reconcile:

- extracted gross totals to an independently produced EDM/RiskLink control;
- gross to net movement by retention category;
- source-currency totals to converted totals using the approved FX basis;
- sum of entity/geography detail to each reported total;
- SQL/CSV output to the values imported into Excel;
- workbook input ranges to final green-output cells; and
- final submitted values to the reviewed workbook.

Historical notes say an earlier aggregate was within 1% of a RiskLink output.
That is historical evidence only. This repository defines no current acceptance
tolerance; agree and record one for the reporting cycle.

## Spreadsheet controls

For BSCR and PRA workbooks:

- save a working copy before refreshing queries or pivots;
- list every input tab and its source file/query;
- refresh pivots and verify their source ranges include all rows;
- recalculate formulas and check for `#REF!`, `#N/A`, `#VALUE!` and stale
  external links;
- trace a sample from raw input through intermediate formulas to each green
  output area;
- compare green outputs before and after refresh and explain movements;
- record every manual adjustment separately; and
- archive the reviewed workbook without overwriting the input evidence.

The repository contains working and return workbooks, but their presence does
not establish approval. Compare each checked-in file with the controlled
reporting-cycle copy before calculation or submission.

## Completion evidence

Archive together:

- current return instructions and blank template;
- exact script/query and run record;
- raw SQL or CSV output;
- row-count and total reconciliations;
- completed workbook, including formula logic;
- explanation and approval of manual adjustments;
- reviewer sign-off; and
- final submitted values or submission receipt, subject to the applicable
  records policy.

## Stop conditions

Do not populate a return when any of these remain unresolved:

- the approved reporting-period workbook or template is unavailable;
- the EDM period/version is uncertain;
- peril, policy, entity or geography codes are unapproved;
- joins produce unexplained row multiplication;
- FX or retention assumptions cannot be evidenced;
- workbook formulas or green outputs cannot be traced; or
- reconciliation differences exceed the agreed tolerance.

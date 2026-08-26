# Run checks and evidence

Use these controls for every process in this handbook. They do not replace current regulator instructions, approved templates, or the team's control framework.

## Run record

Initialize and approve the run record before execution; complete execution,
review, and sign-off fields afterwards. Mark genuinely inapplicable fields
`N/A` with a rationale rather than fabricating workbook/FX/manual-handoff
evidence for a process that does not use them.

| Field | Required evidence |
|---|---|
| Process and period | Deliverable, reporting date, as-of date, and template/version |
| Operator and reviewer | Names and execution/review dates |
| Source system | Server, database, roll-up/version identifier, and source date |
| Code | Repository commit, exact script/query path, and complete command/parameters |
| Scope | Entities, portfolios, peril/policy codes, events, and geography |
| Assumptions | FX basis, retention factors, mappings, scale factors, and manual adjustments |
| Inputs | Source workbook/query result paths, tabs/ranges, row counts, totals, units, and currency |
| Destination | Output folder and controlled calculation/final workbook paths |
| Execution evidence | Exit status, stdout/stderr, warnings/errors, and expected-versus-produced artifact manifest |

Never put credentials, tokens, or connection secrets in the run record or source control.

## Source approval

- Confirm the source is the approved reporting-period version. A successful connection does not prove that the database is the correct annual EDM or roll-up.
- Confirm numeric peril and policy codes against the current EDM dictionary or approved controls. Repository defaults are not standing business definitions.
- Confirm entity, portfolio, event, and geography scope against the current deliverable.
- Confirm source and target currency, FX date/basis, and output unit.
- Confirm `_QS`, `_SRP`, and other retention or proxy decisions against current approved terms.
- Keep source workbooks and instruction emails together so provenance and interpretation are retained.
- Use an approved restricted location for source data, extracts, workbooks, and
  correspondence. Do not commit raw regulated data, run outputs, or credentials
  unless retention and access controls explicitly permit it.

## Pre-run workbook review

Before replacing any data:

1. Make a controlled working copy and preserve the received/check-in source as evidence.
2. Inventory every input tab and identify its source query, script output, or workbook tab.
3. Record formulas, tables, named ranges, pivot sources, calculation mode, validation, external links, and designated input/green cells.
4. Capture pre-refresh row counts and output totals.
5. Confirm mappings, scale factors, FX, dates, units, and formula columns are the approved versions.
6. Resolve stale links and source-range uncertainty before refreshing.

## Extract controls

Capture checks at multiple grains rather than relying on a grand total:

1. source coverage rows and distinct locations;
2. distinct accounts and policies where available;
3. rows before and after one-to-many joins, especially `property`, `policy`, `portacct`, and `portinfo`;
4. gross and net amount by entity or portfolio;
5. amount by source and converted currency;
6. amount by report geography, peril, event, or CRESTA as applicable; and
7. missing or unexpected entity, geography, FX, geocoding, polygon, PML, and mapping values.

A large increase after an account-level join can multiply exposure. Investigate it; a final `GROUP BY` does not prove that duplication did not occur upstream.

## File-loading controls

- Preserve the raw CSV or SQL result and exact command/query used to produce it.
- Compare headers, column order, row count, gross/net totals, currency, and unit to the target range before pasting.
- Clear only controlled source rows; do not overwrite headers, formulas, scale factors, mappings, pivots, validation, or formatting.
- Fill formulas only through the complete new source range and inspect the first, last, blank, and exceptional rows.
- Confirm every table and pivot source includes all new rows and excludes stale rows.
- Never use a schema match alone as proof that cached workbook data came from a particular query run.

## Reconciliation

At minimum, reconcile:

- extracted gross totals to an independently produced EDM/RiskLink or approved source control;
- gross-to-net movement by retention category;
- source-currency totals to converted totals using the approved FX basis, where applicable;
- detail totals to entity, geography, event, peril, and report totals;
- raw output to grouped output;
- SQL/CSV output to the values loaded into Excel;
- workbook input ranges through formulas and pivots to report outputs, where applicable;
- reviewed outputs to every manually populated final cell, where applicable; and
- final submitted values to the reviewed workbook or output pack.

Historical notes that an earlier result was close to a model output are historical evidence only. This repository defines no current acceptance tolerance. Agree, document, and apply the reporting-cycle tolerance.

## Spreadsheet validation

- Refresh only approved queries, tables, and pivots; do not blindly update stale external links.
- Force recalculation when required and check `#REF!`, `#N/A`, `#VALUE!`, blanks, and stale cached values.
- Trace representative records from raw input through formulas to each final report area.
- Compare pre/post-refresh outputs and explain every material movement.
- Record manual adjustments separately with rationale and approval.
- Preserve template formulas, validation, structure, and non-input cells.
- Archive the reviewed workbook without overwriting raw input evidence.

## Manual handoff

For every value copied into an external template, record:

- source query/script and version;
- source workbook, sheet, and exact cell/range;
- mapping, scale-factor, retention, and FX versions;
- destination workbook, sheet, and cell;
- value, gross/net basis, currency, unit, and as-of date; and
- preparer, reviewer, and review date.

A workbook's presence in the repository does not establish approval. Compare it with the controlled reporting-cycle copy before calculation or submission.

## Completion evidence

Archive together, in a new run-specific location (never by overwriting an
earlier run):

- current instructions and blank/controlled template;
- complete run record and repository revision;
- exact script/query and command;
- raw and grouped outputs;
- row-count, gross/net, FX, and report reconciliations;
- completed calculation workbook with formula logic preserved;
- approved mappings, scale factors, proxy decisions, and manual adjustments;
- reviewer sign-off; and
- final output/submission evidence, subject to the applicable records policy.

Record a stable source snapshot or approved change window when more than one
query/read is required. Also retain the executed-file hash or clean-tree/diff,
lockfile/environment and driver version, workbook application version, and
file checksums where available.

## Stop conditions

Stop and escalate when any of these remain unresolved:

- approved instructions, source, or reporting-period template are unavailable;
- the server, database period/version, event set, or source workbook lineage is uncertain;
- peril, policy, entity, portfolio, proxy, or geography scope is unapproved;
- joins produce unexplained row multiplication;
- FX, retention, scale factors, mappings, currency, units, or dates cannot be evidenced;
- formulas, pivot sources, external links, or final output cells cannot be traced;
- expected source and workbook totals do not reconcile; or
- differences exceed the agreed tolerance.

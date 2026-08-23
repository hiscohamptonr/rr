# PRA January/February return

## Status and reproducibility conclusion

The repository preserves a short description of an Excel-led process, but not
the process itself. The expected `PRA_BSCR_Aggs` workbook and the
`Region_mappings` lookup are absent from both the current working tree and all
reachable Git history. There is no executable Prudential Regulation Authority
(PRA) implementation under [`pra/`](../../pra/). Consequently, the repository
can recover the historical sequence and its control points, but **cannot
reproduce the calculation or a submission-ready PRA workbook**.

Do not rebuild the workbook from the prose alone or substitute one of the
repository SQL files without establishing provenance. The formulas, pivot
configuration, mapping contents, output-sheet layout and final PRA format are
not specified in enough detail to do that safely.

## Evidence and artifact search

The primary note exists as three byte-identical tracked copies:

- [`pra/readme3.md`](../../pra/readme3.md);
- [`docs/readme.md`](../readme.md); and
- [`docs/readme3.md`](../readme3.md).

Git history shows that `pra/readme.md` was added in the initial reachable commit,
then renamed to `docs/readme.md`; the other two copies were added later. The
copies add no independent corroboration or missing detail.

The artifact investigation covered:

- a Git-ignore-disabled working-tree search for `.xlsx`, `.xlsm`, `.xls`,
  `.xlsb`, `.ods` and `.csv` files;
- working-tree searches for `PRA_BSCR_Aggs`, `Region_mappings` and filename
  variants containing `region` or `mapping`; and
- filenames and objects reachable from every local and remote Git ref.

No workbook, spreadsheet, CSV mapping or `Region_mappings` file was found. No
reachable historical path has the expected workbook or mapping name. The
current [`.gitignore`](../../.gitignore) excludes `*.xlsx` and `*.csv`, so their
absence from Git does **not** prove that an operator never held them locally; it
does prove that neither artifact is recoverable from this repository or its
reachable history. The note does not give either artifact an extension,
location, schema, owner or version.

## What the historical notes actually establish

The following is a transcription of the recoverable process, not a claim that
its calculations remain current or correct:

1. The process was used for a PRA return described only as the
   "January/February" return, with an estimated run time of three hours.
2. Open the workbook identified by the stem `PRA_BSCR_Aggs`.
3. Open its `sql` tab and point the extraction at the relevant exposure data
   model (EDM).
4. Run the embedded SQL against an EDM in the exact format received from GC.
   The author explicitly says the SQL was not made generic.
5. Apply `Region_mappings` to map source data to PRA regions.
6. Move to the green-coloured tabs. The note says these tabs run slow,
   convoluted formulas and split the data by class and `FA` into pivot tables on
   the right-hand side of the sheets.
7. Format the resulting data into the required PRA format.

The notes do not define `FA`, identify sheet names other than `sql`, state how
the SQL is executed, list formula ranges, describe pivot fields or filters,
define the green colour, provide regional mapping rules, or identify the PRA
template and its required formatting. Green is therefore only a historical
navigation cue; it is not evidence that a sheet has passed review or is ready
for submission.

## Contradictions and limits in the evidence

- The note's metadata says its purpose is to "Produce aggregates for BSCR",
  while its introduction says the folder produces the PRA January/February
  return. The combined workbook name reinforces that overlap. The repository
  does not resolve whether one workbook served both returns or whether the
  metadata was copied incorrectly.
- [`docs/bscr_guide.md`](../bscr_guide.md) says the BSCR query was exactly the
  same query as the PRA query. The missing workbook SQL tab prevents that claim
  from being checked. The present repository is not internally uniform:
  [`aggregates/aggs-from-edm.sql`](../../aggregates/aggs-from-edm.sql) filters
  `peril = 2` and `policytype = 2`, whereas the inline query in
  [`bscr/BSCR_UKEU.py`](../../bscr/BSCR_UKEU.py) filters `peril = 1` and
  `policytype = 1`. Neither file has evidence identifying it as the missing PRA
  SQL tab. They are comparison material, not drop-in replacements.
- The PRA note says the extract was within 1% of a RiskLink aggregate tool's
  total sum insured (TSI). The BSCR guide describes the result only as similar
  but not identical and acknowledges uncaptured policy terms. No run date,
  input dataset, control output, reconciliation, approved tolerance or
  treatment of the residual is present. This is historical assurance, not a
  current acceptance criterion.
- "Required PRA format" is not defined. The final regulator template,
  instructions, reporting date, units, sign conventions and submission
  mechanism must come from approved sources outside this repository; they
  cannot be inferred from the note.

## Dependencies that must be recovered

### Required to execute the historical calculation

1. The approved `PRA_BSCR_Aggs` workbook in its native format, including its SQL
   tab, formulas, pivot caches and configuration, formatting, and any
   connections or external links.
2. The exact `Region_mappings` artifact used for the reporting cycle, including
   its key columns and PRA-region values. The repository does not establish its
   file type or layout.
3. The intended GC-supplied EDM and authorized access to the SQL Server that
   hosts it. Its schema must match what the recovered SQL expects.
4. A spreadsheet application and database connectivity compatible with the
   recovered workbook. Whether macros, Power Query or another connection
   mechanism are involved cannot be known until the workbook is inspected.

### Required for the final handoff

1. The current, approved PRA template and instructions for the relevant entity
   and reporting period.
2. Approved reporting-cycle decisions for regional mapping, class/`FA`
   treatment and any adjustments not encoded in the recovered workbook.
3. A current independent control source and an approved reconciliation
   tolerance. A prior RiskLink comparison may be useful evidence if recovered,
   but the undocumented historical 1% result is not itself approval.
4. Reviewer and submission-owner sign-off under the organisation's current
   governance process.

These are external prerequisites, not files claimed to exist in this
repository.

## Safe recovery and execution checklist

### 1. Recover and preserve the artifacts

- Obtain the workbook and mapping from an approved archive or process owner;
  record their source, reporting-cycle applicability, filenames and hashes.
- Preserve received copies read-only and perform the run in dated working
  copies. Do not save over the only recoverable workbook.
- Scan the workbook in the organisation's controlled environment before
  enabling data connections or active content.
- Confirm that the native workbook still contains the `sql` tab, green-coloured
  processing/output tabs, formulas, pivots and all referenced ranges. Record
  broken external links, missing named ranges and calculation errors before
  changing anything.

**Recovery gate:** stop if the workbook, mapping, current PRA template or
applicable EDM cannot be identified. The prose and repository SQL are not a
safe substitute.

### 2. Establish calculation provenance

- Extract and retain the exact SQL text from the workbook's `sql` tab.
- Identify how that SQL is executed and record the actual server, database and
  EDM snapshot selected for the run. Confirm that it is the intended GC EDM,
  not merely a database with similar tables.
- Compare the recovered query with related repository queries and the prior
  approved workbook, if available. Investigate every difference rather than
  choosing the closest-looking SQL.
- Review hard-coded peril and policy selections, portfolio/class logic,
  geography fields, limits and deductibles, currencies, and aggregation grain
  with a qualified owner. The repository does not supply approved PRA
  definitions for these items.

### 3. Validate the lookup and extraction

- Confirm the workbook points to the recovered `Region_mappings` version and
  not a stale local or network path.
- Check mapping-key uniqueness, blank keys, unmapped source values and
  unexpected many-to-many joins. Have the reporting owner approve all mapping
  changes; do not silently assign unknown values to a region.
- Before refresh, capture prior row counts, totals and workbook calculation
  state where available. After extraction, record query completion, source row
  counts and control totals so an empty, truncated or duplicated result cannot
  pass unnoticed.

### 4. Recalculate formulas and pivots

- Use a working copy and enable only the reviewed connection or active content
  required by the recovered process.
- Refresh the SQL result, force a full workbook recalculation, then refresh each
  pivot on every green-coloured tab. Do not assume opening the file refreshes
  either formulas or pivots.
- Inspect formula continuity, errors, stale external links, pivot source ranges,
  filters and excluded blank or unmapped categories. Verify that all refreshed
  source rows are represented in the class/`FA` outputs.
- Reconcile totals through each boundary: EDM extract to mapped data, mapped
  data to formula results, formula results to pivots, and pivots to final PRA
  values. Agree and document tolerances before accepting differences.

### 5. Produce and hand off the final workbook

- Populate the current approved PRA template from the reviewed green-tab
  outputs, following the current instructions rather than copying historical
  layout assumptions.
- Perform a second-person review of source period and entity, mappings, formula
  and pivot refresh status, units, totals, adjustments, and the final template.
- Retain the native calculation workbook; do not replace the only formula and
  pivot evidence with a values-only export.
- Archive together: the final submitted PRA workbook, the completed
  `PRA_BSCR_Aggs` working copy, exact SQL, `Region_mappings`, source and output
  hashes, extraction evidence, reconciliations, exceptions, approvals, and the
  applicable regulator instructions and template.
- Apply the repository's [shared controls and evidence checklist](controls.md)
  in addition to the PRA-specific checks above.

## Material risks

| Risk | Why it is material | Required response |
| --- | --- | --- |
| Missing calculation artifacts | SQL, mappings, formulas and pivots cannot be inspected or rerun | Recover approved native artifacts; do not recreate them from prose |
| GC EDM schema dependence | The note says the SQL works only on the exact received format | Validate the actual schema and query joins before execution |
| Query identity ambiguity | PRA/BSCR notes conflict and current candidate queries use different hard-coded filters | Establish SQL provenance and approve every selection |
| Mapping drift | No region mapping values or version are recorded | Recover the cycle-specific mapping and test coverage and cardinality |
| Opaque class/`FA` logic | The formula ranges and pivot definitions are missing | Inspect, reconcile and independently review the recovered workbook |
| Stale spreadsheet state | Cached pivots, manual calculation or broken links can show plausible old values | Force refresh and recalculation and retain refresh evidence |
| Unsupported 1% comparison | The historical RiskLink result has no recoverable evidence or current tolerance | Define current controls and investigate differences; do not inherit 1% |
| Template drift | "Required PRA format" is unspecified | Use the current approved PRA template and instructions |

Until the recovery gate and these controls are satisfied, this guide is a
recovery runbook only, not an executable or approved PRA return procedure.

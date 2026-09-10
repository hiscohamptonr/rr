# Run checklist

[Start here](../README.md) · [Detailed controls for LLMs/reviewers](llm-instructions.md#detailed-run-controls)

Use this alongside your process guide. Keep the evidence in a new, restricted
run folder—not in source control. Mark irrelevant checks N/A with a reason.

## Before you start

- [ ] Confirm the reporting period, source snapshot, scope and controlled template.
- [ ] Confirm the approved mappings, retention/proxy rules, scale factors, FX and units.
- [ ] Record the operator, reviewer, code version, exact command/query and output folder. Keep credentials out of the record.
- [ ] Agree independent control totals and acceptable differences with the reviewer.
- [ ] For Excel, work on a copy. Identify input ranges, formulas, tables, pivot sources and external links before changing anything.
- [ ] Resolve the blockers listed in your guide before doing the affected step.

## Run and check

- [ ] Save the raw outputs, logs, parameters and row counts. Use a stable snapshot when running multiple queries.
- [ ] Check joins have not multiplied exposure; investigate missing mappings, geography, currency or other required values.
- [ ] Reconcile source → raw output → grouped output by relevant entity, peril and geography, including gross/net and FX movements.
- [ ] Before loading Excel, check headers/order, row counts, currency and units. Replace input rows only; preserve formulas and report areas.
- [ ] Extend approved formulas and table/pivot ranges to all new rows; remove stale input rows. Do not copy known inconsistent formulas or blindly refresh external links.
- [ ] Recalculate in Excel and reconcile report totals. Investigate errors, stale values and unexplained movements.

## Finish

- [ ] Use an approved source-to-destination map for any final-template transfer. Do not choose cells by colour or label alone.
- [ ] Log each transfer: source file/sheet/range, destination file/sheet/cell, value, measure, currency/unit, as-of date and assumption versions.
- [ ] Obtain reviewer sign-off and retain inputs, outputs, reconciliations, adjustments and final submission/delivery evidence together.

**Stop if** the source or assumptions are unapproved, a formula/pivot/handoff
cannot be traced, or differences exceed the agreed tolerance. A successful
command or refresh does not mean the return is complete.

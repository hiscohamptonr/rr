# BSCR Schedule X — offline operator guide

## Scope and result

This guide runs the BSCR calculation from an approved SQL export and produces reviewed exposure files; it does **not** produce a complete Schedule X return, final-cell submission, EP curves, premiums, narratives, model classifications, or distinct-contract counts.

The calculation PC needs Python 3.13+ and the repository only; Excel, `uv`, ODBC, and a live database connection are not required.  An approved SQL-export host remains responsible for producing the input CSV.

## Files and contract

All paths are relative to the repository root.  Each input folder is one approved snapshot with one approved peril and policy selection.

| File | Required contract |
|---|---|
| `bscr-source.csv` | Input file, with this exact header and order: `pml,accgrpid,uwritrname,state,userid1,branchname,cntrycode,is_geocoded` |
| `bscr-output.csv` | Script output, with this exact header and order: `cntrycode,bscr_entity,region,sum_pml,sum_net,count_policies,is_geocoded` |
| `bscr/sql/bscr-extract.sql` | Separate SQL-export query; its defaults are `@peril = 1` and `@policy_type = 1`, but the approved cycle values control the export |

The checked-in workbooks `bscr/workbooks/Workings_with_geocodingFW - Including blanks USD.xlsx` and `bscr/workbooks/2026 BSCR - UKEU - HIC.xlsx` are historical/reference files only; they are not calculation inputs, and this runbook does not require opening or refreshing them.

## Numbered operator steps

1. Create an input folder for one snapshot and peril/policy selection, such as `runs\eq\input`.
2. On the SQL-export host, run `bscr/sql/bscr-extract.sql` with the approved peril and policy values and save the result with headers as `bscr-source.csv` in that folder, retaining parameters and source totals.
3. From the repository root on the calculation PC, create the one-time environment with `python -m venv .venv` and Windows dependencies with `.venv\Scripts\python -m pip install -r bscr\requirements.txt`.
4. Ensure the output directory is absent or empty before starting and do not reuse it for another snapshot.
5. Run `.venv\Scripts\python bscr/BSCR_UKEU.py --input-dir runs\eq\input --output-dir runs\eq\output --process bscr` using the actual input and output folders.
6. Confirm that the run completes and that `runs\eq\output\bscr-output.csv` has the exact seven-column header and non-partial contents.
7. Reconcile source and output row counts, gross/net totals, entity and region totals, country/state frequencies, geocode splits, and unexplained nulls or unmapped values before review.
8. Retain the input CSV, output CSV, query revision and parameters, source controls, run command, code revision, reconciliation, exceptions, and reviewer record together as the run evidence.

For a combined run, use `--process both` and provide both required source files; `--process bscr` requires `bscr-source.csv`, while `--process pra` is documented by the shared script contract and is not needed for a BSCR-only run.

## Interpret the output safely

`sum_pml` is gross source-currency exposure before retention, `sum_net` applies the current Python retention logic, and `count_policies` is a contributing grouped/source-row count rather than a guaranteed distinct policy or contract count.  `ALL` and regional rows are overlapping views, so never add regional rows together or treat them as separate peril extracts.  A new peril selection requires its own approved SQL snapshot; changing a region filter is not a substitute for a separate peril extraction.

Record source currency explicitly: Python does not convert currency, and a USD-labelled historical workbook view does not make a source-currency CSV USD.  The historical workings workbook applied a hard-coded `1.35` conversion and `/1,000,000` scaling, but those workbook mechanics are not part of this offline CSV calculation.

## Stop conditions and current blockers

- Stop for a missing, partial, reordered, or extra-header input; a non-empty output directory; a failed run; a missing output; unexplained control-total differences; or unexplained join multiplication.
- The policy join is not proven to be policy-grain safe because `policyid` is omitted from downstream grouping; multiple policy/geography rows can multiply exposure, so review join diagnostics before relying on totals.
- The current `is_nahu()` implementation classifies every US row as NAHU because its intended state allow-list is bypassed; do not describe this as approved coastal-state logic.
- Retention remains `_QS = 0.50`, `_SRP = 0.3333`, otherwise `1.00`, with `_QS` taking precedence when both markers occur; source currency, FX direction, and annual rate approval remain open.
- Approval of all-peril codes and the final source snapshot is unresolved, so defaults are convenience values rather than cycle approval.
- The final HIC template has no approved source-to-cell map and cannot be inferred from labels, colours, cached values, or prior layouts; the checked-in template also contains documented formula/link defects.

The output is reviewed BSCR exposure input only.  Historical workbooks may be used for comparison after the CSV reconciliation, but they are optional and do not convert this run into an approved final return.

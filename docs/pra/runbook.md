# PRA offline runbook

## Operator steps

Use Python 3.13+ on the calculation PC; it does not need SQL Server access, ODBC, Excel or `uv`.

1. Create one input folder and one empty output folder for each approved snapshot and peril/policy selection, without mixing snapshots or scopes.
2. On the approved SQL Server, run `pra/sql/pra-raw.sql` with the recorded PRA defaults `@peril = 2` and `@policy_type = 2` unless the approved selection says otherwise.
3. Export the SQL result, including its header, as `<input-dir>/pra-source.csv` with exactly `pml,accgrpid,uwritrname,state,userid1,branchname,cntrycode` in that order.
4. On the calculation PC, create the one-time environment with `python -m venv .venv` and, on Windows, install dependencies with `.venv\Scripts\python -m pip install -r bscr/requirements.txt`.
5. From the repository root, run Windows with `.venv\Scripts\python bscr/BSCR_UKEU.py --input-dir runs\eq\input --output-dir runs\eq\output --process pra` or run macOS/Linux with `.venv/bin/python bscr/BSCR_UKEU.py --input-dir runs/eq/input --output-dir runs/eq/output --process pra`.
6. Confirm that the output directory was absent or empty before the run and that it now contains exactly `pra-raw.csv` and `pra-aggregate.csv` for a PRA-only run.
7. Check `pra-raw.csv` as the seven-column raw file and `pra-aggregate.csv` as the five-column file `pml,state,userid1,cntrycode,uwritrname`, then reconcile row counts, headers, totals, and approved tolerances.
8. Retain the SQL export, both output files, snapshot/peril/policy metadata, script and query revisions, mappings, and the reconciliation record before review.
9. Treat unexplained differences, partial files, malformed headers, mapping errors, currency or unit uncertainty, and policy-join cardinality or cross-product risk as stops.
10. Treat these files as reviewed internal calculation candidates only: no checked-in template or approved source-to-destination map establishes a final PRA return.

## Column boundary

| File | Columns | Use |
|---|---|---|
| `pra-source.csv` | `pml,accgrpid,uwritrname,state,userid1,branchname,cntrycode` (7) | Input exported by `pra/sql/pra-raw.sql` |
| `pra-raw.csv` | Same seven columns | Offline raw output and evidence |
| `pra-aggregate.csv` | `pml,state,userid1,cntrycode,uwritrname` (5) | Offline aggregate output |

Do not substitute an eight-column BSCR source for `pra-source.csv`, and do not paste a five-column aggregate where the script requires the seven-column raw input.

## All-peril runs

1. Put every separately approved all-peril export in its own directory, such as `runs/all-peril-<scope>/input/pra-source.csv`, with a matching empty output directory.
2. Keep the all-peril producer, population, peril code, policy code, currency, mappings, and approval evidence with that directory rather than combining it with the earthquake run.
3. Do not promote `1/1` or `4/4` to an approved all-peril scope: the repository does not resolve which population or scope those codes represent.
4. Run the same offline command with that folder's paths only after the source selection is established, and apply the same exact-file and reconciliation checks.

## Optional current workbook review

`pra/workbooks/PRA_Aggs.xlsx` is optional: it has only the two aggregate sheets and their three mapping sheets, not the former raw-data, BSCR-panel or SQL tabs.

1. Choose `pivot_eq` for earthquake or `pivot_allperil` for a separately confirmed all-peril input.
2. Clear old A:E data below row 1 and paste the five-column aggregate **with headers into A1**, leaving F:M and the report areas untouched.
3. Resize `Table32` (earthquake) or `Table3` (all-peril) through column M to the last pasted row and fill the correct F:M formulas down.
4. Set every earthquake pivot source to `Table32`—the retained cache initially points to `Table3`—and every all-peril pivot source to `Table3`, then check value fields, refresh those pivots and reconcile totals.

The four pivot titles are **Total PML / Fine Art**, **Portfolio / country / Fine Art**, **Country / Fine Art**, and **CDS class**; the banner identifies the peril and makes clear that `pml` is not automatically USD-converted.

## Former workbook reference

The former `PRA_BSCR_Aggs.xlsx` is available in repository history only; its raw sheet, SQL tab and BSCR panels were removed from the renamed workbook, and raw CSVs now remain separate audit files.

## Financial caveats

The SQL logic zeroes grouped value below `deductamt` without subtracting the deductible, retains equality, groups deductible and limit currencies without conversion, and has unresolved null/negative deductible, currency, limit, policy-join, and cross-product behaviour. Python's existing BSCR retention and geography discrepancies remain unchanged: the removed raw-sheet formulas used 33% SRP versus 0.3333 in Python. The optional PRA workbook still requires review of CDS/PRA-region `#N/A`, `Agg_USD = pml * 1.25`, and whether pivots should sum `pml` or `Agg_USD`.

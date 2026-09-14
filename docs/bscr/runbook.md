# BSCR — SQL, CSV and Python

## Run the calculation

1. Run `bscr/sql/bscr-extract.sql` against the correct EDM database, checking `@peril` and `@policy_type` for the required run (the file defaults to `1/1`).
2. Export the result as a CSV with these headers: `pml, accgrpid, uwritrname, state, userid1, branchname, cntrycode, is_geocoded`.
3. Copy the CSV to the calculation PC and open `bscr/BSCR_UKEU.py`.
4. Set the CSV filename and output folder at the top of the file using the example below, leaving `PRA_INPUT_CSV = None` for BSCR only.
5. Use a new or empty output folder so old and new results cannot be mixed.
6. Run `.venv\Scripts\python bscr/BSCR_UKEU.py` from the repository folder, with no arguments.
7. Open `bscr-output.csv` in the configured output folder and reconcile the `ALL` rows' gross totals and contributing-row counts to the source CSV.
8. Check retained/net totals, entity, geography and geocode splits, and investigate missing mappings or unexplained differences.
9. Save the input CSV, output, SQL parameters, database snapshot and reconciliation together.

## Set the paths

Replace these example paths at the top of the Python file:

```python
BSCR_INPUT_CSV = Path(r"C:\Returns\my BSCR extract.csv")
PRA_INPUT_CSV = None
OUTPUT_DIR = Path(r"C:\Returns\bscr-output")
```

The input path includes the **CSV filename**; the output path is a **folder**.

## One-time Python setup

Use Python 3.13+ and run these commands from the repository folder on Windows:

```text
python -m venv .venv
.venv\Scripts\python -m pip install -r bscr\requirements.txt
```

The calculation PC needs neither database access nor `uv`; SQL runs separately where database access is available.
On macOS/Linux use `.venv/bin/python` instead of `.venv\Scripts\python`.

## Check before using the output

- Keep source currency and units: the script does not convert to USD or millions.
- Do not add overlapping regional rows together or treat `count_policies` as distinct contracts.
- Confirm the existing retention rules (QS 50%, SRP 33.33%, QS first) and geography rules: the current hurricane flag includes every US row.
- Stop on failed/partial exports, unexplained totals or policy-join multiplication; workbooks are not needed for this calculation.

**To return to later:** agree where the exposure results go in the final HIC template and obtain the separate EP curves, premiums and contract counts; this CSV is not the complete BSCR return.

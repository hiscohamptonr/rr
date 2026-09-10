# BSCR Schedule X

[Start here](../../README.md) · [Run checklist](../operating-controls.md) ·
[Detailed LLM reference](technical-contract.md)

**Result:** reviewed exposure inputs for HIC Schedule X—not a complete return.
EP curves, premiums, narratives and distinct contract counts need other sources.

**Before production:** resolve policy joins, geography/retention/FX rules, the
static consolidation step and the HIC template defects and cell map.
See [BSCR-01–04](../decisions.md#bscr-01).

## 1. Get ready

Complete the [run checklist](../operating-controls.md). Confirm the approved
EDM snapshot, mappings, FX and peril/policy codes (`1/1` in the January setup).
You need SQL Server access with ODBC Driver 18 and integrated authentication.

Use working copies of:

- **Calculation:** `bscr/workbooks/Workings_with_geocodingFW - Including blanks USD.xlsx`
- **Final template:** `bscr/workbooks/2026 BSCR - UKEU - HIC.xlsx`—check against the approved current-cycle version.

## 2. Extract the data

Run from the repository root. Replace the placeholders; use a new run folder.

```bash
uv sync --locked
uv run python bscr/BSCR_UKEU.py \
  --server '<approved-server>' --database '<approved-edm>' \
  --peril 1 --policy-type 1 \
  --output '<run-dir>/bscr-output.csv' \
  --source-output '<run-dir>/bscr-source.csv'
```

Keep both CSVs and the run log. If the command fails or either file is missing,
do not load partial results.

## 3. Load the calculation workbook

1. Review `AUDIT_SUMMARY`, input ranges, formulas and pivot sources before editing.
2. Check the seven-column output header. Clear old input rows in `Sheet1!A:G`
   only, then paste `bscr-output.csv` data **without headers** from row 2.
3. Preserve and extend formulas H:K through the new rows. Check the workbook's
   `1.35` conversion and million-unit scaling against the approved FX/unit basis.
   `Sheet1` is not an Excel table; do not create one.
4. **Stop at `output!A:F`: it is static.** Loading `Sheet1` does not update it.
   Obtain the approved consolidation procedure, including grouping keys,
   aggregation, clearing old groups and reconciliation. Do not guess the bridge.
5. Rebuild `output` under that procedure, then refresh `piv` and recalculate.
   Do not blindly refresh external connections.

## 4. Check the results

- Reconcile the extract → `Sheet1` → rebuilt `output` → `piv`, including gross,
  net and contributing-row counts. Investigate missing mappings and Excel errors.
- Regional views **overlap**; do not add them together. `ALL` is a separate view.
- `count_policies` counts grouped source rows, **not distinct contracts**.
  It cannot supply Schedule X(f) on its own.
- Stop if the bridge, currency, source ranges or final cells cannot be traced.

## 5. Transfer and review

The calculation workbook and HIC template are not formula-linked. Transfer only
reviewed values to cells in an approved source-to-destination map. Do not choose
cells by colour or overwrite formulas and other non-input cells.

Use the run checklist to log each transfer and obtain reviewer sign-off.
A refreshed pivot is not a completed Schedule X return.

For formulas, historical totals and diagnostics, use the
[technical reference](technical-contract.md). For missing final mappings and
supplemental sources, use the [handoff trace](handoff.md).

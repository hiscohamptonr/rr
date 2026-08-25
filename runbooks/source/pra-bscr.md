# PRA and BSCR

## Summary

- **Sources:** approved January EDM, PRA workbook mappings, and current BSCR assumptions.
- **Calculation:** `bscr/BSCR_UKEU.py`, `pra/workbooks/PRA_BSCR_Aggs.xlsx`, and the BSCR workings workbook.
- **Final workbook/output:** PRA pivot tabs and `bscr/workbooks/2026 BSCR - UKEU - HIC.xlsx` Schedule X.
- **Time estimate:** 1 day for PRA and BSCR together.

Both processes use `bscr/BSCR_UKEU.py`, but they produce different files and workbook outputs.

| Process | Script output | Paste into | Refresh | Final calculation output |
|---|---|---|---|---|
| PRA | PRA raw and aggregate CSVs | `PRA_BSCR_Aggs.xlsx` input sheets | Validate table/pivot sources, then recalculate approved pivots | Calculation pivots; final PRA template is external |
| BSCR | `bscr-output.csv` | BSCR workings `Sheet1!A:G` | Rebuild the static `output` bridge, then refresh `piv` | Reviewed inputs for specified HIC cells; not all Schedule X content |

Use the individual pages for commands, exact paste ranges, and stop conditions.
Do not use this summary as a refresh procedure.

## Relationship between the routes

`pra/workbooks/PRA_BSCR_Aggs.xlsx` contains PRA pivots and legacy BSCR earthquake calculation panels. Those BSCR panels overlap the separate Python-to-BSCR-workings route; neither automatically supersedes the other. Reconcile both routes and obtain return-owner approval before selecting final BSCR values.

The current Python PRA raw/aggregate outputs are regeneration candidates. They do not by themselves prove how the checked-in January pivot tables were populated. The earthquake route has a documented `2/2` command and control total; the exact all-peril producer remains unconfirmed. PRA `2/2` and BSCR `1/1` are unlike scopes and must not be compared or selected between until their peril, geography, retention, FX, and unit bases are aligned and approved.

## Shared operating sequence

1. Freeze the approved server/database, codes, mappings, retentions, FX, workbook versions, and reporting date.
2. Preserve detailed and grouped script outputs with row counts and totals.
3. Load only the documented input ranges and preserve workbook formula/table/pivot definitions.
4. Reconcile source, grouped output, workbook inputs, formulas, pivots, and final handoff values.
5. Resolve known geography, retention, FX, stale-link, and pivot-source issues before sign-off.

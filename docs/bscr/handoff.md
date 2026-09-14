# BSCR handoff trace

## Status

**Blocked — no approved Schedule X handoff.** This trace records the current CSV lineage and historical workbook observations; it is not a final cell map and does not turn candidate matches into approved destinations.

Use the [offline runbook](runbook.md) and [technical contract](technical-contract.md) for the executable process.  The calculation boundary ends at reviewed CSV exposure outputs unless an owner approves a separate final-template handoff.

## Current CSV lineage

| Stage | Required artifact | Contract or meaning | Next stage |
|---|---|---|---|
| Approved extraction | `bscr/sql/bscr-extract.sql` run on the approved export host | One approved snapshot, peril, and policy selection; defaults are `@peril = 1`, `@policy_type = 1`, not cycle approval | `bscr-source.csv` |
| BSCR source | `bscr-source.csv` | Exact header: `pml,accgrpid,uwritrname,state,userid1,branchname,cntrycode,is_geocoded`; source currency and source row counts remain evidence | Offline Python |
| Offline calculation | `bscr/BSCR_UKEU.py` with `--input-dir`, `--output-dir`, and `--process bscr` | Reads the folder only; no database, embedded SQL, workbook, Excel, or ODBC dependency | `bscr-output.csv` |
| Reviewed output | `bscr-output.csv` | Exact header: `cntrycode,bscr_entity,region,sum_pml,sum_net,count_policies,is_geocoded`; gross/net and contributing counts require reconciliation | Reviewed exposure input only |

`sum_pml` and `sum_net` retain source currency; Python performs no FX conversion.  `count_policies` is not a distinct contract count.  `ALL` and regional rows overlap and must not be summed, while a different peril requires a separate approved extraction rather than another region view.

## Historical workbook observations (optional reference)

The checked-in workings workbook historically represented script output in `Sheet1!A:G`, formula columns in `H:K`, a static bridge in `output!A:F`, formulas in `G:J`, and review pivots in `piv`.  Those ranges are historical traces only: the bridge was not a refreshable link, and the CSV process does not load or refresh the workbook.

The HIC workbook contains candidate labels for Schedules X(a), X(b), X(c), and X(f), but the checked-in files do not evidence current editable cells, required measures, or approved source ranges.  They also do not provide EP curves, premiums, narratives, model classifications, or a distinct-contract method.

No destination may be selected from label position, fill colour, cached values, prior layouts, or workbook formulas.  An approved map would need source file/range, measure, currency/unit, as-of date, destination cell, preparer, reviewer, and approval ID.

## Known calculation caveats

- The policy join is not proven to be policy-grain safe because downstream grouping omits `policyid`; multiple policy/geography rows can multiply exposure.
- The current `is_nahu()` implementation returns true for every US row because its intended state allow-list is bypassed; this is not approved coastal-state logic.
- Retention remains `_QS = 0.50`, `_SRP = 0.3333`, otherwise `1.00`, with `_QS` winning when both markers occur.
- Source currency must remain distinct from USD; the historical workbook's `1.35` and `/1,000,000` mechanics are not Python CSV calculations.

## Missing evidence and contract IDs

- **COMMON-01:** approved snapshot, peril/policy parameters, source currency, mappings, output directory, reviewer, and reproducible run record are incomplete.
- **BSCR-01:** policy-level grain, join diagnostics, distinct contract count, geography, NAHU behavior, retention, and FX decisions are unresolved.
- **BSCR-02:** no approved CSV-to-workbook static bridge is required by the offline run, and no approved historical `Sheet1` → `output!A:F` bridge exists for optional comparisons.
- **BSCR-03:** HIC mapping and supplemental sources (EP curves, premiums, narratives, model classifications, and X(f) methodology/counts) are absent.
- **BSCR-04:** HIC `#REF!` formulas, old external links, and current-cycle template defects are unresolved.

Until these artifacts and decisions are supplied, the handoff ends at reconciled `bscr-output.csv`; it does not continue to a final Schedule X cell or claim a completed return.

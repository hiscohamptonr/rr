# BSCR technical contract — offline CSV calculation

This is the implementation reference for [runbook.md](runbook.md).  It describes the current code and observed historical workbook mechanics; it does not approve a snapshot, policy logic, geography, currency, retention, FX, Schedule X methodology, or final handoff.

## Scope and calculation boundary

The process is two separate stages:

1. An approved SQL-export host runs `bscr/sql/bscr-extract.sql` against the approved snapshot and writes `bscr-source.csv`.
2. The calculation PC runs `bscr/BSCR_UKEU.py` offline against a folder of CSVs and writes `bscr-output.csv`.

The Python stage reads no database, embedded SQL, workbook, Excel connection, or ODBC configuration.  The calculation PC needs Python 3.13+ and the pinned `bscr/requirements.txt`; `uv`, Excel, and ODBC are not required.

Each input folder is one approved snapshot and one approved peril/policy selection.  A different peril is a different extraction and input folder, not another overlapping region view of the same file.

## SQL export contract

The separate `bscr/sql/bscr-extract.sql` query defaults to `@peril = 1` and `@policy_type = 1`.  Those defaults do not approve a cycle; the export record must identify the approved values, query revision, snapshot, source currency, row count, and controls.  The exported input header is exactly:

```text
pml,accgrpid,uwritrname,state,userid1,branchname,cntrycode,is_geocoded
```

The SQL stage retains the query's source grain and does not promise distinct contracts.  Its account/policy joins and resulting grouping require owner review before totals are accepted.

## Python input/output contract

From the repository root, create the Windows environment once:

```text
python -m venv .venv
.venv\Scripts\python -m pip install -r bscr\requirements.txt
```

Run BSCR from a new empty output directory:

```text
.venv\Scripts\python bscr/BSCR_UKEU.py --input-dir runs\eq\input --output-dir runs\eq\output --process bscr
```

The supported process choices are `bscr`, `pra`, and `both`; `both` is the default.  `bscr` requires `bscr-source.csv` and emits `bscr-output.csv`; `both` requires all source files in the shared contract.  The output directory must be absent or empty before execution, and a failed or incomplete run is not consumable.

The BSCR output header is exactly:

```text
cntrycode,bscr_entity,region,sum_pml,sum_net,count_policies,is_geocoded
```

Output meanings:

| Column | Meaning |
|---|---|
| `cntrycode` | Source country code retained in regional and `ALL` rows |
| `bscr_entity` | First case-insensitive substring in order `HIG`, `HSA`, `33`, `3624`, `HIC` |
| `region` | `ALL`, `is_eu`, `is_jp`, `is_na_eq`, `is_nahu`, or `is_us_all` |
| `sum_pml` | Gross amount in source currency before Python retention |
| `sum_net` | Amount after current substring retention |
| `count_policies` | Contributing grouped/source-row count, not guaranteed distinct policies |
| `is_geocoded` | `0` only when `addrmatch = 0`; null currently becomes `1` in the SQL source logic |

Python does not convert currency.  Keep source currency beside every control total and do not relabel output as USD.  The historical workings workbook applied `1.35` and `/1,000,000`; those workbook mechanics are not performed by this CSV stage.

## Current calculation mechanics and caveats

The observed calculation groups source exposure to entity/geography and writes gross/net totals and contributing counts.  Retention is `_QS = 0.50`, `_SRP = 0.3333`, otherwise `1.00`; when both markers occur, `_QS` wins.

The policy join is not demonstrably policy-grain safe: `policyid` is omitted from downstream grouping, so multiple geography or policy rows can cross-multiply exposure.  `count_policies` therefore cannot establish distinct contracts for Schedule X(f), and join diagnostics, policy/account counts, and gross/net controls remain required.

`ALL` is a separate country/geocode view.  Regional flags overlap, so regional rows are not mutually exclusive and must not be summed.  Region overlap also does not replace a separate SQL extraction for another peril.

The current `is_nahu()` implementation returns true for every US row because its intended state allow-list is bypassed; this is not approved coastal-state logic.  Python and workbook geography lists also differ, including country and US-state/Caribbean handling.

## Historical workbook trace (optional reference only)

The checked-in workings workbook historically contained `Sheet1!A:G` source rows, formula columns `H:K`, static `output!A:F`, formula columns `G:J`, and `piv` review values.  Its static bridge was not a refreshable link, and its pivots had fixed historical ranges.  These artifacts explain prior comparisons only; the Python CSV calculation does not open, update, or depend on them.

The HIC workbook is a historical final-template reference with unresolved `#REF!`/external-link defects and no approved source-to-cell map.  Labels, colours, cached values, and prior layouts cannot identify current editable destinations.

## Review boundary and blockers

Reconcile `bscr-source.csv` to `bscr-output.csv` by gross/net totals, source and contributing-row counts, entity, country/state, region, and geocode classification.  Retain the exact source currency, snapshot, peril/policy parameters, code revision, and exception decisions.

Current blockers are unresolved all-peril approval, policy-grain/join multiplication, geography and NAHU decisions, retention and source-currency/FX approval, and an approved final HIC mapping.  The output is reviewed exposure input only; it does not establish EP curves, premiums, narratives, model/data-quality classifications, distinct-contract methodology, or final Schedule X sign-off.

# BSCR technical contract — observed mechanics for humans and LLMs

This is the detailed implementation reference for [runbook.md](runbook.md).
It captures observed `BSCR_UKEU.py` and workbook behaviour; it is not a second
procedure and does not approve mappings, policy logic, geography, currency,
retention, FX, Schedule X methodology, or handoff. See [handoff.md](handoff.md)
for evidenced lineage and missing destinations.

## Scope, sources, and calculation boundary

The process calculates entity and regional catastrophe exposure inputs for BSCR
Schedule X. It uses SQL Server EDM tables `loccvg`, `loc`, `policy`, and
`accgrp`, selected by `bscr/BSCR_UKEU.py`; the seven-column script output in
`bscr/workbooks/Workings_with_geocodingFW - Including blanks USD.xlsx`; and
reviewed manual entry into `bscr/workbooks/2026 BSCR - UKEU - HIC.xlsx`.
Current instructions, approved template, mappings, rates, and annual owner
decisions are external and authoritative.

The script:

1. selects `loccvg` records for the approved peril and groups `valueamt` by
   location and deductible fields;
2. sets the grouped amount to zero when below `deductamt` (does not subtract
   the deductible);
3. groups to account/geography and joins policies for the approved policy
   type;
4. caps exposure using the query's `partof`/`blanlimamt` policy-limit logic;
5. assigns entity, geography, and geocoding classifications;
6. applies substring retention: `_QS = 0.50`, `_SRP = 0.3333`, otherwise
   `1.00`; if both markers occur, `_QS` wins; and
7. writes grouped gross/net totals and contributing-row counts.

Python does not perform currency conversion. The workings workbook owns the
hard-coded `1.35` conversion and `/1,000,000` scaling. The final HIC workbook
owns template formulas and controlled inputs. The workings and HIC files are
not formula-linked; transfer is manual, reviewed, and evidenced.

## Query grain and output contract

The query groups `loccvg.VALUEAMT` by location/deductible/limit fields. Location
limit fields are grouping fields, not applied limits. Equality and null
deductibles retain amount. It then groups to account/state/country/geocode,
joins policies, and applies the `partof`/`blanlimamt` cap expression. The
policy join is not demonstrably at policy-level grain: multiple geography or
geocode rows and policies can cross-multiply, and grouping omits `policyid`.

The seven output columns are:

| Column | Meaning |
|---|---|
| `cntrycode` | Source country code retained in regional and `ALL` rows |
| `bscr_entity` | First case-insensitive substring in order `HIG`, `HSA`, `33`, `3624`, `HIC` |
| `region` | `ALL`, `is_eu`, `is_jp`, `is_na_eq`, `is_nahu`, or `is_us_all` |
| `sum_pml` | Gross amount before workbook conversion |
| `sum_net` | Amount after substring `_QS`/`_SRP` retention |
| `count_policies` | Contributing grouped/source-row count; not guaranteed distinct policies |
| `is_geocoded` | `0` only when `addrmatch = 0`; null currently treated as `1` |

Regional flags overlap. A source row can contribute to multiple regional
buckets; regional rows must not be added as mutually exclusive totals. `ALL`
is calculated separately and remains grouped by country and geocoding status.

## Geography and null truth table

- `addrmatch = 0` means not geocoded; null and every other value mean geocoded.
- Current `is_nahu()` returns true for every US row: a null state returns true,
  while a non-null state bypasses the intended allow-list. It also includes
  selected Caribbean/Mexico codes. This is not approved coastal-state logic.
- NA EQ, EU, Japan, and other country sets are hard-coded, case-sensitive, and
  overlap. `LX` appears in the EU list.
- Produce country/state frequency tables and owner-approved regional totals
  before use. Python and workbook geography lists differ, including Caribbean
  codes and US coastal-state definitions.

## Workbooks and invariant ranges

The workings workbook sheets are:

| Sheet | Role |
|---|---|
| `AUDIT_SUMMARY` | Purpose, lineage, output, and control reminder |
| `Sheet1` | Script output A:G; formula columns H:K |
| `output` | Static entity/region/geocoding rows A:F; formula columns G:J |
| `piv` | Reviewed gross/net values in USD millions by entity/region/geocode |

The input contract is seven columns in `Sheet1!A:G`, with H:K filled through
the exact data range. `Sheet1` is not an Excel table. Its local pivot uses the
fixed full-column source `A1:K1048576`; it is filtered and is not the
downstream consolidation. Do not create or resize a table without an approved
workbook change.

`output!A:F` are static values; only G:J are formulas. All `piv` pivots source
`output!A1:J50`. Consequently this sequence is invalid:

```text
paste Sheet1 -> Refresh All -> use piv
```

A controlled bridge must specify how to rebuild `output!A:F` from `Sheet1`,
including the exact key, aggregation, clear/paste method, treatment of groups
that vanished, formula coverage, and reconciliation. Without that approval,
stop. Refreshing `piv` alone can retain stale static rows.

The workings workbook's formula columns apply `1.35` and `/1,000,000`; confirm
source currency, rate direction, and annual approval. Checked-in January
`Sheet1` `ALL` comparison totals are gross `237,171,936,541.44` and net
`225,427,324,454.27`. These values do not prove that `output`, `piv`, or HIC
are current and are not approved tolerances.

## Execution contract

From the repository root, `uv sync --locked` prepares the locked environment;
`uv run python bscr/BSCR_UKEU.py --help` does not connect to SQL Server. A
production candidate uses a new empty directory:

```bash
uv run python bscr/BSCR_UKEU.py \
  --server '<approved-server>' \
  --database '<approved-edm>' \
  --peril 1 \
  --policy-type 1 \
  --output '<new-empty-run-directory>/bscr-output.csv' \
  --source-output '<new-empty-run-directory>/bscr-source.csv'
```

The run tests the connection, executes the embedded query, prints source
diagnostics, writes the optional account-level/geocoded source file, and
writes the seven-column aggregate output. Files are written sequentially; do
not load any result if the command fails or either expected file is missing.
Retain `bscr-source.csv` as detailed evidence for entity, geography,
geocoding, retention, and row-count investigations, along with the complete
run record and metadata.

## Workbook load and refresh mechanics

In a controlled copy, review `AUDIT_SUMMARY`; verify ODBC Driver 18, integrated
authentication, and approved certificate policy before connecting. Record
formulas, pivot sources, calculation mode, external links, designated
unlocked/yellow ranges, and pre-refresh values.

Clear only old source rows in `Sheet1!A:G`; preserve row 1, formulas H:K,
formatting, and the fixed full-column source. Validate the CSV header and
paste data rows only into `Sheet1!A2:G...` in existing order. Fill H:K through
the final row and confirm `1.35` and `/1,000,000` remain intact.

Before any pivot refresh, stop and obtain the approved procedure that rebuilds
static `output!A:F` from `Sheet1`, including clearing vanished groups and
retaining source evidence. After the bridge is approved and rebuilt, inspect
`output` first, then inspect/refresh `piv`. Use **Data > Refresh All** only when
it cannot update stale or unapproved external connections. Recalculate and
check errors, blanks, unmapped entities, unexpected geography, geocoding
splits, and each final-cell map.

Reconcile query diagnostics, `bscr-source.csv`, `bscr-output.csv`, `Sheet1`,
rebuilt `output`, and `piv` for gross, net, and source-row counts. Record
currency, unit, source range, as-of date, parameters, and row count with any
comparison totals.

## Schedule X and handoff constraints

`piv` supplies only reviewed, mapped exposure inputs. Its regional values can
include Atlantic hurricane, North American earthquake, European windstorm,
and Japanese earthquake views potentially used by Schedule X(c), but it is not
a complete source for every schedule or field. It does not derive EP curves,
premiums, narratives, model/data-quality classifications, or Schedule X(f)
methodology classifications. `count_policies` cannot establish distinct
contract counts for X(f).

The HIC workbook contains `#REF!` formulas, older external links, and a blank
current-cycle HIG template. Schedule X(b) references an external `Import`
sheet. An unresolved formula/link is a stop condition, not something to
preserve. The final transfer must use an approved source-to-destination map
containing source range, destination cell, measure, currency/unit, and
reviewer. Current editable cells are yellow/unlocked; never infer an input
from a generic green-cell convention.

Copy only values listed in the approved map into designated unlocked/yellow
inputs in Schedules X(a), X(b), X(c), and X(f). Do not replace template
formulas, validation, structure, or non-input cells. For each entry record
source workbook/range, destination workbook/cell, value, currency, unit,
as-of date, preparer, reviewer, and review date. The manual transfer is the
final handoff boundary; a successful SQL connection, command completion, or
pivot refresh is not approval or sign-off.

## Required gates and known issues

Do not continue unless the approved database snapshot, parameters, entity and
geography mappings, retention, FX, source currency, and output cell map are
recorded; the output directory is unique and empty; and ODBC/certificate
policy is approved. Per-CTE before/after join counts, distinct policies and
accounts, and gross/net totals must meet owner-approved checks. Resolve all
unmapped entities/geography, unexpected address-match values, and
multi-policy accounts. Rebuild and reconcile the bridge and pivots. Resolve
all final-workbook `#REF!` and external links or explicitly approve them out of
scope.

Review these known discrepancies before production use:

- `is_nahu()` currently returns true for all US records due to unreachable
  state allow-list logic.
- Python and workbook geography lists differ.
- `_SRP` is `0.3333` in Python, `33%` in the PRA workbook, and `0.33333` in
  supplementary SQL.
- The workings workbook hard-codes `1.35`; confirm intended basis and rate.
- Final HIC links point to older external workbooks; Schedule X(b) references
  external `Import`.
- Confirm every pivot source range and refresh state.
- Review policy/account join cardinality; a final group does not prove that
  upstream one-to-many joins did not multiply exposure.

The script does not approve the reporting database, mappings, rates, source
currency, retention, bridge, refresh behaviour, final values, green/yellow
cells, or sign-off.

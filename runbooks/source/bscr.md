# BSCR Schedule X

## Summary

- **Sources:** approved January EDM and current BSCR entity, geography, retention, and FX assumptions.
- **Calculation:** `bscr/BSCR_UKEU.py` and `bscr/workbooks/Workings_with_geocodingFW - Including blanks USD.xlsx`.
- **Final workbook/output:** `bscr/workbooks/2026 BSCR - UKEU - HIC.xlsx`, Schedules X(a), X(b), X(c), and X(f).
- **Time estimate:** included in 1 day for PRA and BSCR together.

## Purpose and sources

This process calculates entity and regional catastrophe exposure values for BSCR Schedule X. It uses:

- SQL Server EDM tables `loccvg`, `loc`, `policy`, and `accgrp` selected by `bscr/BSCR_UKEU.py`;
- the seven-column script output loaded into `bscr/workbooks/Workings_with_geocodingFW - Including blanks USD.xlsx`; and
- reviewed manual entry into `bscr/workbooks/2026 BSCR - UKEU - HIC.xlsx`.

Current BSCR instructions, the approved template, mappings, rates, and annual owner decisions are external to the repository and remain authoritative.

## Calculation boundary

The script performs the following work:

1. Selects `loccvg` records for the approved peril and groups coverage `valueamt` by location and deductible fields.
2. Sets the grouped amount to zero when it is below `deductamt`; it does not subtract the deductible.
3. Groups to account/geography and joins policies for the approved policy type.
4. Caps exposure using the query's `partof`/`blanlimamt` policy-limit logic.
5. Assigns BSCR entity, geography, and geocoding classifications.
6. Applies suffix retention: `_QS = 0.50`, `_SRP = 0.3333`, otherwise `1.00`.
7. Writes grouped gross/net totals and contributing-row counts.

The script does not perform currency conversion. The workings workbook owns the hard-coded `1.35` conversion, `/1,000,000` scaling, consolidation, and pivots. The final HIC workbook owns template formulas and the controlled green-cell inputs.

The workings and HIC files are not formula-linked. The final transfer is manual, reviewed, and evidenced.

## Output contract

| Column | Meaning |
|---|---|
| `cntrycode` | Source country code retained in both regional and `ALL` output rows |
| `bscr_entity` | First configured entity token found in `userid1`: `HIG`, `HSA`, `33`, `3624`, or `HIC` |
| `region` | `ALL`, `is_eu`, `is_jp`, `is_na_eq`, `is_nahu`, or `is_us_all` |
| `sum_pml` | Gross amount before workbook currency conversion |
| `sum_net` | Amount after suffix-based `_QS`/`_SRP` retention |
| `count_policies` | Count of contributing grouped/source rows; not guaranteed to be distinct policies |
| `is_geocoded` | `1` when `addrmatch` is non-zero, otherwise `0` |

Regional flags overlap. A source row can contribute to more than one regional bucket. Do not add regional rows together as if they were mutually exclusive. `ALL` is calculated separately and remains grouped by country and geocoding status.

## Pre-run controls

1. Record the server, EDM database and roll-up/version, reporting date, script revision, operator, and reviewer.
2. Confirm the annual meaning and approval of peril/policy codes; January defaults are `1/1`.
3. Approve the entity list, geography mappings, geocoding treatment, and `_QS`/`_SRP` factors.
4. Confirm the source currency and approve the workbook's `1.35` conversion and `/1,000,000` unit scaling.
5. Open controlled copies of both workbooks and record formulas, pivot sources, calculation mode, external links, designated green cells, and pre-refresh values.

## Run

From the repository root:

```bash
uv sync
uv run python bscr/BSCR_UKEU.py --help
uv run python bscr/BSCR_UKEU.py \
  --server '<approved-server>' \
  --database '<approved-edm>' \
  --peril 1 \
  --policy-type 1 \
  --output outputs/bscr-output.csv \
  --source-output outputs/bscr-source.csv
```

`--help` does not connect to SQL Server. The run itself tests the trusted connection, executes the embedded query, prints source diagnostics, writes the optional account-level/geocoded source file, and writes the seven-column aggregate output. Existing output paths may be replaced.

Retain both CSVs and the complete run record. `bscr-source.csv` is the detailed evidence needed to investigate entity, geography, geocoding, retention, and row-count results.

## Workings workbook

| Sheet | Role |
|---|---|
| `AUDIT_SUMMARY` | Purpose, lineage, output, and required-control reminder |
| `Sheet1` | Script output in A:G; formula columns H:K calculate converted and USD-million measures |
| `output` | Consolidates by entity, region, and geocoding, applying `1.35` and `/1,000,000` |
| `piv` | Presents reviewed gross/net values in USD millions by entity/region/geocoding |

### Load and refresh

1. Open a controlled copy of `bscr/workbooks/Workings_with_geocodingFW - Including blanks USD.xlsx` and review `AUDIT_SUMMARY`.
2. Clear only the old source rows in `Sheet1!A:G`; preserve row 1, formulas H:K, tables, pivots, and formatting.
3. Paste `bscr-output.csv` into `Sheet1!A:G` in the existing header order.
4. Fill formulas H:K through every pasted row and confirm the `1.35` and `/1,000,000` logic is still intact.
5. Inspect workbook connections and pivot sources. Refresh the intended `output` and `piv` calculations; use **Data > Refresh All** only when it will not update stale or unapproved external connections.
6. Check `output` first, then `piv`, and inspect errors, blanks, unmapped entities, unexpected geography, and geocoding splits.
7. Reconcile query diagnostics, `bscr-source.csv`, `bscr-output.csv`, `Sheet1`, `output`, and `piv` for gross, net, and row counts.

The checked-in January `Sheet1` `ALL` comparison totals are:

- gross: `237,171,936,541.44`
- net: `225,427,324,454.27`

Record currency, unit, source range, as-of date, parameters, and row count with these values. They are comparison baselines, not approved tolerances.

## Final output and handoff

Use `piv` for the reviewed BSCR values. The regional values include Atlantic hurricane, North American earthquake, European windstorm, and Japanese earthquake views used by Schedule X(c).

Copy approved values manually into the designated green cells in Schedules X(a), X(b), X(c), and X(f) of `bscr/workbooks/2026 BSCR - UKEU - HIC.xlsx`. Do not replace template formulas, validation, structure, or non-input cells.

For every entry, record the source workbook/range, destination workbook/cell, value, currency, unit, as-of date, preparer, reviewer, and review date.

## Known issues requiring review

- `is_nahu()` currently returns true for all US records: a null state returns true, while a non-null state bypasses the unreachable allow-list. Resolve or explicitly approve this behavior before production use.
- Python and workbook geography lists differ, including Caribbean codes and US coastal-state definitions.
- `_SRP` is `0.3333` in Python, `33%` in the PRA workbook, and `0.33333` in supplementary SQL.
- The workings workbook hard-codes `1.35`; confirm the source amounts are on the intended basis and that the rate is approved for the cycle.
- The final HIC workbook contains links to older 2025 and 2017 workbooks and a blank 2026 HIG template. Schedule X(b) references an external `Import` sheet.
- Confirm every pivot source range and refresh state before handoff.
- Review policy/account join cardinality and `count_policies`; a final group does not prove that upstream one-to-many joins did not multiply exposure.

## Automation boundary

The script does not approve the reporting database, mappings, rates, source currency, green cells, refresh behavior, final values, or sign-off. A successful SQL connection or command completion is not evidence that those controls passed.

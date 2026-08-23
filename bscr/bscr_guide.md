# BSCR aggregate guide

## Data sources

- Configured SQL Server EDM tables `loccvg`, `loc`, `policy`, and `accgrp`.
- [`BSCR_UKEU.py`](BSCR_UKEU.py).
- BSCR calculation workbook [`Workings_with_geocodingFW - Including blanks USD.xlsx`](Workings_with_geocodingFW%20-%20Including%20blanks%20USD.xlsx).
- HIC return workbook [`2026 BSCR - UKEU - HIC.xlsx`](2026%20BSCR%20-%20UKEU%20-%20HIC.xlsx).
- Current BSCR instructions, mappings, rates, and approved green-cell handoff.

## Purpose

`BSCR_UKEU.py` is the SQL-to-CSV calculation stage for BSCR Schedule X. It allocates account PML to locations, applies deductible and policy-limit logic, assigns entities and regional flags, applies Fine Art retention, and writes long-form grouped totals.

## Calculation boundary

The script owns:

- SQL extraction from the configured EDM;
- location TIV and PML allocation;
- invalid-location zeroing;
- deductible and policy-limit application;
- entity/geography/geocoding classification;
- `_QS` and `_SRP` retention;
- grouped gross/net CSV output.

The workbooks own:

- the hard-coded `1.35` USD conversion and USD-millions columns;
- consolidation and pivots by entity, geography, and geocoding;
- final Schedule X formulas and approved green-cell entry.

No formula relationship connects the workings workbook to the final HIC workbook.

## Output

```text
cntrycode,bscr_entity,region,sum_pml,sum_net,count_policies,is_geocoded
```

`count_policies` is a count of contributing grouped rows, not guaranteed distinct policies. Geography flags overlap, while `ALL` is calculated separately.

## Material assumptions and limitations

- The embedded SQL targets a specific GC-format EDM.
- `is_nahu()` currently returns true for every non-null US state; fix and approve the intended state mapping before production use.
- Python and workbook geography lists differ.
- The script performs no currency conversion and drops currency from its output.
- `_SRP` uses `0.3333` in Python, compared with `33%` in the PRA workbook and `0.33333` in SQL.
- The workings workbook's `1.35` factor must be confirmed against the source currency and reporting-cycle rate.
- The final HIC workbook contains stale external links to older templates.
- Historical similarity to model output is not current reconciliation or materiality approval.

## Controlled use

Use the [runbook](bscr-runbook.md) for commands. Use the [BSCR process guide](../docs/regulatory-returns/bscr.md) and [complete data-flow map](../docs/regulatory-returns/data-flow.md) for workbook lineage, known mismatches, and green-cell evidence requirements.

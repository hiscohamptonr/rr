# UKEU retail roll-up documentation

## Data sources

- Annual GC-format SQL Server EDMs named in the checked-in Python and SQL.
- Received S33 source workbook and companion instruction email under `UKEU S33 Contingency/`.
- BSCR, PRA, and Lloyd's calculation/return workbooks under `bscr/`, `pra/`, and `lloyds/`.
- `GlobalExposures.data.Events`, `data.ShapeFiles`, and `data.PML` for event-footprint reporting.
- Current regulator instructions, approved templates, mappings, rate sets, and cycle decisions held outside this repository.

This repository contains regulatory-return processes, workbook evidence, and supporting exposure utilities for the 2026 retail roll-up cycle. Hard-coded dates, rates, mappings, and database names must be reviewed for each cycle.

## Regulatory returns

Start with the [regulatory returns hub](regulatory-returns/index.md) and the [complete data-flow map](regulatory-returns/data-flow.md).

| Return | Guide |
|---|---|
| Lloyd's supplementary information | [Source workbook, SQL extracts, and calculation workbooks](regulatory-returns/lloyds-supplementary.md) |
| BSCR Schedule X | [Python extraction, workings, and HIC handoff](regulatory-returns/bscr.md) |
| PRA and combined BSCR aggregates | [PRA/BSCR calculation workbook](regulatory-returns/pra.md) |
| Shared controls | [Controls and evidence](regulatory-returns/controls.md) |

## Current artefacts

The repository now contains the BSCR workings and HIC return workbook, the combined PRA/BSCR workbook, Lloyd's supplementary workings, and the received S33 exposure package. These files were statically inspected for sheet structure, formulas, links, cached values, and provenance; they were not recalculated or refreshed during documentation review.

The calculation workbooks still depend on manual paste/green-cell handoffs, external templates, and unresolved annual assumptions. Presence in Git does not make a workbook an approved submission.

## SharePoint and Copilot entry point

Publish this `docs` directory with `regulatory-returns` intact and use this page as the documentation entry point. Publish linked SQL, Python, and controlled workbook artefacts alongside the documentation when source-level traceability is required; links beginning with `../` leave the `docs` directory.

Copilot answers must distinguish direct evidence, structural schema matches, manual handoffs, and unresolved assumptions. Current regulator instructions and approved reporting-cycle decisions remain authoritative.

## Supporting tools

- [`aggregates/aggs-from-edm.sql`](../aggregates/aggs-from-edm.sql): aggregate query embedded in the PRA/BSCR calculation route.
- [`globalexposures/`](../globalexposures/): separate event-footprint exposure reporting.
- [`bscr/BSCR_UKEU.py`](../bscr/BSCR_UKEU.py): executable BSCR SQL-to-CSV workflow.

## Important limitation

The checked-in calculations target specific GC/London Market schemas and reporting-cycle assumptions. They are not generic regulatory extractors. Review database, schema, codes, geography, mappings, retention, FX, dates, units, source totals, and workbook refresh state before use.

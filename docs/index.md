# UKEU retail roll-up documentation

This repository contains regulatory-return processes and supporting exposure
aggregation/reporting utilities for the GC-format 2026 retail roll-up EDM.

## Regulatory returns

Start with the centralized [regulatory returns hub](regulatory-returns/index.md).

| Return | Guide |
| --- | --- |
| Lloyd's supplementary returns | [Direct SQL Server EDM extracts](regulatory-returns/lloyds-supplementary.md) |
| BSCR Schedule V | [BSCR process](regulatory-returns/bscr.md) |
| PRA January/February | [PRA process](regulatory-returns/pra.md) |
| Shared execution controls | [Controls and evidence](regulatory-returns/controls.md) |

The BSCR and PRA processes describe spreadsheet formula/pivot stages ending in
green output areas. No spreadsheet file is present in the working tree or
reachable Git history, so those stages cannot be inspected or run from this
repository alone.

## SharePoint and Copilot entry point

Publish this `docs` directory with its `regulatory-returns` subdirectory intact,
then use this page as the Copilot agent's documentation entry point. Publish the
linked SQL and Python source files alongside the documentation when source-level
traceability is required; links that begin with `../` refer to files outside the
`docs` directory.

The feature guides are deliberately self-contained and use explicit labels for
observed repository behaviour, historical notes, missing artifacts and annual
decisions. Copilot answers should not turn a hard-coded 2026 value or historical
statement into a current reporting rule. Current regulator instructions and
approved reporting-cycle workbooks remain authoritative.

## Supporting tools

- [`aggregates/aggs-from-edm.sql`](../aggregates/aggs-from-edm.sql): an
  EDM-specific aggregate query and historical basis for return work.
- [`globalexposures/`](../globalexposures/): event-footprint exposure reporting.
- [`bscr/BSCR_UKEU.py`](../bscr/BSCR_UKEU.py): the executable BSCR
  Marimo/Python workflow.

## Important limitation

The aggregation SQL was written and checked against GC/London Market outputs
for the supplied 2026 EDM format. It is not a generic EDM extractor. Review
database names, schema, codes, mappings, retention factors and controls for
every reporting cycle before use.

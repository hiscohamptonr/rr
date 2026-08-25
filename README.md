# January 2026 workflows

## Generated reference runbooks

These are reference instructions, **not evidence of current approval**. Current
regulator instructions, controlled templates, mappings, rates, databases, and
owner decisions remain authoritative.

- `runbooks/docx/PRA-BSCR-Jan-2026.docx`
- `runbooks/docx/Lloyds-Supplementary-Jan-2026.docx`
- `runbooks/docx/Global-Exposures-Jan-2026.docx`

To regenerate them, edit `runbooks/source/`, ensure Pandoc is installed, then
run `python3 tools/build_docx.py` from the repository root. This overwrites the
files in `runbooks/docx/`.

Read the [shared controls](runbooks/source/run-checks.md) before using a
process runbook: [PRA](runbooks/source/pra.md), [BSCR](runbooks/source/bscr.md),
[Lloyd's supplementary](runbooks/source/lloyds-supplementary.md), or
[Global Exposures](runbooks/source/global-exposures.md).

## Prerequisites

- Python 3.13 and `uv`; use the checked-in lockfile (`uv sync --locked`).
- Approved SQL Server/network access and the process-specific Microsoft ODBC
  driver (18 for PRA/BSCR; 17 for Global Exposures).
- Excel for workbook procedures and Pandoc only when regenerating DOCX files.

## Technical documentation

- [`docs/dataiku-aggs.md`](docs/dataiku-aggs.md) — current checked-in Dataiku
  OED baseline at commit `d264675`: provisional uncapped exposure behavior,
  not a final PRA, BSCR, or Lloyd's calculation.
- [`docs/calculation-discrepancies.md`](docs/calculation-discrepancies.md) —
  verified code/workbook discrepancies, their effects, and required owner
  decisions before production use.

## File layout

| Folder | Contents |
|---|---|
| `pra/workbooks/` | PRA calculation workbook |
| `pra/sql/` | PRA legacy/query SQL |
| `bscr/workbooks/` | BSCR workings and final HIC workbook |
| `bscr/BSCR_UKEU.py` | PRA/BSCR CSV producer |
| `lloyds/source/` | Received S33 workbook and instruction email |
| `lloyds/sql/` | Lloyd's extract SQL |
| `lloyds/workbooks/` | Four Lloyd's calculation workbooks |
| `globalexposures/` | Global Exposures output producer |
| `runbooks/source/` | Markdown operating instructions and DOCX source |
| `runbooks/docx/` | Final runbook deliverables |
| `docs/` | Technical documentation for repository scripts |
| `dataiku/` | Checked-in Dataiku aggregation SQL and implementation plan |

No HTML documentation site or virtual environment is committed; `uv sync` may
create an ignored local `.venv`.

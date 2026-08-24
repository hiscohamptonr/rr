# January 2026 workflows

## Deliverables

- `runbooks/docx/PRA-BSCR-Jan-2026.docx`
- `runbooks/docx/Lloyds-Supplementary-Jan-2026.docx`
- `runbooks/docx/Global-Exposures-Jan-2026.docx`

Rebuild them with `python3 tools/build_docx.py`.

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
| `runbooks/source/` | Markdown used only to generate the three DOCX files |
| `runbooks/docx/` | Final runbook deliverables |

No HTML documentation site or local Python virtual environment is retained.

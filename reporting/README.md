# Regulatory returns

PRA uses **SQL → CSV → Excel**; follow its short runbook.
BSCR uses **`bscr-output.sql` → paste eight result columns into Excel →
automatically populated entity schedules**. No Python is needed on the work
machine. Historical comparison is kept in a separate reconciliation workbook.
Global Exposures uses **SQL → CSV → offline Python**, with four input files
and local spatial calculations.
Python dependencies come from each project's `pyproject.toml` and `uv.lock`;
the runbooks use `uv run --isolated --locked` without a local `.venv`.
## Start with your guide

These are the short, human-readable instructions. Each covers what you need,
what to run, what to check and where the process stops.

| Process | Read online / in your editor | Open in Word |
|---|---|---|
| BSCR Schedule X | [BSCR guide](docs/bscr/runbook.md) | [BSCR](docs/generated/BSCR-Jan-2026.docx) |
| PRA aggregates | [PRA guide](docs/pra/runbook.md) | [PRA](docs/generated/PRA-Jan-2026.docx) |
| Lloyd's supplementary | [Lloyd's guide](docs/lloyds/runbook.md) | [Lloyd's](docs/generated/Lloyds-Supplementary-Jan-2026.docx) |
| Global Exposures | [Global Exposures guide](docs/global-exposures/runbook.md) | [Global Exposures](docs/generated/Global-Exposures-Jan-2026.docx) |
| Dataiku aggregation | [Dataiku guide](docs/dataiku/aggregation.md) | — |

**BSCR files:** [current SQL](bscr/sql/bscr-output.sql) ·
[population workbook](bscr/workbooks/BSCR_Auto_Population.xlsx) ·
[reconciliation workbook](bscr/reconcile/results/BSCR_Reconciliation.xlsx).
To refresh the population workbook: clear its old SQL input rows (keep the
headers/table), then paste the new results. Blue schedule fields remain manual.

Before running anything, use the [short run checklist](docs/operating-controls.md).
The guides describe the January 2026 implementation, not approval for a new
reporting cycle. Each guide flags the decisions still needed for production.
Dataiku is a separate provisional route, not a replacement for the returns.

## Need more detail?

- **LLMs and technical reviewers:** start with [LLM instructions](docs/llm-instructions.md).
- **Something is blocked:** [decisions](docs/decisions.md) lists the answer or artifact needed and how to close the issue.
- **Why is it blocked?** [calculation discrepancies](docs/calculation-discrepancies.md) contains the code and workbook evidence.

You do not need the detailed review instructions before browsing a human guide.

## Opening and updating the docs

Open `.docx` files in Word. For Markdown, open this folder in VS Code, select
`README.md` and press **⌘⇧V** for a formatted preview.

Markdown is the maintained source. Each Word file contains only its process's short runbook—no appended checklist or source-identity section.
To regenerate them, run the following from the `reporting/` directory with
Python and the project's locked dependencies:

```bash
uv run --isolated --locked python tools/build_docx.py
```

Unless a guide explicitly changes directories, its paths are relative to
`reporting/`, not the repository root. SQL assets and workbooks remain in
`bscr/`, `pra/`, `lloyds/`, `globalexposures/` and `dataiku/`.

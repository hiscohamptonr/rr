# Regulatory returns

## Start with your guide

These are the short, human-readable instructions. Each covers what you need,
what to run, what to check and where the process stops.

| Process | Read online / in your editor | Open in Word |
|---|---|---|
| BSCR Schedule X | [BSCR guide](docs/bscr/runbook.md) | [PRA & BSCR](docs/generated/PRA-BSCR-Jan-2026.docx) |
| PRA aggregates | [PRA guide](docs/pra/runbook.md) | [PRA & BSCR](docs/generated/PRA-BSCR-Jan-2026.docx) |
| Lloyd's supplementary | [Lloyd's guide](docs/lloyds/runbook.md) | [Lloyd's](docs/generated/Lloyds-Supplementary-Jan-2026.docx) |
| Global Exposures | [Global Exposures guide](docs/global-exposures/runbook.md) | [Global Exposures](docs/generated/Global-Exposures-Jan-2026.docx) |
| Dataiku aggregation | [Dataiku guide](docs/dataiku/aggregation.md) | — |

Before running anything, use the [short run checklist](docs/operating-controls.md).
The guides describe the January 2026 implementation, not approval for a new
reporting cycle. Each guide flags the decisions still needed for production.
Dataiku is a separate provisional route, not a replacement for the returns.

## Need more detail?

- **LLMs and technical reviewers:** start with [LLM instructions](docs/llm-instructions.md), then the process's technical reference.
- **Something is blocked:** [decisions](docs/decisions.md) lists the answer or artifact needed and how to close the issue.
- **Why is it blocked?** [calculation discrepancies](docs/calculation-discrepancies.md) contains the code and workbook evidence.
- **Where do workbook values go?** The [BSCR](docs/bscr/handoff.md), [PRA](docs/pra/handoff.md) and [Lloyd's](docs/lloyds/handoff.md) handoff traces distinguish known internal paths from missing final-cell maps.

You do not need to read the technical pack before browsing a human guide.

## Opening and updating the docs

Open `.docx` files in Word. For Markdown, open this folder in VS Code, select
`README.md` and press **⌘⇧V** for a formatted preview.

Markdown is the maintained source. The Word copies contain only the human
guides and short checklist; detailed references stay linked, not appended.
To regenerate them from the repository root, with Python and Pandoc installed:

```bash
python3 tools/build_docx.py
```

Commands in the guides run from the repository root. Scripts, SQL and workbooks
remain in `bscr/`, `pra/`, `lloyds/`, `globalexposures/` and `dataiku/`.

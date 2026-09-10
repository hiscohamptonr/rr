# Global Exposures

[Start here](../../README.md) · [Run checklist](../operating-controls.md) ·
[Detailed LLM reference](technical-contract.md)

**Result:** a CSV pack of exposure and estimated loss within event polygons.
There is no calculation workbook or Excel-loading step.

**Before production:** the owner must approve the source snapshot, event/PML
data, policy/portfolio rules and spatial controls. See
[GLOBAL-01](../decisions.md#global-01). A successful command is not approval.

## 1. Get ready

The script reads the annual EDM and `GlobalExposures.data.Events`,
`ShapeFiles` and `PML` database tables—not spreadsheets. Confirm the server,
ODBC Driver 17 access and approved settings in `globalexposures/exposures.py`.

Complete the [run checklist](../operating-controls.md). Check event/polygon/PML
IDs, polygon validity, coordinates and independent EDM totals. Use a **new,
empty output folder**: files are written individually, so reusing a folder can
mix results from different runs.

## 2. Install and run

From the repository root:

```bash
uv sync --project globalexposures --locked
uv run --project globalexposures python globalexposures/exposures.py --help
```

Run all events with the approved configuration:

```bash
uv run --project globalexposures python globalexposures/exposures.py \
  --output-dir '<new-run-folder>'
```

Or select an event and approved overrides (replace the example values):

```bash
uv run --project globalexposures python globalexposures/exposures.py \
  --event-id 123 --peril 4 --portnum PORTFOLIO_NUMBER \
  --output-dir '<new-run-folder>'
```

Do **not** use `--allow-missing-pml` for production: unknown loss can appear as
zero with a successful status. Exit `1` means pipeline failure; `2` means at
least one selected event failed. Do not deliver partial results.

## 3. Check the CSV pack

| File | What to check |
|---|---|
| `*_summary.csv` | Overall status and event counts—not monetary totals |
| `*_run_log.csv`, `*_error_log.csv` | Every selected event accounted for; investigate failures |
| `*_location_rows.csv` | Impacted-location detail |
| `*_account_breakdown.csv`, `*_location_breakout.csv` | Grouped totals reconcile to detail |
| `edm_exposures.csv` | Extract reconciles to independent EDM controls |

Investigate missing files/headers, join multiplication, invalid geometry/PML,
missing policy factors and every zero/no-impact result. A zero is acceptable
only with independent evidence that there was genuinely no impact. Do not sum
across overlapping events without an approved rule.

## 4. Review and deliver

Retain the full CSV pack, command, configuration/source snapshot, counts,
reconciliations and reviewer sign-off. Stop if any selected event or unexplained
exception remains unresolved.

The [technical reference](technical-contract.md) describes exact SQL, spatial
selection, status behavior and detailed validation requirements.

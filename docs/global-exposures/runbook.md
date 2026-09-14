# Global Exposures — CSV operator run

1. **Choose one scope.** Open the four files in `globalexposures/sql/` and
   use the same approved snapshot and event selection for the exports.
   Run `events.sql`, `shape-points.sql` and `pml.sql` against `GlobalExposures`.
   Run `edm-exposures.sql` against the selected EDM snapshot and export the results as:
   `events.csv`, `shape-points.csv`, `pml.csv`, and `edm-exposures.csv`.
   Use the same `@event_id` in those three queries (`NULL` means all events);
   set `@peril_to_use` and `@portnum_filter` in the EDM query for the required exposure scope.

2. **Place the inputs.** Put the four header-bearing CSVs beside
   `exposures.py`, or set each constant below to an arbitrary full path. A
   header-only shape or PML export can be valid for an event; review missing
   shapes and every `No impacted exposures` result rather than treating them as
   proof of no impact.

3. **Edit the constants at the top of `exposures.py`.** Use a new or empty
   output folder and keep the paths and event selection explicit:

   ```python
   EVENTS_INPUT_CSV = Path(__file__).with_name("events.csv")
   SHAPE_POINTS_INPUT_CSV = Path(__file__).with_name("shape-points.csv")
   PML_INPUT_CSV = Path(__file__).with_name("pml.csv")
   EDM_INPUT_CSV = Path(__file__).with_name("edm-exposures.csv")
   OUTPUT_DIR = Path(__file__).with_name("global_exposures_outputs")
   EVENT_ID_TO_RUN = None  # or one approved EventID
   ```

4. **Run from `globalexposures/`.** Use no CLI flags and no local virtual
   environment:

   ```bash
   uv run --no-project --with-requirements requirements.txt python exposures.py
   ```

5. **Inspect the complete output pack.** Review the summary, run and error
   logs, `*_location_rows.csv`, both breakdown files, and `edm_exposures.csv`.
   Account for each selected event and reconcile totals. Missing PML is an
   event failure. Boundary points count as impacted; an exposure in multiple
   polygons keeps only the highest-PML match (then lowest `PolygonID`), not an
   additive overlap. Investigate invalid or dropped coordinates, repaired
   geometry, multiplied post-join exposure, and every zero result before
   delivery. Keep inputs, constants, command, outputs, and reconciliations
   together.
   A `Complete` summary is processing status only; it does not approve a zero
   result or establish that monetary totals are complete.

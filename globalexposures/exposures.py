"""Calculate event exposures locally from four SQL-exported CSV files.

Run the scripts in globalexposures/sql on the appropriate database servers,
export with headers, then set the file paths below and run this file.
Python never connects to a database or reads a workbook.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon

# EDIT THESE PATHS BEFORE RUNNING; each input includes its CSV filename.
EVENTS_INPUT_CSV = Path(__file__).with_name("events.csv")
SHAPE_POINTS_INPUT_CSV = Path(__file__).with_name("shape-points.csv")
PML_INPUT_CSV = Path(__file__).with_name("pml.csv")
EDM_INPUT_CSV = Path(__file__).with_name("edm-exposures.csv")
OUTPUT_DIR = Path(__file__).with_name("global_exposures_outputs")
EVENT_ID_TO_RUN: int | None = None  # None means all events in the CSV.


@dataclass(frozen=True)
class RunConfig:
    events_csv: Path = EVENTS_INPUT_CSV
    shape_points_csv: Path = SHAPE_POINTS_INPUT_CSV
    pml_csv: Path = PML_INPUT_CSV
    edm_csv: Path = EDM_INPUT_CSV
    event_id_to_run: int | None = EVENT_ID_TO_RUN
    output_dir: Path = OUTPUT_DIR
    crs_wgs84: str = "EPSG:4326"
    fail_on_missing_pml: bool = True


CONFIG = RunConfig()


EVENT_COLUMNS = {
    "EventID": "Int64",
    "EventName": "string",
    "EventDescription": "string",
}
SHAPE_COLUMNS = {
    "ShapefileID": "string",
    "EventID": "Int64",
    "PolygonID": "Int64",
    "Lat": "float64",
    "Long": "float64",
    "DrawOrder": "Int64",
}
PML_COLUMNS = {"EventID": "Int64", "PolygonID": "Int64", "PML": "float64"}
EDM_COLUMNS = {
    "CEDANTID": "string",
    "PORTACCTID": "string",
    "PERIL": "Int64",
    "LOCID": "string",
    "LOCNUM": "string",
    "LATITUDE": "float64",
    "LONGITUDE": "float64",
    "GroundUpTIV": "float64",
    "PolicyAdjustedTIV": "float64",
    "CountryCode": "string",
    "CurrencyCode": "string",
    "PORTNAME": "string",
    "PORTNUM": "string",
    "POLICY_LINE_FACTOR": "float64",
    "FA_QS_SRP_FACTOR": "float64",
    "Coverage": "string",
}


def read_source_csv(path: Path, columns: dict[str, str]) -> pd.DataFrame:
    """Read headers and types explicitly, preserving identifier zeros and country NA."""
    frame = pd.read_csv(
        path, dtype=columns, keep_default_na=False, na_values=[""], encoding="utf-8-sig"
    )
    if list(frame.columns) != list(columns):
        raise ValueError(f"{path}: expected CSV headers in order: {', '.join(columns)}")
    return frame


def select_events(events: pd.DataFrame, event_id_to_run: int | None) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(columns=["EventID", "EventName"])
    if event_id_to_run is None:
        return events[["EventID", "EventName"]].drop_duplicates().copy()

    selected = (
        events.loc[
            events["EventID"] == int(event_id_to_run),
            ["EventID", "EventName"],
        ]
        .drop_duplicates()
        .copy()
    )
    if selected.empty:
        raise ValueError(
            f"EVENT_ID_TO_RUN={event_id_to_run} was not found in the events CSV"
        )
    return selected


def shape_points_to_polygons(
    shape_points: pd.DataFrame,
    crs: str,
) -> gpd.GeoDataFrame:
    required = {"EventID", "PolygonID", "Lat", "Long", "DrawOrder"}
    missing = required.difference(shape_points.columns)
    if missing:
        raise ValueError(f"Missing required shape point columns: {sorted(missing)}")

    if shape_points.empty:
        return gpd.GeoDataFrame(
            columns=["EventID", "PolygonID", "PointCount", "geometry"],
            geometry="geometry",
            crs=crs,
        )

    df = (
        shape_points.dropna(subset=list(required))
        .sort_values(["EventID", "PolygonID", "DrawOrder"])
        .copy()
    )
    rows: list[dict] = []
    for (event_id, polygon_id), group in df.groupby(
        ["EventID", "PolygonID"], sort=False
    ):
        coords = list(zip(group["Long"].astype(float), group["Lat"].astype(float)))
        if len(coords) < 3:
            continue
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        rows.append(
            {
                "EventID": int(event_id),
                "PolygonID": int(polygon_id),
                "PointCount": len(coords),
                "geometry": Polygon(coords),
            }
        )

    gdf = gpd.GeoDataFrame(rows, geometry="geometry", crs=crs)
    if not gdf.empty:
        invalid = ~gdf.geometry.is_valid
        if invalid.any():
            gdf.loc[invalid, "geometry"] = gdf.loc[invalid, "geometry"].buffer(0)
    return gdf


def exposures_to_points(exposures: pd.DataFrame, crs: str) -> gpd.GeoDataFrame:
    required = {"LOCID", "LATITUDE", "LONGITUDE", "GroundUpTIV", "PolicyAdjustedTIV"}
    missing = required.difference(exposures.columns)
    if missing:
        raise ValueError(
            f"Exposure data is missing required columns: {sorted(missing)}"
        )

    df = exposures.dropna(subset=["LATITUDE", "LONGITUDE"]).copy()
    df = df[
        df["LATITUDE"].between(-90, 90) & df["LONGITUDE"].between(-180, 180)
    ].reset_index(drop=True)
    df["_ExposureRowID"] = df.index.astype("int64")
    geometry = [
        Point(lon, lat)
        for lon, lat in zip(df["LONGITUDE"].astype(float), df["LATITUDE"].astype(float))
    ]
    return gpd.GeoDataFrame(df, geometry=geometry, crs=crs)


def load_event_polygons(
    shape_points: pd.DataFrame,
    pmls: pd.DataFrame,
    event_id: int,
    crs: str,
    fail_on_missing_pml: bool,
) -> tuple[gpd.GeoDataFrame, pd.DataFrame, pd.DataFrame]:
    polygons = shape_points_to_polygons(shape_points, crs)
    polygons_with_pml = polygons.merge(pmls, on=["EventID", "PolygonID"], how="left")
    if fail_on_missing_pml and not polygons_with_pml.empty:
        missing = polygons_with_pml["PML"].isna()
        if missing.any():
            polygon_ids = polygons_with_pml.loc[missing, "PolygonID"].tolist()
            raise ValueError(
                f"Event {event_id} has {len(polygon_ids)} polygon(s) without PML: "
                f"{polygon_ids[:20]}"
            )
    return polygons_with_pml, shape_points, pmls


def intersect_exposure_rows_with_polygons(
    exposure_points: gpd.GeoDataFrame,
    polygons: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    if exposure_points.empty or polygons.empty:
        return exposure_points.iloc[0:0].copy()

    joined = gpd.sjoin(
        exposure_points,
        polygons[["EventID", "PolygonID", "PML", "geometry"]],
        how="inner",
        predicate="intersects",
    ).drop(columns=["index_right"], errors="ignore")
    if joined.empty:
        return joined

    joined = (
        joined.sort_values(
            ["_ExposureRowID", "PML", "PolygonID"],
            ascending=[True, False, True],
            na_position="last",
        )
        .drop_duplicates(subset=["_ExposureRowID"], keep="first")
        .reset_index(drop=True)
    )
    joined["SourcePML"] = joined["PML"]
    joined["PMLOverrideApplied"] = False
    joined["GroundUpLoss"] = joined["GroundUpTIV"] * joined["PML"]
    joined["GULoss"] = joined["PolicyAdjustedTIV"] * joined["PML"]
    return joined


def build_account_breakdown(location_rows: pd.DataFrame) -> pd.DataFrame:
    if location_rows.empty:
        return pd.DataFrame()
    group_cols = [
        "EventID",
        "EventName",
        "SelectedPeril",
        "CEDANTID",
        "PORTACCTID",
        "PORTNAME",
        "PORTNUM",
        "CurrencyCode",
    ]
    group_cols = [c for c in group_cols if c in location_rows.columns]
    return (
        location_rows.groupby(group_cols, dropna=False)
        .agg(
            impacted_location_count=("LOCID", "nunique"),
            exposure_row_count=("_ExposureRowID", "count"),
            ground_up_tiv=("GroundUpTIV", "sum"),
            policy_adjusted_tiv=("PolicyAdjustedTIV", "sum"),
            ground_up_loss=("GroundUpLoss", "sum"),
            gross_loss_after_policy_terms=("GULoss", "sum"),
        )
        .reset_index()
        .sort_values(
            ["gross_loss_after_policy_terms", "policy_adjusted_tiv"],
            ascending=[False, False],
        )
    )


def build_location_breakout(location_rows: pd.DataFrame) -> pd.DataFrame:
    if location_rows.empty:
        return pd.DataFrame()
    group_cols = [
        "EventID",
        "EventName",
        "SelectedPeril",
        "LOCID",
        "LATITUDE",
        "LONGITUDE",
        "CountryCode",
        "CurrencyCode",
        "PolygonID",
        "SourcePML",
        "PML",
    ]
    group_cols = [c for c in group_cols if c in location_rows.columns]
    return (
        location_rows.groupby(group_cols, dropna=False)
        .agg(
            account_count=("PORTACCTID", "nunique"),
            portfolio_count=("PORTNUM", "nunique"),
            exposure_row_count=("_ExposureRowID", "count"),
            ground_up_tiv=("GroundUpTIV", "sum"),
            policy_adjusted_tiv=("PolicyAdjustedTIV", "sum"),
            ground_up_loss=("GroundUpLoss", "sum"),
            gross_loss_after_policy_terms=("GULoss", "sum"),
        )
        .reset_index()
        .sort_values(
            ["gross_loss_after_policy_terms", "policy_adjusted_tiv"],
            ascending=[False, False],
        )
    )


def build_run_summary(
    selected_events: pd.DataFrame,
    run_log: pd.DataFrame,
    location_rows: pd.DataFrame,
) -> pd.DataFrame:
    counts = (
        run_log["Status"].value_counts() if not run_log.empty else pd.Series(dtype=int)
    )
    return pd.DataFrame(
        {
            "metric": [
                "overall_status",
                "events_selected",
                "events_successful",
                "events_no_polygons",
                "events_no_impacted_exposures",
                "events_failed",
                "impacted_exposure_rows",
            ],
            "value": [
                "Complete with errors" if counts.get("Error", 0) else "Complete",
                len(selected_events),
                counts.get("Success", 0),
                counts.get("No polygons", 0),
                counts.get("No impacted exposures", 0),
                counts.get("Error", 0),
                len(location_rows),
            ],
        }
    )


def write_frame(df: pd.DataFrame, path: Path) -> None:
    """Write a useful empty CSV with no accidental pandas index."""
    df.to_csv(path, index=False)


def run_pipeline(config: RunConfig = CONFIG) -> dict[str, object]:
    """Calculate the selected events from CSVs and write the output pack."""
    output_dir = Path(config.output_dir)
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise ValueError(f"{output_dir}: use a new or empty output directory")

    # Read every required export before creating output files.
    events = read_source_csv(config.events_csv, EVENT_COLUMNS)
    shape_points = read_source_csv(config.shape_points_csv, SHAPE_COLUMNS)
    pmls = read_source_csv(config.pml_csv, PML_COLUMNS)
    edm_exposures = read_source_csv(config.edm_csv, EDM_COLUMNS)
    edm_exposures["TIV"] = edm_exposures["PolicyAdjustedTIV"]
    selected_events = select_events(events, config.event_id_to_run)
    if selected_events.empty:
        raise RuntimeError("No events were selected; nothing can be run")
    exposure_points = exposures_to_points(edm_exposures, config.crs_wgs84)
    shapes_by_event = shape_points.groupby("EventID", sort=False)
    pmls_by_event = pmls.groupby("EventID", sort=False)

    all_location_rows: list[pd.DataFrame] = []
    run_log_rows: list[dict] = []
    error_rows: list[dict] = []
    for row in selected_events.itertuples(index=False):
        event_id = int(row.EventID)
        event_name = str(row.EventName)
        try:
            event_shapes = (
                shapes_by_event.get_group(event_id)
                if event_id in shapes_by_event.indices
                else shape_points.iloc[:0]
            )
            event_pmls = (
                pmls_by_event.get_group(event_id)
                if event_id in pmls_by_event.indices
                else pmls.iloc[:0]
            )
            polygons, _, _ = load_event_polygons(
                event_shapes,
                event_pmls,
                event_id,
                config.crs_wgs84,
                config.fail_on_missing_pml,
            )
            if event_shapes.empty or polygons.empty:
                run_log_rows.append(
                    {
                        "EventID": event_id,
                        "EventName": event_name,
                        "Status": "No polygons",
                        "Rows": 0,
                    }
                )
                continue

            impacted = intersect_exposure_rows_with_polygons(exposure_points, polygons)
            if impacted.empty:
                run_log_rows.append(
                    {
                        "EventID": event_id,
                        "EventName": event_name,
                        "Status": "No impacted exposures",
                        "Rows": 0,
                    }
                )
                continue
            impacted["EventName"] = event_name
            impacted["SelectedPeril"] = impacted["PERIL"]
            all_location_rows.append(pd.DataFrame(impacted.drop(columns="geometry")))
            run_log_rows.append(
                {
                    "EventID": event_id,
                    "EventName": event_name,
                    "Status": "Success",
                    "Rows": len(impacted),
                }
            )
        # Keep event failures visible while calculating the remaining events.
        except Exception as exc:  # noqa: BLE001
            error_rows.append(
                {
                    "EventID": event_id,
                    "EventName": event_name,
                    "Error": f"{type(exc).__name__}: {exc}",
                }
            )
            run_log_rows.append(
                {
                    "EventID": event_id,
                    "EventName": event_name,
                    "Status": "Error",
                    "Rows": 0,
                }
            )

    location_rows = (
        pd.concat(all_location_rows, ignore_index=True)
        if all_location_rows
        else pd.DataFrame()
    )
    run_log = pd.DataFrame(run_log_rows)
    error_log = pd.DataFrame(error_rows, columns=["EventID", "EventName", "Error"])
    account_breakdown = build_account_breakdown(location_rows)
    location_breakout = build_location_breakout(location_rows)
    summary = build_run_summary(selected_events, run_log, location_rows)
    prefix = (
        "all_events"
        if config.event_id_to_run is None
        else f"event_{config.event_id_to_run}"
    )
    paths = {
        "summary": output_dir / f"{prefix}_summary.csv",
        "run_log": output_dir / f"{prefix}_run_log.csv",
        "error_log": output_dir / f"{prefix}_error_log.csv",
        "location_rows": output_dir / f"{prefix}_location_rows.csv",
        "account_breakdown": output_dir / f"{prefix}_account_breakdown.csv",
        "location_breakout": output_dir / f"{prefix}_location_breakout.csv",
        "edm_exposures": output_dir / "edm_exposures.csv",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_frame(summary, paths["summary"])
    write_frame(run_log, paths["run_log"])
    write_frame(error_log, paths["error_log"])
    write_frame(location_rows, paths["location_rows"])
    write_frame(account_breakdown, paths["account_breakdown"])
    write_frame(location_breakout, paths["location_breakout"])
    write_frame(edm_exposures, paths["edm_exposures"])

    return {
        "config": config,
        "events": events,
        "selected_events": selected_events,
        "edm_exposures": edm_exposures,
        "location_rows": location_rows,
        "account_breakdown": account_breakdown,
        "location_breakout": location_breakout,
        "run_log": run_log,
        "error_log": error_log,
        "summary": summary,
        "paths": paths,
        "has_errors": not error_log.empty,
    }


def main() -> int:

    try:
        results = run_pipeline(CONFIG)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}")
        return 1

    print("\nGlobal Exposures run finished")
    print(results["summary"].to_string(index=False))
    print("\nOutputs:")
    for name, path in results["paths"].items():
        print(f"  {name}: {path}")

    if results["has_errors"]:
        print("\nOne or more events failed. See the error log.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

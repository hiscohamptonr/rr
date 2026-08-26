"""Run geospatial event-loss calculations and write the CSV output pack.

External data sources:
- The ``GlobalExposures`` Microsoft SQL Server database (by default on
  ``PR0603-41001-00``): ``data.Events``, ``data.ShapeFiles``, and ``data.PML``.
- The configured EDM Microsoft SQL Server database (by default
  ``HISCO_UKEU_01JAN26_010126_ROLLUP_ByLOB_GC_v25_EDM`` on
  ``prod-lmrmsinsurance-db\\LMRMSinsurance``): ``dbo.loc``, ``dbo.loccvg``,
  ``dbo.policy``, ``dbo.accgrp``, ``dbo.portacct``, and ``dbo.portinfo``.

The pipeline consumes no input files or other external data feeds. Run all
configured events with ``python globalexposures/exposures.py`` or select one
with ``--event-id``.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from pathlib import Path
from urllib.parse import quote_plus

import geopandas as gpd
import pandas as pd
import sqlalchemy as sa
from shapely.geometry import Point, Polygon
from sqlalchemy.exc import SQLAlchemyError


# Default run configuration; CLI arguments override these values.
@dataclass(frozen=True)
class RunConfig:
    global_exposures_server: str = "PR0603-41001-00"
    global_exposures_db: str = "GlobalExposures"
    edm_server: str = r"prod-lmrmsinsurance-db\LMRMSinsurance"
    edm_db: str = "HISCO_UKEU_01JAN26_010126_ROLLUP_ByLOB_GC_v25_EDM"
    odbc_driver: str = "ODBC Driver 17 for SQL Server"

    # This value is applied to both loccvg.PERIL and policy.POLICYTYPE.
    # Confirm the required peril before production use. The previous notebook's
    # comment said 1 while its actual configured value was 4; this keeps the
    # actual behaviour (4) and removes the misleading comment.
    edm_peril_to_use: int = 4

    # None means all events. An integer means one event only.
    event_id_to_run: int | None = None
    portnum_filter: str | None = None
    output_dir: Path = Path("global_exposures_outputs")
    crs_wgs84: str = "EPSG:4326"

    # A missing polygon PML makes that event fail rather than silently writing
    # null losses.
    fail_on_missing_pml: bool = True


CONFIG = RunConfig()


@dataclass(frozen=True)
class SqlConfig:
    server: str
    database: str
    driver: str
    trusted_connection: bool = True
    trust_server_certificate: bool = True


def make_sql_server_engine(config: SqlConfig) -> sa.Engine:
    trusted = "yes" if config.trusted_connection else "no"
    trust_cert = "yes" if config.trust_server_certificate else "no"
    connection_string = (
        f"DRIVER={{{config.driver}}};"
        f"SERVER={config.server};"
        f"DATABASE={config.database};"
        f"Trusted_Connection={trusted};"
        f"TrustServerCertificate={trust_cert};"
    )
    return sa.create_engine(
        f"mssql+pyodbc:///?odbc_connect={quote_plus(connection_string)}",
        fast_executemany=True,
    )


def test_sql_connection(engine: sa.Engine) -> pd.DataFrame:
    sql = """
        SELECT
            @@SERVERNAME AS ServerName,
            DB_NAME() AS DatabaseName,
            SUSER_SNAME() AS LoginName,
            SYSDATETIME() AS ServerDateTime
    """
    return pd.read_sql(sql, engine)


def read_global_exposure_events(engine: sa.Engine) -> pd.DataFrame:
    return pd.read_sql(
        """
        SELECT EventID, EventName, EventDescription
        FROM data.Events
        ORDER BY EventID
        """,
        engine,
    )


def read_global_exposure_shape_points(engine: sa.Engine, event_id: int) -> pd.DataFrame:
    sql = sa.text("""
        SELECT ShapefileID, EventID, PolygonID, Lat, Long, DrawOrder
        FROM data.ShapeFiles
        WHERE EventID = :event_id
        ORDER BY EventID, PolygonID, DrawOrder
    """)
    return pd.read_sql(sql, engine, params={"event_id": int(event_id)})


def read_global_exposure_pmls(engine: sa.Engine, event_id: int) -> pd.DataFrame:
    sql = sa.text("""
        SELECT EventID, PolygonID, PML
        FROM data.PML
        WHERE EventID = :event_id
    """)
    return pd.read_sql(sql, engine, params={"event_id": int(event_id)})


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
            f"EVENT_ID_TO_RUN={event_id_to_run} was not found in "
            "GlobalExposures.data.Events"
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


def read_edm_exposures_cte(
    engine: sa.Engine,
    peril_to_use: int,
    portnum_filter: str | None,
) -> pd.DataFrame:
    line_factor_case = """
        CASE WHEN POL.BLANLIMAMT = 0 THEN 1 ELSE POL.BLANLIMAMT END
    """
    fa_qs_srp_case = """
        CASE
            WHEN PI.Portnum LIKE '%_QS' AND PI.Portnum LIKE '%_FA_%' THEN 0.5
            WHEN PI.Portnum LIKE '%_SRP' AND PI.Portnum LIKE '%_FA_%' THEN 0.3333333
            ELSE 1.0
        END
    """
    sql = sa.text(f"""
        WITH locs AS (
            SELECT
                L.LOCID, L.ACCGRPID, L.LOCNUM, L.LATITUDE, L.LONGITUDE,
                L.CNTRYCODE AS CountryCode, LC.PERIL,
                LC.VALUECUR AS CurrencyCode,
                SUM(LC.VALUEAMT) AS GroundUpTIV
            FROM dbo.loc L
            JOIN dbo.loccvg LC ON LC.LOCID = L.LOCID
            WHERE LC.PERIL = :peril_to_use
            GROUP BY
                L.LOCID, L.ACCGRPID, L.LOCNUM, L.LATITUDE, L.LONGITUDE,
                L.CNTRYCODE, LC.PERIL, LC.VALUECUR
        ),
        policy_terms AS (
            SELECT
                POL.ACCGRPID, POL.POLICYTYPE AS PERIL,
                MAX({line_factor_case}) AS POLICY_LINE_FACTOR
            FROM dbo.policy POL
            WHERE POL.POLICYTYPE = :peril_to_use
            GROUP BY POL.ACCGRPID, POL.POLICYTYPE
        ),
        account_portfolio AS (
            SELECT
                A.ACCGRPID, A.CEDANTID, PA.PORTACCTID,
                UPPER(PI.PORTNAME) AS PORTNAME, PI.Portnum AS PORTNUM,
                {fa_qs_srp_case} AS FA_QS_SRP_FACTOR
            FROM dbo.accgrp A
            JOIN dbo.portacct PA ON PA.ACCGRPID = A.ACCGRPID
            JOIN dbo.portinfo PI ON PI.PORTINFOID = PA.PORTINFOID
            WHERE (:portnum_filter IS NULL OR PI.Portnum = :portnum_filter)
        )
        SELECT
            AP.CEDANTID, AP.PORTACCTID, L.PERIL, L.LOCID, L.LOCNUM,
            L.LATITUDE, L.LONGITUDE, L.GroundUpTIV,
            L.GroundUpTIV * COALESCE(PT.POLICY_LINE_FACTOR, 1.0)
                * AP.FA_QS_SRP_FACTOR AS PolicyAdjustedTIV,
            L.CountryCode, L.CurrencyCode, AP.PORTNAME, AP.PORTNUM,
            COALESCE(PT.POLICY_LINE_FACTOR, 1.0) AS POLICY_LINE_FACTOR,
            AP.FA_QS_SRP_FACTOR, 'ALL' AS Coverage
        FROM locs L
        JOIN account_portfolio AP ON AP.ACCGRPID = L.ACCGRPID
        LEFT JOIN policy_terms PT
            ON PT.ACCGRPID = L.ACCGRPID AND PT.PERIL = L.PERIL
    """)
    df = pd.read_sql(
        sql,
        engine,
        params={
            "peril_to_use": int(peril_to_use),
            "portnum_filter": portnum_filter,
        },
    )
    df["TIV"] = df["PolicyAdjustedTIV"]
    return df


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
    engine: sa.Engine,
    event_id: int,
    crs: str,
    fail_on_missing_pml: bool,
) -> tuple[gpd.GeoDataFrame, pd.DataFrame, pd.DataFrame]:
    shape_points = read_global_exposure_shape_points(engine, event_id)
    polygons = shape_points_to_polygons(shape_points, crs)
    pmls = read_global_exposure_pmls(engine, event_id)
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
    """Run one event or every event and write the complete output pack."""
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    global_engine = make_sql_server_engine(
        SqlConfig(
            config.global_exposures_server,
            config.global_exposures_db,
            config.odbc_driver,
        )
    )
    edm_engine = make_sql_server_engine(
        SqlConfig(config.edm_server, config.edm_db, config.odbc_driver)
    )

    try:
        global_connection_check = test_sql_connection(global_engine)
        edm_connection_check = test_sql_connection(edm_engine)

        events = read_global_exposure_events(global_engine)
        selected_events = select_events(events, config.event_id_to_run)
        if selected_events.empty:
            raise RuntimeError("No events were selected; nothing can be run")

        edm_exposures = read_edm_exposures_cte(
            edm_engine,
            config.edm_peril_to_use,
            config.portnum_filter,
        )
        exposure_points = exposures_to_points(edm_exposures, config.crs_wgs84)

        all_location_rows: list[pd.DataFrame] = []
        run_log_rows: list[dict] = []
        error_rows: list[dict] = []

        for row in selected_events.itertuples(index=False):
            event_id = int(row.EventID)
            event_name = str(row.EventName)
            try:
                polygons, shape_points, _ = load_event_polygons(
                    global_engine,
                    event_id,
                    config.crs_wgs84,
                    config.fail_on_missing_pml,
                )
                if shape_points.empty or polygons.empty:
                    run_log_rows.append(
                        {
                            "EventID": event_id,
                            "EventName": event_name,
                            "Status": "No polygons",
                            "Rows": 0,
                        }
                    )
                    continue

                impacted = intersect_exposure_rows_with_polygons(
                    exposure_points, polygons
                )
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
                all_location_rows.append(
                    pd.DataFrame(impacted.drop(columns="geometry"))
                )
                run_log_rows.append(
                    {
                        "EventID": event_id,
                        "EventName": event_name,
                        "Status": "Success",
                        "Rows": len(impacted),
                    }
                )
            # Each event is an isolation boundary; retain any failure in the
            # output pack and continue processing the remaining configured events.
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
        write_frame(summary, paths["summary"])
        write_frame(run_log, paths["run_log"])
        write_frame(error_log, paths["error_log"])
        write_frame(location_rows, paths["location_rows"])
        write_frame(account_breakdown, paths["account_breakdown"])
        write_frame(location_breakout, paths["location_breakout"])
        write_frame(edm_exposures, paths["edm_exposures"])

        return {
            "config": config,
            "global_connection_check": global_connection_check,
            "edm_connection_check": edm_connection_check,
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
    finally:
        global_engine.dispose()
        edm_engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Global Exposures event losses and write the output pack."
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--event-id", type=int, help="Run one EventID only")
    scope.add_argument(
        "--all-events",
        action="store_true",
        help="Run all events (the default)",
    )
    parser.add_argument("--portnum", help="Optional exact PORTNUM filter")
    parser.add_argument("--peril", type=int, help="Override the configured EDM peril")
    parser.add_argument("--output-dir", type=Path, help="Override the output directory")
    parser.add_argument(
        "--allow-missing-pml",
        action="store_true",
        help="Allow polygons with missing PML instead of failing that event",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    event_id_to_run = (
        None
        if args.all_events
        else args.event_id
        if args.event_id is not None
        else CONFIG.event_id_to_run
    )
    config = replace(
        CONFIG,
        event_id_to_run=event_id_to_run,
        portnum_filter=(
            args.portnum if args.portnum is not None else CONFIG.portnum_filter
        ),
        edm_peril_to_use=(
            args.peril if args.peril is not None else CONFIG.edm_peril_to_use
        ),
        output_dir=(
            args.output_dir if args.output_dir is not None else CONFIG.output_dir
        ),
        fail_on_missing_pml=(
            False if args.allow_missing_pml else CONFIG.fail_on_missing_pml
        ),
    )

    try:
        results = run_pipeline(config)
    except (SQLAlchemyError, OSError, ValueError, RuntimeError) as exc:
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

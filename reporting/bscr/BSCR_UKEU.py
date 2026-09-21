"""Calculate BSCR and PRA CSV outputs from independently exported SQL results.

Run bscr/sql/bscr-extract.sql and/or pra/sql/pra-raw.sql on the database
machine, then copy their CSV exports to the calculation machine.
This script never connects to SQL Server or reads a workbook.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import polars as pl
from tabulate import tabulate

# EDIT THESE PATHS BEFORE RUNNING. Use None to skip a calculation.
# Example: PRA_INPUT_CSV = Path(r"C:\Returns\my PRA extract.csv")
BSCR_INPUT_CSV: Path | None = Path("aggs.csv")
PRA_INPUT_CSV: Path | None = None
OUTPUT_DIR = Path("output")


LOB_COLUMN = "userid1"
BSCR_ENTITIES = ("HIG", "HSA", "33", "3624", "HIC")
QS_PCT_RETENTION = 0.5
SRP_PCT_RETENTION = 0.3333
SOURCE_COLUMNS = [
    "pml",
    "accgrpid",
    "uwritrname",
    "state",
    "userid1",
    "branchname",
    "cntrycode",
    "is_geocoded",
]
PRA_RAW_COLUMNS = [
    "pml",
    "accgrpid",
    "uwritrname",
    "state",
    "userid1",
    "branchname",
    "cntrycode",
]
PRA_AGGREGATE_COLUMNS = ["pml", "state", "userid1", "cntrycode", "uwritrname"]


def print_source_summary(data: pl.DataFrame) -> None:
    """Print the same operational input summary shown by the notebook."""
    sum_agg = data.select(pl.sum("pml"))[0][0]
    print(
        tabulate(
            [
                ["variable", "value"],
                ["cwd", f"{Path.cwd()}"],
                ["selected data columns", data.columns],
                ["total pml agg in file", str(sum_agg)],
            ]
        )
    )


def which_entity(
    modelled_lob: str | None, valid_bscr_entities: Iterable[str]
) -> str | None:
    """Return the first BSCR entity code contained in a portfolio name."""
    if modelled_lob is None:
        return None
    modelled_lob_upper = str(modelled_lob).upper()
    for entity in valid_bscr_entities:
        entity_upper = entity.upper()
        if entity_upper in modelled_lob_upper:
            return entity_upper
    return None


def is_fa_qs(modelled_lob: str | None) -> bool:
    if modelled_lob is None:
        return False
    return "_QS" in str(modelled_lob).upper()


def is_fa_srp(modelled_lob: str | None) -> bool:
    if modelled_lob is None:
        return False
    return "_SRP" in str(modelled_lob).upper()


def is_nahu(countrycode: str | None, state: str | None) -> bool:
    valid_countries = {"US", "CB", "TC", "BH", "JM", "VI", "MX"}
    valid_us_states = {
        "Florida",
        "Texas",
        "Louisiana",
        "Mississippi",
        "Alabama",
        "North Carolina",
        "South Carolina",
        "New Jersey",
        "Virginia",
        "New York",
        "Connecticut",
        "Delaware",
        "Georgia",
    }

    if countrycode is None:
        return False
    if countrycode not in valid_countries:
        return False
    if countrycode == "US" and state is None:
        if state is None:
            return True
        if state not in valid_us_states:
            return False
    return True


def is_naeq(countrycode: str | None, state: str | None) -> bool:
    valid_countries = {"US", "CA"}
    valid_us_states = {
        "California",
        "Washington",
        "Oregon",
        "South Carolina",
        "Tennessee",
    }
    if countrycode is None:
        return False
    if countrycode not in valid_countries:
        return False
    if countrycode == "US":
        if state is None:
            return True
        if state not in valid_us_states:
            return False
    return True


def is_jp(cntrycode: str | None) -> bool:
    return cntrycode == "JP"


def is_eu(cntrycode: str | None) -> bool:
    valid_countries = {
        "GB",
        "UK",
        "FR",
        "DE",
        "BE",
        "NL",
        "LX",
        "AT",
        "DK",
        "SE",
        "PL",
        "CZ",
    }
    return cntrycode in valid_countries


def is_us_all(cntrycode: str | None) -> bool:
    return cntrycode == "US"


def classify_exposure(data: pl.DataFrame) -> pl.DataFrame:
    """Add BSCR entity, treaty, and regional classification columns."""
    return data.with_columns(
        [
            pl.col(LOB_COLUMN)
            .map_elements(
                lambda value: which_entity(value, BSCR_ENTITIES),
                return_dtype=pl.Utf8,
            )
            .alias("bscr_entity"),
            pl.col(LOB_COLUMN)
            .map_elements(is_fa_qs, return_dtype=pl.Boolean)
            .alias("is_qs"),
            pl.col(LOB_COLUMN)
            .map_elements(is_fa_srp, return_dtype=pl.Boolean)
            .alias("is_srp"),
            pl.struct(["cntrycode", "state"])
            .map_elements(
                lambda row: is_nahu(row["cntrycode"], row["state"]),
                return_dtype=pl.Boolean,
            )
            .alias("is_nahu"),
            pl.struct(["cntrycode", "state"])
            .map_elements(
                lambda row: is_naeq(row["cntrycode"], row["state"]),
                return_dtype=pl.Boolean,
            )
            .alias("is_na_eq"),
            pl.struct(["cntrycode"])
            .map_elements(lambda row: is_jp(row["cntrycode"]), return_dtype=pl.Boolean)
            .alias("is_jp"),
            pl.struct(["cntrycode"])
            .map_elements(lambda row: is_eu(row["cntrycode"]), return_dtype=pl.Boolean)
            .alias("is_eu"),
            pl.struct(["cntrycode"])
            .map_elements(
                lambda row: is_us_all(row["cntrycode"]), return_dtype=pl.Boolean
            )
            .alias("is_us_all"),
        ]
    )


def apply_retentions(data: pl.DataFrame) -> pl.DataFrame:
    """Apply the Fine Art QS and SRP retention percentages."""
    return data.with_columns(
        pl.when(pl.col("is_qs"))
        .then(pl.col("pml") * pl.lit(QS_PCT_RETENTION))
        .when(pl.col("is_srp"))
        .then(pl.col("pml") * pl.lit(SRP_PCT_RETENTION))
        .otherwise(pl.col("pml"))
        .alias("net")
    )


def aggregate_regional_wide(data: pl.DataFrame) -> pl.DataFrame:
    """Aggregate gross and net exposure across the regional flags."""
    group_columns = [
        "bscr_entity",
        "is_nahu",
        "is_na_eq",
        "is_jp",
        "is_eu",
        "is_us_all",
        "is_geocoded",
        "cntrycode",
    ]
    return (
        data.group_by(group_columns)
        .agg(
            [
                pl.sum("pml").alias("sum_pml"),
                pl.sum("net").alias("sum_net"),
                pl.len().alias("count_policies"),
            ]
        )
        .sort(group_columns)
    )


def reshape_regional_exposure(wide_regions: pl.DataFrame) -> pl.DataFrame:
    """Convert true regional flags to one row per region and grouping key."""
    region_flags = ["is_nahu", "is_na_eq", "is_jp", "is_eu", "is_us_all"]
    return (
        wide_regions.unpivot(
            index=[
                "bscr_entity",
                "sum_pml",
                "sum_net",
                "count_policies",
                "is_geocoded",
                "cntrycode",
            ],
            on=region_flags,
            variable_name="region",
            value_name="in_region",
        )
        .filter(pl.col("in_region"))
        .group_by(["bscr_entity", "region", "is_geocoded", "cntrycode"])
        .agg(
            [
                pl.sum("sum_pml").alias("sum_pml"),
                pl.sum("sum_net").alias("sum_net"),
                pl.sum("count_policies").alias("count_policies"),
            ]
        )
    )


def aggregate_all_exposure(data: pl.DataFrame) -> pl.DataFrame:
    """Aggregate the all-regions rows in the final output schema."""
    return (
        data.group_by(["bscr_entity", "is_geocoded", "cntrycode"])
        .agg(
            [
                pl.sum("pml").alias("sum_pml"),
                pl.sum("net").alias("sum_net"),
                pl.len().alias("count_policies"),
            ]
        )
        .with_columns(pl.lit("ALL").alias("region"))
        .select(
            [
                "cntrycode",
                "bscr_entity",
                "region",
                "sum_pml",
                "sum_net",
                "count_policies",
                "is_geocoded",
            ]
        )
    )


def combine_region_outputs(
    regional_exposure: pl.DataFrame, all_exposure: pl.DataFrame
) -> pl.DataFrame:
    """Combine regional and all-regions aggregates in the export schema."""
    output_columns = [
        "cntrycode",
        "bscr_entity",
        "region",
        "sum_pml",
        "sum_net",
        "count_policies",
        "is_geocoded",
    ]
    return pl.concat([regional_exposure.select(output_columns), all_exposure]).sort(
        ["region", "bscr_entity", "is_geocoded", "cntrycode"]
    )


def build_bscr_output(source_data: pl.DataFrame) -> pl.DataFrame:
    """Transform queried exposure to the BSCR export; currency conversion is excluded."""
    classified = classify_exposure(source_data)
    retained = apply_retentions(classified)
    wide_regions = aggregate_regional_wide(retained)
    regional_exposure = reshape_regional_exposure(wide_regions)
    all_exposure = aggregate_all_exposure(retained)
    return combine_region_outputs(regional_exposure, all_exposure)


def build_pra_raw_output(source_data: pl.DataFrame) -> pl.DataFrame:
    """Return the source rows in the PRA earthquake-workbook column order."""
    return source_data.select(PRA_RAW_COLUMNS)


def build_pra_aggregate_output(source_data: pl.DataFrame) -> pl.DataFrame:
    """Group source rows into the five-column PRA pivot input contract."""
    return (
        source_data.group_by(
            ["state", "userid1", "cntrycode", "uwritrname"],
            maintain_order=True,
        )
        .agg(pl.sum("pml").alias("pml"))
        .select(PRA_AGGREGATE_COLUMNS)
    )


def write_csv(data: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data.write_csv(path)


def load_source_csv(path: Path, columns: list[str]) -> pl.DataFrame:
    """Read SQL exports without inferring identifiers or country codes as numbers."""
    schema: dict[str, type[pl.DataType]] = {column: pl.String for column in columns}
    schema["pml"] = pl.Float64
    if "is_geocoded" in columns:
        schema["is_geocoded"] = pl.UInt8
    data = pl.read_csv(path, schema_overrides=schema)
    if data.columns != columns:
        raise ValueError(f"{path}: expected CSV headers in order: {', '.join(columns)}")
    if data.is_empty():
        raise ValueError(f"{path}: the source export contains no data rows")
    if data["pml"].null_count() or not data["pml"].is_finite().all():
        raise ValueError(f"{path}: pml must contain finite numbers without blanks")
    if "is_geocoded" in columns and (
        data["is_geocoded"].null_count() or not data["is_geocoded"].is_in([0, 1]).all()
    ):
        raise ValueError(f"{path}: is_geocoded must contain 0 or 1")
    return data


def run_pipeline(
    output_dir: Path,
    *,
    bscr_input: Path | None = None,
    pra_input: Path | None = None,
) -> dict[str, Path]:
    """Calculate one snapshot/peril run from CSVs, without database access."""
    if bscr_input is None and pra_input is None:
        raise ValueError("set BSCR_INPUT_CSV or PRA_INPUT_CSV at the top of this file")
    if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
        raise ValueError(f"{output_dir}: use a new or empty output directory")

    # Load all requested inputs before creating any outputs.
    bscr_source = (
        load_source_csv(bscr_input, SOURCE_COLUMNS) if bscr_input is not None else None
    )
    pra_source = (
        load_source_csv(pra_input, PRA_RAW_COLUMNS) if pra_input is not None else None
    )
    outputs: dict[str, Path] = {}
    if bscr_source is not None:
        print("BSCR source:", bscr_input)
        print_source_summary(bscr_source)
        destination = output_dir / "bscr-output.csv"
        write_csv(build_bscr_output(bscr_source), destination)
        outputs["bscr"] = destination
    if pra_source is not None:
        print("PRA source:", pra_input)
        print_source_summary(pra_source)
        raw_destination = output_dir / "pra-raw.csv"
        aggregate_destination = output_dir / "pra-aggregate.csv"
        write_csv(build_pra_raw_output(pra_source), raw_destination)
        write_csv(build_pra_aggregate_output(pra_source), aggregate_destination)
        outputs["pra_raw"] = raw_destination
        outputs["pra_aggregate"] = aggregate_destination
    return outputs


def main() -> None:
    try:
        outputs = run_pipeline(
            OUTPUT_DIR, bscr_input=BSCR_INPUT_CSV, pra_input=PRA_INPUT_CSV
        )
    except (OSError, ValueError, pl.exceptions.PolarsError) as error:
        raise SystemExit(f"Error: {error}") from error
    for destination in outputs.values():
        print("Wrote:", destination)


if __name__ == "__main__":
    main()

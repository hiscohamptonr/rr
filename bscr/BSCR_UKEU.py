"""Produce BSCR aggregate outputs from Microsoft SQL Server.

External data sources: the configured SQL Server database's ``loccvg``, ``loc``,
``policy``, and ``accgrp`` tables.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Sequence
from pathlib import Path
from urllib.parse import quote_plus

import polars as pl
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from tabulate import tabulate

DEFAULT_SERVER = r"pr0503-14002-00\LMRMSINSURANCE"
DEFAULT_DATABASE = "HISCO_UKEU_01JAN26_010126_ROLLUP_ByLOB_GC_v25_EDM"
DEFAULT_ENCRYPT = "yes"
DEFAULT_TRUST_SERVER_CERTIFICATE = "yes"
DEFAULT_OUTPUT = Path("output.csv")
DEFAULT_PERIL = 1
DEFAULT_POLICY_TYPE = 1
CONNECTION_TIMEOUT_SECONDS = 30

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

QUERY = """


with loc_tiv as (
	select
		locid,
		peril,
		deductamt,
		deductcur,
		sum(valueamt) valueamt

	from loccvg
	where peril = :peril
	group by
		locid,
		peril,
		deductamt,
		deductcur,
		limitamt,
		limitcur

	)



, gross_loctiv as (


	select
		case when valueamt < deductamt then 0
		else valueamt
		end as pml,
		*

		from loc_tiv

)


, selected_locs as (

select  locid, accgrpid, locnum,
case when addrmatch = 0 then 0 else 1 end as is_geocoded,
case when cntrycode = 'US' then state else '' end as state,
cntrycode, country
from loc

	)


, loc_exposure as (

	select

	sum(gross_loctiv.pml) as pml,
	selected_locs.accgrpid,
	state, cntrycode, country,
	is_geocoded
	from gross_loctiv
	inner join selected_locs on selected_locs.locid = gross_loctiv.locid
	group by accgrpid, state, cntrycode, country, is_geocoded

	)


, policies as (

	select distinct policy.accgrpid, policyid, partof,
	case when blanlimamt = 0 then 0 else partof end as policy_limit,
	undcovamt, blandedamt, accgrp.userid1, accgrp.branchname, accgrp.UWritrname, is_geocoded
	from policy
	inner join accgrp on accgrp.accgrpid = policy.accgrpid
	inner join  loc_exposure on loc_exposure.accgrpid = accgrp.accgrpid and loc_exposure.accgrpid = policy.accgrpid
	where policy.policytype = :policy_type

	)



, policy_exposure as (

		select
			case when sum(pml) > policy_limit then policy_limit else sum(pml) end as pml,
			policies.accgrpid,
			uwritrname,
			state,
			userid1,
			branchname,
			cntrycode,
			policies.is_geocoded
	from loc_exposure
	inner join policies on policies.accgrpid = loc_exposure.accgrpid
	group by
			policies.accgrpid,
			uwritrname,
			state,
			userid1,
			branchname,
			cntrycode,
			policies.is_geocoded,
			policy_limit

	)




select sum(pml) as pml, accgrpid, uwritrname, state, userid1, branchname, cntrycode, is_geocoded from policy_exposure
group by state, cntrycode, userid1, uwritrname, branchname, is_geocoded, accgrpid
order by sum(pml) desc

"""

# This is the same query family without the BSCR-only geocoding split. Its
# output grain matches raw_data_for_bscr_splits_eq in PRA_BSCR_Aggs.xlsx.
PRA_QUERY = """
with loc_tiv as (
	select
		locid,
		peril,
		deductamt,
		deductcur,
		sum(valueamt) valueamt
	from loccvg
	where peril = :peril
	group by
		locid,
		peril,
		deductamt,
		deductcur,
		limitamt,
		limitcur
),
gross_loctiv as (
	select
		case when valueamt < deductamt then 0 else valueamt end as pml,
		*
	from loc_tiv
),
selected_locs as (
	select
		locid,
		accgrpid,
		locnum,
		case when cntrycode = 'US' then state else '' end as state,
		cntrycode,
		country
	from loc
),
loc_exposure as (
	select
		sum(gross_loctiv.pml) as pml,
		selected_locs.accgrpid,
		state,
		cntrycode,
		country
	from gross_loctiv
	inner join selected_locs on selected_locs.locid = gross_loctiv.locid
	group by accgrpid, state, cntrycode, country
),
policies as (
	select distinct
		policy.accgrpid,
		policyid,
		partof,
		case when blanlimamt = 0 then 0 else partof end as policy_limit,
		undcovamt,
		blandedamt,
		accgrp.userid1,
		accgrp.branchname,
		accgrp.uwritrname
	from policy
	inner join accgrp on accgrp.accgrpid = policy.accgrpid
	inner join loc_exposure on loc_exposure.accgrpid = accgrp.accgrpid
		and loc_exposure.accgrpid = policy.accgrpid
	where policy.policytype = :policy_type
),
policy_exposure as (
	select
		case when pml > policy_limit then policy_limit else pml end as pml,
		policies.accgrpid,
		uwritrname,
		state,
		userid1,
		branchname,
		cntrycode
	from loc_exposure
	inner join policies on policies.accgrpid = loc_exposure.accgrpid
)
select pml, accgrpid, uwritrname, state, userid1, branchname, cntrycode
from policy_exposure
order by pml desc
"""


def build_engine(
    server: str = DEFAULT_SERVER,
    database: str = DEFAULT_DATABASE,
    encrypt: str = DEFAULT_ENCRYPT,
    trust_server_certificate: str = DEFAULT_TRUST_SERVER_CERTIFICATE,
) -> Engine:
    """Create the SQLAlchemy engine without opening a connection."""
    odbc_connection_string = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server={server};"
        f"Database={database};"
        "Trusted_Connection=yes;"
        f"Encrypt={encrypt};"
        f"TrustServerCertificate={trust_server_certificate};"
        f"Connection Timeout={CONNECTION_TIMEOUT_SECONDS};"
    )
    return create_engine(
        "mssql+pyodbc:///?odbc_connect=" + quote_plus(odbc_connection_string),
        fast_executemany=True,
        pool_pre_ping=True,
    )


def check_connection(engine: Engine) -> None:
    """Verify that SQL Server accepts a connection before running the query."""
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1 AS ok")).scalar()
    assert result == 1


def load_exposure(
    engine: Engine,
    peril: int = DEFAULT_PERIL,
    policy_type: int = DEFAULT_POLICY_TYPE,
) -> pl.DataFrame:
    """Run the BSCR exposure query and retain the pipeline's source columns."""
    return pl.read_database(
        text(QUERY),
        engine,
        execute_options={"parameters": {"peril": peril, "policy_type": policy_type}},
    ).select(SOURCE_COLUMNS)


def load_pra_exposure(
    engine: Engine,
    peril: int,
    policy_type: int,
) -> pl.DataFrame:
    """Run the non-geocoded query at the PRA raw-workbook grain."""
    return pl.read_database(
        text(PRA_QUERY),
        engine,
        execute_options={"parameters": {"peril": peril, "policy_type": policy_type}},
    ).select(PRA_RAW_COLUMNS)


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


def run_pipeline(
    server: str = DEFAULT_SERVER,
    database: str = DEFAULT_DATABASE,
    encrypt: str = DEFAULT_ENCRYPT,
    trust_server_certificate: str = DEFAULT_TRUST_SERVER_CERTIFICATE,
    output: Path = DEFAULT_OUTPUT,
    peril: int = DEFAULT_PERIL,
    policy_type: int = DEFAULT_POLICY_TYPE,
    source_output: Path | None = None,
    pra_raw_output: Path | None = None,
    pra_aggregate_output: Path | None = None,
) -> pl.DataFrame:
    """Load, transform, and export the BSCR aggregates."""
    engine = build_engine(server, database, encrypt, trust_server_certificate)
    pra_source_data = None
    try:
        check_connection(engine)
        source_data = load_exposure(engine, peril, policy_type)
        if pra_raw_output is not None or pra_aggregate_output is not None:
            pra_source_data = load_pra_exposure(engine, peril, policy_type)
    finally:
        engine.dispose()

    print_source_summary(source_data)
    if source_output is not None:
        write_csv(source_data, source_output)
    if pra_raw_output is not None:
        assert pra_source_data is not None
        write_csv(build_pra_raw_output(pra_source_data), pra_raw_output)
    if pra_aggregate_output is not None:
        assert pra_source_data is not None
        write_csv(build_pra_aggregate_output(pra_source_data), pra_aggregate_output)
    final_output = build_bscr_output(source_data)
    write_csv(final_output, output)
    return final_output


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Produce the BSCR UKEU aggregate CSV from SQL Server exposure data."
    )
    parser.add_argument("--server", default=DEFAULT_SERVER, help="SQL Server instance")
    parser.add_argument(
        "--database", default=DEFAULT_DATABASE, help="SQL Server database name"
    )
    parser.add_argument(
        "--encrypt",
        choices=("yes", "no"),
        default=DEFAULT_ENCRYPT,
        help="ODBC connection encryption setting (default: %(default)s)",
    )
    parser.add_argument(
        "--trust-server-certificate",
        choices=("yes", "no"),
        default=DEFAULT_TRUST_SERVER_CERTIFICATE,
        help="ODBC certificate trust setting (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="output CSV path (default: %(default)s)",
    )
    parser.add_argument(
        "--peril",
        type=int,
        default=DEFAULT_PERIL,
        help="loccvg peril code (default: %(default)s)",
    )
    parser.add_argument(
        "--policy-type",
        type=int,
        default=DEFAULT_POLICY_TYPE,
        help="policy type code (default: %(default)s)",
    )
    parser.add_argument(
        "--source-output",
        type=Path,
        help="optional geocoded BSCR account-level source CSV",
    )
    parser.add_argument(
        "--pra-raw-output",
        type=Path,
        help="optional PRA-shaped non-geocoded account-level source CSV",
    )
    parser.add_argument(
        "--pra-aggregate-output",
        type=Path,
        help="optional five-column PRA pivot-input CSV",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_argument_parser().parse_args(argv)
    run_pipeline(
        server=args.server,
        database=args.database,
        encrypt=args.encrypt,
        trust_server_certificate=args.trust_server_certificate,
        output=args.output,
        peril=args.peril,
        policy_type=args.policy_type,
        source_output=args.source_output,
        pra_raw_output=args.pra_raw_output,
        pra_aggregate_output=args.pra_aggregate_output,
    )


if __name__ == "__main__":
    main()

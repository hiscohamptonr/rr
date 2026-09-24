# This workbook connects to an xlsx file to generate the output for BSCR
# I left the sql query in the sql cell in cell 2 but the actualprocess
# just used an xlsx file that contaiend the same data

import marimo

__generated_with = "0.21.1"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    _df = mo.sql(
        f"""

        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Producing BSCR Agg outputs for Retail
    1. Run the SQL Query in cell 1 tests connection
    2. Query to select exposure in cell 2
    3. Loads this to polars -> creates functions to split out region perils
    4. sum and group by
    5. DOES NOT DO Currency conversion, do this after
    """)
    return


@app.cell
def _():
    from sqlalchemy import create_engine, text
    import polars as pl
    from urllib.parse import quote_plus
    import pyodbc

    # -------------------------
    # CONFIG (edit me)
    # -------------------------
    SERVER = r"pr0503-14002-00\LMRMSINSURANCE"
    DATABASE = "HISCO_UKEU_01JAN26_010126_ROLLUP_ByLOB_GC_v25_EDM"

    # SSL behaviour (ODBC Driver 18 encrypts by default)
    ENCRYPT = "yes"  # "yes" recommended
    TRUST_SERVER_CERT = "yes"  # set to "no" if cert name matches (production ideal)

    ODBC_CONNECTION_STRING = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server={SERVER};"
        f"Database={DATABASE};"
        "Trusted_Connection=yes;"
        f"Encrypt={ENCRYPT};"
        f"TrustServerCertificate={TRUST_SERVER_CERT};"
        "Connection Timeout=30;"
    )

    # SQLAlchemy engine
    engine = create_engine(
        "mssql+pyodbc:///?odbc_connect=" + quote_plus(ODBC_CONNECTION_STRING),
        fast_executemany=True,
        pool_pre_ping=True,  # helps with stale connections
    )

    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 AS ok")).scalar()
    assert result == 1
    return engine, pl


@app.cell
def _():

    query = """


    with loc_tiv as (
    	select
    		locid,
    		peril,
    		deductamt,
    		deductcur,
    		sum(valueamt) valueamt

    	from loccvg
    	where peril = 1
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
    	where policy.policytype = 1

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




    select sum(pml) as pml, accgrpid, state,userid1,cntrycode,uwritrname,is_geocoded from policy_exposure
    group by state,cntrycode,userid1,uwritrname,is_geocoded, accgrpid
    order by sum(pml) desc

    """
    return (query,)


@app.cell
def _(engine, pl, query):
    import marimo as mo
    from pathlib import Path
    from tabulate import tabulate
    from typing import Iterable, Optional

    # set the columns u want
    COLUMNS_IN_EXCEL_TABLE = [
        "pml",
        "accgrpid",
        "uwritrname",
        "state",
        "userid1",
        "cntrycode",
    ]

    # This is the column that contains the portfolio name to define the entity / is_Fine Art or not
    LOB_COLUMN = "userid1"

    ## Define the BSCR Entities
    BSCR_ENTITIES = ["HIG", "HSA", "33", "3624", "HIC"]

    ## QS on Fine Art
    QS_PCT_RETENTION = 0.5
    SRP_PCT_RETENTION = 0.3333

    ## NOTE: You can change this line to debug a failed connection and
    ## connect directly to a csv using read_csv instead.
    df = pl.read_database(query, engine)

    df = df.select(
        [
            "pml",
            "accgrpid",
            "uwritrname",
            "state",
            "userid1",
            "cntrycode",
            "is_geocoded",
        ]
    )
    sumAgg = df.select(pl.sum("pml"))[0][0]

    print(
        tabulate(
            [
                ["variable", "value"],
                ["cwd", f"{Path.cwd()}"],
                ["selected data columns", df.columns],
                ["total pml agg in file", str(sumAgg)],
            ]
        )
    )
    return (
        BSCR_ENTITIES,
        Iterable,
        LOB_COLUMN,
        Optional,
        QS_PCT_RETENTION,
        SRP_PCT_RETENTION,
        df,
        mo,
    )


@app.cell
def _(df):
    # Check what we are working with
    df.head()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Write functions to bucket exposure
    We write some functions  sql to decide which BSCR template we shove the data in
    """)
    return


@app.cell
def _(Iterable, Optional):
    def which_entity(
        modelled_lob: str, valid_bscr_entities: Iterable[str]
    ) -> Optional[str]:
        if modelled_lob is None:
            return None
        s = str(modelled_lob).upper()
        for ent in valid_bscr_entities:
            ent_u = ent.upper()
            if ent_u in s:  # substring check
                return ent_u
        return None

    def is_fa_qs(modelled_lob: str) -> bool:
        if modelled_lob is None:
            return False
        return "_QS" in str(modelled_lob).upper()

    def is_fa_srp(modelled_lob: str) -> bool:
        if modelled_lob is None:
            return False
        return "_SRP" in str(modelled_lob).upper()

    def is_nahu(countrycode: str, state: Optional[str]) -> bool:
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
        if countrycode == 'US' and state is None:
            if state is None:
                return True
            if state not in valid_us_states:
                return False
        return True

    def is_naeq(countrycode: str, state: Optional[str]) -> bool:
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

    def is_jp(cntrycode: str) -> bool:
        valid_countries = {"JP"}
        if cntrycode is None:
            return False
        if cntrycode not in valid_countries:
            return False
        return True

    def is_eu(cntrycode: str) -> bool:
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
        if cntrycode is None:
            return False
        if cntrycode not in valid_countries:
            return False
        return True

    def is_us_all(cntrycode: str) -> bool:
        valid_countries = {"US"}
        if cntrycode is None:
            return False
        if cntrycode not in valid_countries:
            return False
        return True

    return (
        is_eu,
        is_fa_qs,
        is_fa_srp,
        is_jp,
        is_naeq,
        is_nahu,
        is_us_all,
        which_entity,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Map these functions to polars and apply to the data
    """)
    return


@app.cell
def _(
    BSCR_ENTITIES,
    LOB_COLUMN,
    df,
    is_eu,
    is_fa_qs,
    is_fa_srp,
    is_jp,
    is_naeq,
    is_nahu,
    is_us_all,
    pl,
    which_entity,
):

    df2 = df.with_columns(
        [
            pl.col(LOB_COLUMN)
            .map_elements(
                lambda x: which_entity(x, BSCR_ENTITIES), return_dtype=pl.Utf8
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
                lambda r: is_nahu(r["cntrycode"], r["state"]), return_dtype=pl.Boolean
            )
            .alias("is_nahu"),
            pl.struct(["cntrycode", "state"])
            .map_elements(
                lambda r: is_naeq(r["cntrycode"], r["state"]), return_dtype=pl.Boolean
            )
            .alias("is_na_eq"),
            pl.struct(["cntrycode"])
            .map_elements(lambda r: is_jp(r["cntrycode"]), return_dtype=pl.Boolean)
            .alias("is_jp"),
            pl.struct(["cntrycode"])
            .map_elements(lambda r: is_eu(r["cntrycode"]), return_dtype=pl.Boolean)
            .alias("is_eu"),
            pl.struct(["cntrycode"])
            .map_elements(lambda r: is_us_all(r["cntrycode"]), return_dtype=pl.Boolean)
            .alias("is_us_all"),
        ]
    )
    return (df2,)


@app.cell
def _(df2):
    df2.head()
    return


@app.cell
def _(QS_PCT_RETENTION, SRP_PCT_RETENTION, df2, pl):
    df3 = df2.with_columns(
        pl.when(pl.col("is_qs"))
        .then(pl.col("pml") * pl.lit(QS_PCT_RETENTION))
        .when(pl.col("is_srp"))
        .then(pl.col("pml") * pl.lit(SRP_PCT_RETENTION))
        .otherwise(pl.col("pml"))
        .alias("net")
    )
    df3.columns
    return (df3,)


@app.cell
def _(df3):
    df3
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Final stage: Sum / group by the calculated columns
    Yes polars is a bit esoteric and not ideal for this, but it got the job done. Easiest way to see
    what is going on here is just run the cells. it's grouping, summing and concating outputs
    """)
    return


@app.cell
def _(df3, pl):

    group_cols = [
        "bscr_entity",
        "is_nahu",
        "is_na_eq",
        "is_jp",
        "is_eu",
        "is_us_all",
        "is_geocoded",
        "cntrycode",
    ]

    wide_format_regions = (
        df3.group_by(group_cols)
        .agg(
            [
                pl.sum("pml").alias("sum_pml"),
                pl.sum("net").alias("sum_net"),
                pl.len().alias("count_policies"),
            ]
        )
        .sort(group_cols)
    )

    wide_format_regions
    return (wide_format_regions,)


@app.cell
def _(pl, wide_format_regions):
    region_flags = ["is_nahu", "is_na_eq", "is_jp", "is_eu", "is_us_all"]

    regional_long = (
        wide_format_regions.unpivot(
            index=[
                "bscr_entity",
                "sum_pml",
                "sum_net",
                "count_policies",
                "is_geocoded",
                "cntrycode"
            ],
            on=region_flags,
            variable_name="region",
            value_name="in_region",
        )
        .filter(pl.col("in_region"))  # keep only True rows
        .group_by(["bscr_entity", "region", "is_geocoded", "cntrycode"])
        .agg(
            [
                pl.sum("sum_pml").alias("sum_pml"),
                pl.sum("sum_net").alias("sum_net"),
                pl.sum("count_policies").alias("count_policies"),
            ]
        )
    )
    regional_long
    return (regional_long,)


@app.cell
def _(df3, pl):
    all_long = (
        df3.group_by(["bscr_entity", "is_geocoded", "cntrycode"])
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
    all_long
    return (all_long,)


@app.cell
def _(all_long, pl, regional_long):
    final_long = pl.concat(
        [
            regional_long.select(
                [
                    "cntrycode",
                    "bscr_entity",
                    "region",
                    "sum_pml",
                    "sum_net",
                    "count_policies",
                    "is_geocoded",
                ]
            ),
            all_long,
        ]
    ).sort(["region", "bscr_entity", "is_geocoded", "cntrycode"])
    final_long
    return (final_long,)


@app.cell
def _(final_long):
    final_long.write_csv("output.csv")
    return


if __name__ == "__main__":
    app.run()

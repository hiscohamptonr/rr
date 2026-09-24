# Intro
This project describes three main categories of work relating to the UKEU Retail rollup.
- The rollup itself
- The data validation process
- Regulatory reporting

## Rollup
The documentation for the rollup is hosted on Azure and can also be viewed via the Dataiku project.
See the [rollup README](rollup/readme.md).

## Validation
Similarly, validation documentation is hosted on Azure and viewable in Dataiku.
See the [validation README](validation/readme.md).

## Reporting
Start with the [reporting guides](reporting/README.md), particularly the
[BSCR SQL-only workflow](reporting/docs/bscr/runbook.md).

## Key information

### SQL Servers
The primary SQL server is:
pr0503-14002-00\LMRMSINSURANCE

This is used for UK to attach EDMs and historically RDMs.
Going forward it will be not strictly necessary to attach RDMs for the rollup
as flat files in csv or parquet are used by the dataiku rollup process.



# Intro
This project describes three main categories of work relating to the UKEU Retail rollup.
- The rollup itself
- The data validaiton process
- Regulatory reporting

## Rollup
The documentation for the rollup is hosted on Azure and can also be viewed via the Dataiku project.
See the readme file in the ./rollup folder for this.

## Validation
Similar to rollup the documentation is hosted on Azure and viewable on dataiku.
See the ./validaiton folder readme file.

## Reporting
The documentation is hosted in ./reporting/docs

## Key information

### SQL Servers
The primary SQL server is:
pr0503-14002-00\LMRMSINSURANCE

This is used for UK to attach EDMs and historically RDMs.
Going forward it will be not strictly necessary to attach RDMs for the rollup
as flat files in csv or parquet are used by the dataiku rollup process.



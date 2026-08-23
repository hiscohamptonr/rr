# Intro
This script produces aggregates/limits and policy counts for the
BSCR return.

## Material assumptions
It contains known errors and assumptions, these are:
1. Potentially not 100% accuracy on which region counts as
Hurricane region in USA.
2. Potential double counting on policies between US states and countries
especially prominent when filling out the All World policy count.

These errors were deemed immaterial for the return.


## Other assumptions
The SQL query used to generate aggregates for the BSCR is the
exact same query as used for the PRA return.

This query was hand written at short notice and therefore contains
simplifications and corner-cuts to produce reasonable exposures.

The original query was tested against a Risklink aggregation output
and the total aggregate was similar, but not identical.

This means there are policy terms not captured by the query, which is
expected given the constraints but they were again deemed immaterial.

## Output
The procedure outputs raw csv file with pre-calculated limits and
policy counts. It needs slight manipulation in Excel to calculate
the difference between All World and US only.

This years output I created 3 pivot tables and did a quick diff to
calculate this.

## Procedure
The step by step procedure to re-run this analysis is
in a runbook stored locally here:
[BSCR Runbook](bscr-runbook.md)


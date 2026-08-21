# Intro
This repo contains documentation for completing UKEU retail rollup aggregates and
regulatory returns.

- Aggs for BSCR
- Aggs from EDM script
- Aggs for PRA return
- Global exposures
- Contingency RDS

## IMPORTANT
The aggs from EDM script was coded up in a rush and was measured against
GC and London market team outputs to verify it was correct within a small percentage.

It will not work on any EDM, just the EDM format we were given from GC in 2026.

## BSCR
BSCR uses this as a base and runs the output through some functions to breakout
what the bscr needs:
- Tables for each region peril, e.g. nahu, naeq and so on


## Amending the bscr output
Main real world problem in the script is hardcoding the group by columns
this occurs in several places after df3 has been created.


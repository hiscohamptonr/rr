# \---

Time: 3h

Purpose: Produce aggregates for "Global Exposures" Report

Concerns: Embedded SQL Script may need updating each year if EDM format changes

Concerns2: Fine Art QS implementation



\---

# 

# 

# Intro

This is a simple re-write of the global exposures tool.
Previously an R script and now re-written in a python notebook.

## 

\## difference to old R tool

The new tool has various features that the R script did not:

1. Maps a zoomable html map for given footprints
2. Runs individual footprints or bulk
3. outputs clean .csv output ready to be queried



## SQL Code

The notebook contains an embedded SQL script to read data from EDM.


Over time this will potentially need rebuilding, or the script should
potentially read from a flat file of exposures instead of connecting/querying
sql directly.



## Outputs

Go into specified directory or ./global\_exposures\_outputs as .csv files.



## Reinsurance

As per the previous script there is a major limitation with how Fine Art
reinsurance is done. It is still done in an embedded way inside the SQL script
functions.

Still, this is better than the previous one but users will need to edit this
as reinsurance changes.


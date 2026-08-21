# \---

Time: 3h

Data: Contained in sql script in workbook see SQL tab

Purpose: Produce aggregates for BSCR

\---

# 

# Intro

This folder produces the PRA return for January/February



# Lookups

Region\_mappings file is used to map to PRA regions

# Sequence

Open PRA\_BSCR\_Aggs

* Open the 'sql' tab
* Point this at the EDM to extract from

\*\* It is very important to understand that the sql script here is only designed
to work on the EDM as received from GC, in the exact format they produce.\*\*
We did not have time to create a generic EDM exposure extract script.

The values coming out of this script were verified against the Risklink agg tool
and produce within 1% the same TSI.

# Go to the green tabs.

These run a series of slow and convoluted formulas, but they work.
They split out the data by class / FA etc. into pivot tables on the right
hand side of the spreadsheet.
This data should then be formatted into required PRA format.


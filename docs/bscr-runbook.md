\---

title: bscr-runbook
time: 1h - 2h
author: Richard Hampton
required software:
python: uv package manager
output: csv
---

# Summary

This runbook describes step by step how to run the BSCR process for
BSCR Schedule V.

There are 5 BSCR outputs required, one for each entity.

The output of the runbook is a csv file that requires
minimal manipulation in Excel to produce the required limits
and policy counts for Schedule V.

## Requirements

The user requires access to the SQL Server storing the
source EDM. The script relies on the trusted connection
to SQL Server being available.

## Run the process

The preferred method is to open this inside marimo notebooks.
You can execute the script using python directly if you know
what you're doing.



## Architecture

Single python script written in Marimo notebook style.
This can also be run as a standalone python script.



### Step 1: Load Marimo

These commands should load a marimo notebook server.
From there you can load the file in a notebook itnerface and run
each cell one by one if you prefer.

```bash

uv sync
uv run marimo edit

```

\[Marimo Docs]



### Step 2: Edit database and EDM config

Browse to the first python cell approximately line 40:
Edit these variables as needed:

SERVER
DATABASE

Run that cell, the script contains an assertion to check the connection
is successful. If you receive an error it is likely a SQL Connection error.
In this case see the troubleshooting section.

## Step 3:  Run remaining cells

Should you wish to change any of the selection criteria for the BSCR you
can do so in the cell which contains functions like is\_nahu, is\_jp and so on.
This is not recommended.

## Step 4: Copy output csv to BSCR folder and perform diff

Copy the csv into an Excel file in the BSCR workings folder.
Pivot the raw data.
Difference the result from the All World and US Only to produce
the required policy count and limits for All World xUS.

> Note: This is technically incorrect but immaterial for the UKEU
> policies as very few will be cross border policies.



## Troubleshooting

### Symtom: Failure to connect to SQL

Do not waste time trying to get a SQL Server connection
working if it doesn't work out the box. This is a problem
with the way Hiscox is setup in that you need to have the
trusted connection/microsoft login access to the SQL Server
and ODBC Driver.



#### Cause A: ODBC Driver error

However if it is an ODBC driver error you are seeing:

* Type ODBC in search, go to Drivers.
* Note down the ODBC drivers you have installed
* If not ODBC 18 driver then change the script to the
correct driver.

#### Cause B: Cannot debug further

Do not waste more time tryign to debug SQL connections.
Copy the SQL script and manually save it into a csv file.
Point the script at this line:

``` python
    ## NOTE: You can change this line to debug a failed connection and
    ## connect directly to a csv using read\\\_csv instead.
    df = pl.read\\\_database(query, engine)
```


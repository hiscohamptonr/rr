-- Save result as reporting/bscr/reconcile/edm_raw/loc.parquet
-- Run all six queries against the SAME frozen EDM database/snapshot.
-- Preserve native types, SQL NULLs, empty strings and duplicate rows.
-- No FX conversion, aggregation or additional filtering of source data.

SELECT
    locid,
    accgrpid,
    locnum,
    addrmatch,
    state,
    cntrycode,
    country,
    latitude,
    longitude
FROM dbo.loc;

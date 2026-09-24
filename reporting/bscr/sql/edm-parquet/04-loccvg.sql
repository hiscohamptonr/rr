-- Save result as reporting/bscr/reconcile/edm_raw/loccvg.parquet
-- Run all six queries against the SAME frozen EDM database/snapshot.
-- Preserve native types, SQL NULLs, empty strings and duplicate rows.
-- No FX conversion, aggregation or additional filtering of source data.

SELECT
    locid,
    peril,
    deductamt,
    deductcur,
    valueamt,
    valuecur,
    limitamt,
    limitcur
FROM dbo.loccvg
WHERE peril IN (1, 2);

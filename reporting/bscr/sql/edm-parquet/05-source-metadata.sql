-- Save result as reporting/bscr/reconcile/edm_raw/source_metadata.parquet
-- Run all six queries against the SAME frozen EDM database/snapshot.
-- Preserve native types, SQL NULLs, empty strings and duplicate rows.
-- No FX conversion, aggregation or additional filtering of source data.

SELECT
    CONVERT(nvarchar(128), SERVERPROPERTY('ServerName')) AS source_server,
    DB_NAME() AS source_database,
    SYSUTCDATETIME() AS recorded_utc,
    CONVERT(nvarchar(128), DATABASEPROPERTYEX(DB_NAME(), 'Collation'))
        AS database_collation,
    (SELECT COUNT_BIG(*) FROM dbo.accgrp) AS accgrp_rows,
    (SELECT COUNT_BIG(*) FROM dbo.policy
        WHERE policytype IN (1, 2)) AS policy_rows,
    (SELECT COUNT_BIG(*) FROM dbo.loc) AS loc_rows,
    (SELECT COUNT_BIG(*) FROM dbo.loccvg
        WHERE peril IN (1, 2)) AS loccvg_rows;

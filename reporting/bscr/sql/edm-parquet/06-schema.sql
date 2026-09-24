-- Save result as reporting/bscr/reconcile/edm_raw/schema.parquet
-- Run all six queries against the SAME frozen EDM database/snapshot.
-- Preserve native types, SQL NULLs, empty strings and duplicate rows.
-- No FX conversion, aggregation or additional filtering of source data.

SELECT
    t.name AS table_name,
    c.name AS column_name,
    ty.name AS data_type,
    c.max_length,
    c.precision,
    c.scale,
    c.is_nullable,
    c.collation_name
FROM sys.tables AS t
INNER JOIN sys.schemas AS s
    ON s.schema_id = t.schema_id
INNER JOIN sys.columns AS c
    ON c.object_id = t.object_id
INNER JOIN sys.types AS ty
    ON ty.user_type_id = c.user_type_id
WHERE s.name = 'dbo'
  AND t.name IN ('accgrp', 'policy', 'loc', 'loccvg')
ORDER BY t.name, c.column_id;

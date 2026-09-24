-- Save result as reporting/bscr/reconcile/edm_raw/policy.parquet
-- Run all six queries against the SAME frozen EDM database/snapshot.
-- Preserve native types, SQL NULLs, empty strings and duplicate rows.
-- No FX conversion, aggregation or additional filtering of source data.

SELECT
    policyid,
    accgrpid,
    policytype,
    partof,
    blanlimamt,
    undcovamt,
    blandedamt
FROM dbo.policy
WHERE policytype IN (1, 2);

-- Server (original Python default): prod-lmrmsinsurance-db\LMRMSinsurance
-- Database (original Python default): HISCO_UKEU_01JAN26_010126_ROLLUP_ByLOB_GC_v25_EDM
-- Schema: dbo
-- Source tables: dbo.loc, dbo.loccvg, dbo.policy, dbo.accgrp, dbo.portacct, dbo.portinfo
-- Export with headers as: edm-exposures.csv
-- Select the correct current EDM snapshot and confirm peril/portfolio parameters before running.
DECLARE @peril_to_use int = 4;
DECLARE @portnum_filter nvarchar(255) = NULL;

WITH locs AS (
    SELECT
        L.LOCID, L.ACCGRPID, L.LOCNUM, L.LATITUDE, L.LONGITUDE,
        L.CNTRYCODE AS CountryCode, LC.PERIL,
        LC.VALUECUR AS CurrencyCode,
        SUM(LC.VALUEAMT) AS GroundUpTIV
    FROM dbo.loc L
    JOIN dbo.loccvg LC ON LC.LOCID = L.LOCID
    WHERE LC.PERIL = @peril_to_use
    GROUP BY
        L.LOCID, L.ACCGRPID, L.LOCNUM, L.LATITUDE, L.LONGITUDE,
        L.CNTRYCODE, LC.PERIL, LC.VALUECUR
),
policy_terms AS (
    SELECT
        POL.ACCGRPID, POL.POLICYTYPE AS PERIL,
        MAX(
            CASE WHEN POL.BLANLIMAMT = 0 THEN 1 ELSE POL.BLANLIMAMT END
        ) AS POLICY_LINE_FACTOR
    FROM dbo.policy POL
    WHERE POL.POLICYTYPE = @peril_to_use
    GROUP BY POL.ACCGRPID, POL.POLICYTYPE
),
account_portfolio AS (
    SELECT
        A.ACCGRPID, A.CEDANTID, PA.PORTACCTID,
        UPPER(PI.PORTNAME) AS PORTNAME, PI.Portnum AS PORTNUM,
        CASE
            WHEN PI.Portnum LIKE '%_QS' AND PI.Portnum LIKE '%_FA_%' THEN 0.5
            WHEN PI.Portnum LIKE '%_SRP' AND PI.Portnum LIKE '%_FA_%' THEN 0.3333333
            ELSE 1.0
        END AS FA_QS_SRP_FACTOR
    FROM dbo.accgrp A
    JOIN dbo.portacct PA ON PA.ACCGRPID = A.ACCGRPID
    JOIN dbo.portinfo PI ON PI.PORTINFOID = PA.PORTINFOID
    WHERE @portnum_filter IS NULL OR PI.Portnum = @portnum_filter
)
SELECT
    AP.CEDANTID,
    AP.PORTACCTID,
    L.PERIL,
    L.LOCID,
    L.LOCNUM,
    L.LATITUDE,
    L.LONGITUDE,
    L.GroundUpTIV,
    L.GroundUpTIV * COALESCE(PT.POLICY_LINE_FACTOR, 1.0)
        * AP.FA_QS_SRP_FACTOR AS PolicyAdjustedTIV,
    L.CountryCode,
    L.CurrencyCode,
    AP.PORTNAME,
    AP.PORTNUM,
    COALESCE(PT.POLICY_LINE_FACTOR, 1.0) AS POLICY_LINE_FACTOR,
    AP.FA_QS_SRP_FACTOR,
    'ALL' AS Coverage
FROM locs L
JOIN account_portfolio AP ON AP.ACCGRPID = L.ACCGRPID
LEFT JOIN policy_terms PT
    ON PT.ACCGRPID = L.ACCGRPID AND PT.PERIL = L.PERIL;

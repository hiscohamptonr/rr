-- SQL-only BSCR source-level extraction.
-- Export this result as the raw/source CSV before running aggregate outputs.
-- Peril 1 is earthquake; peril 2 is wind. Both are selected in one run.
-- Currency remains the database source currency and source units; no FX or /1m.
-- Headers: pml, accgrpid, uwritrname, state, userid1, cntrycode,
-- is_geocoded, peril_id
DECLARE @policy_type int = 1;

WITH peril_selection AS (
    SELECT peril_id, peril_name
    FROM (VALUES
        (1, 'Earthquake'),
        (2, 'Wind')
    ) AS selected_perils(peril_id, peril_name)
),
loc_tiv AS (
    SELECT
        locid,
        peril,
        deductamt,
        deductcur,
        SUM(valueamt) AS valueamt
    FROM loccvg
    WHERE peril IN (SELECT peril_id FROM peril_selection)
    GROUP BY
        locid,
        peril,
        deductamt,
        deductcur,
        limitamt,
        limitcur
),
gross_loctiv AS (
    SELECT
        CASE
            WHEN valueamt < deductamt THEN 0
            ELSE valueamt
        END AS pml,
        *
    FROM loc_tiv
),
selected_locs AS (
    SELECT
        locid,
        accgrpid,
        locnum,
        CASE WHEN addrmatch = 0 THEN 0 ELSE 1 END AS is_geocoded,
        CASE WHEN cntrycode = 'US' THEN state ELSE '' END AS state,
        cntrycode,
        country
    FROM loc
),
loc_exposure AS (
    SELECT
        SUM(gross_loctiv.pml) AS pml,
        gross_loctiv.peril AS peril_id,
        selected_locs.accgrpid,
        state,
        cntrycode,
        country,
        is_geocoded
    FROM gross_loctiv
    INNER JOIN selected_locs
        ON selected_locs.locid = gross_loctiv.locid
    GROUP BY
        gross_loctiv.peril,
        accgrpid,
        state,
        cntrycode,
        country,
        is_geocoded
),
policies AS (
    SELECT DISTINCT
        policy.accgrpid,
        policyid,
        partof,
        CASE WHEN blanlimamt = 0 THEN 0 ELSE partof END AS policy_limit,
        undcovamt,
        blandedamt,
        accgrp.userid1,
        accgrp.branchname,
        accgrp.UWritrname,
        is_geocoded
    FROM policy
    INNER JOIN accgrp
        ON accgrp.accgrpid = policy.accgrpid
    INNER JOIN loc_exposure
        ON loc_exposure.accgrpid = accgrp.accgrpid
       AND loc_exposure.accgrpid = policy.accgrpid
    WHERE policy.policytype = @policy_type
),
policy_exposure AS (
    SELECT
        CASE
            WHEN SUM(pml) > policy_limit THEN policy_limit
            ELSE SUM(pml)
        END AS pml,
        loc_exposure.peril_id,
        policies.accgrpid,
        state,
        userid1,
        branchname,
        cntrycode,
        uwritrname,
        policies.is_geocoded
    FROM loc_exposure
    INNER JOIN policies
        ON policies.accgrpid = loc_exposure.accgrpid
    GROUP BY
        loc_exposure.peril_id,
        policies.accgrpid,
        state,
        userid1,
        branchname,
        cntrycode,
        uwritrname,
        policies.is_geocoded,
        policy_limit
)
SELECT
    SUM(pml) AS pml,
    accgrpid,
    uwritrname,
    state,
    userid1,
    cntrycode,
    is_geocoded,
    peril_id
FROM policy_exposure
GROUP BY
    peril_id,
    state,
    cntrycode,
    userid1,
    uwritrname,
    is_geocoded,
    accgrpid
ORDER BY
    peril_id,
    SUM(pml) DESC;

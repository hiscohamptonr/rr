-- BSCR source-level extraction: peril 1 and policy type 1 only.
-- Applies the same selection to every country/state; no regional peril routing.
-- Other calculations are unchanged from bscr-extract.sql, including its
-- legacy policy/geocoding joins and cap grouping; this is not a corrected extract.
-- Currency remains the database source currency and source units; no FX or /1m.
-- Headers: pml, accgrpid, uwritrname, state, userid1, cntrycode,
-- is_geocoded, peril_id (always 1)
WITH loc_tiv AS (
    SELECT
        locid,
        peril,
        deductamt,
        deductcur,
        SUM(valueamt) AS valueamt
    FROM loccvg
    WHERE peril = 1
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
    WHERE policy.policytype = 1
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

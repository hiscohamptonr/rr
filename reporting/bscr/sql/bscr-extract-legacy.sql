-- Legacy BSCR aggregate output: historical SQL plus original Python regional rules.
-- Diagnostic historical reproduction, NOT the corrected calculation.
-- Peril = 1 and policytype = 1 for ALL regions, including wind-named regions.
-- Intentionally preserves policy-side geocode duplication and cap grouping
-- without policyid, so the saved historical output can be reproduced.
-- Binary geographic comparisons reproduce Python's case-sensitive matching;
-- e.g. uppercase CALIFORNIA does not match the historical California lookup.
-- Uses the original all-US NA hurricane rule (as in the historical CSV).
-- Default output is full USD (GBP x 1.35), not USD millions.
-- To compare directly to the historical source-currency CSV, set FX to 1.
-- Headers: cntrycode, bscr_entity, region, sum_pml, sum_net,
-- count_policies, is_geocoded, peril_id (always 1).
-- count_policies counts grouped source rows, not distinct policy IDs.
DECLARE @gbp_to_usd decimal(18, 8) = 1.35;
DECLARE @qs_pct_retention decimal(9, 6) = 0.5;
DECLARE @srp_pct_retention decimal(9, 6) = 0.3333;
DECLARE @bscr_entity varchar(20) = NULL;

WITH region_peril_lookup AS (
    SELECT region, peril_id, source_flag
    FROM (VALUES
        ('is_nahu',   1, 'is_nahu'),
        ('is_eu',     1, 'is_eu'),
        ('is_jp',     1, 'is_jp'),
        ('is_na_eq',  1, 'is_na_eq'),
        ('is_us_all', 1, 'is_us_all')
    ) AS mapped_regions(region, peril_id, source_flag)
),
loc_tiv AS (
  SELECT
    locid AS locid,
    peril AS peril,
    deductamt AS deductamt,
    deductcur AS deductcur,
    SUM(valueamt) AS valueamt
  FROM loccvg
  WHERE
    peril = 1
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
    CASE WHEN valueamt < deductamt THEN 0 ELSE valueamt END AS pml,
    *
  FROM loc_tiv
),
selected_locs AS (
  SELECT
    locid AS locid,
    accgrpid AS accgrpid,
    locnum AS locnum,
    CASE WHEN addrmatch = 0 THEN 0 ELSE 1 END AS is_geocoded,
    CASE WHEN cntrycode = 'US' THEN state ELSE '' END AS state,
    cntrycode AS cntrycode,
    country AS country
  FROM loc
),
loc_exposure AS (
  SELECT
    SUM(gross_loctiv.pml) AS pml,
    selected_locs.accgrpid AS accgrpid,
    state AS state,
    cntrycode AS cntrycode,
    country AS country,
    is_geocoded AS is_geocoded
  FROM gross_loctiv
  INNER JOIN selected_locs
    ON selected_locs.locid = gross_loctiv.locid
  GROUP BY
    accgrpid,
    state,
    cntrycode,
    country,
    is_geocoded
),
policies AS (
  SELECT DISTINCT
    policy.accgrpid AS accgrpid,
    policyid AS policyid,
    partof AS partof,
    CASE WHEN blanlimamt = 0 THEN 0 ELSE partof END AS policy_limit,
    undcovamt AS undcovamt,
    blandedamt AS blandedamt,
    accgrp.userid1 AS userid1,
    accgrp.branchname AS branchname,
    accgrp.UWritrname AS UWritrname,
    is_geocoded AS is_geocoded
  FROM policy
  INNER JOIN accgrp
    ON accgrp.accgrpid = policy.accgrpid
  INNER JOIN loc_exposure
    ON loc_exposure.accgrpid = accgrp.accgrpid
    AND loc_exposure.accgrpid = policy.accgrpid
  WHERE
    policy.policytype = 1
),
policy_exposure AS (
  SELECT
    CASE WHEN SUM(pml) > policy_limit THEN policy_limit ELSE SUM(pml) END AS pml,
    policies.accgrpid AS accgrpid,
    uwritrname AS uwritrname,
    state AS state,
    userid1 AS userid1,
    branchname AS branchname,
    cntrycode AS cntrycode,
    policies.is_geocoded AS is_geocoded
  FROM loc_exposure
  INNER JOIN policies
    ON policies.accgrpid = loc_exposure.accgrpid
  GROUP BY
    policies.accgrpid,
    uwritrname,
    state,
    userid1,
    branchname,
    cntrycode,
    policies.is_geocoded,
    policy_limit
),
source_exposure AS (
SELECT
  SUM(pml) AS pml,
  accgrpid,
  state,
  userid1,
  cntrycode,
  uwritrname,
  is_geocoded,
  1 AS peril_id
FROM policy_exposure
GROUP BY
  state,
  cntrycode,
  userid1,
  uwritrname,
  is_geocoded,
  accgrpid
),
nahu_country_lookup AS (
    SELECT countrycode
    FROM (VALUES
        ('US'),
        ('CB'),
        ('TC'),
        ('BH'),
        ('JM'),
        ('VI'),
        ('MX')
    ) AS lookup(countrycode)
),
naeq_country_lookup AS (
    SELECT countrycode
    FROM (VALUES
        ('US'),
        ('CA')
    ) AS lookup(countrycode)
),
naeq_us_state_lookup AS (
    SELECT state
    FROM (VALUES
        ('California'),
        ('Washington'),
        ('Oregon'),
        ('South Carolina'),
        ('Tennessee')
    ) AS lookup(state)
),
classified_exposure AS (
    SELECT
        exposure.pml,
        exposure.peril_id,
        exposure.accgrpid,
        exposure.uwritrname,
        exposure.state,
        exposure.userid1,
        exposure.cntrycode,
        exposure.is_geocoded,
        CASE
            WHEN UPPER(COALESCE(CONVERT(varchar(255), exposure.userid1), '')) LIKE '%HIG%' THEN 'HIG'
            WHEN UPPER(COALESCE(CONVERT(varchar(255), exposure.userid1), '')) LIKE '%HSA%' THEN 'HSA'
            WHEN UPPER(COALESCE(CONVERT(varchar(255), exposure.userid1), '')) LIKE '%33%' THEN '33'
            WHEN UPPER(COALESCE(CONVERT(varchar(255), exposure.userid1), '')) LIKE '%3624%' THEN '3624'
            WHEN UPPER(COALESCE(CONVERT(varchar(255), exposure.userid1), '')) LIKE '%HIC%' THEN 'HIC'
            ELSE NULL
        END AS bscr_entity,
        CASE
            WHEN CHARINDEX('_QS', UPPER(COALESCE(CONVERT(varchar(255), exposure.userid1), ''))) > 0 THEN 1
            ELSE 0
        END AS is_qs,
        CASE
            WHEN CHARINDEX('_SRP', UPPER(COALESCE(CONVERT(varchar(255), exposure.userid1), ''))) > 0 THEN 1
            ELSE 0
        END AS is_srp,
        CASE WHEN nahu.countrycode IS NULL THEN 0 ELSE 1 END AS is_nahu,
        CASE
            WHEN naeq.countrycode IS NULL THEN 0
            WHEN exposure.cntrycode COLLATE Latin1_General_100_BIN2 <> 'US' THEN 1
            WHEN exposure.state IS NULL THEN 1
            WHEN naeq_state.state IS NOT NULL THEN 1
            ELSE 0
        END AS is_na_eq,
        CASE WHEN exposure.cntrycode COLLATE Latin1_General_100_BIN2 = 'JP' THEN 1 ELSE 0 END AS is_jp,
        CASE
            WHEN exposure.cntrycode COLLATE Latin1_General_100_BIN2 IN (
                'GB', 'UK', 'FR', 'DE', 'BE', 'NL', 'LX',
                'AT', 'DK', 'SE', 'PL', 'CZ'
            ) THEN 1
            ELSE 0
        END AS is_eu,
        CASE WHEN exposure.cntrycode COLLATE Latin1_General_100_BIN2 = 'US' THEN 1 ELSE 0 END AS is_us_all
    FROM source_exposure AS exposure
    LEFT JOIN nahu_country_lookup AS nahu
        ON nahu.countrycode = exposure.cntrycode
    LEFT JOIN naeq_country_lookup AS naeq
        ON naeq.countrycode = exposure.cntrycode
    LEFT JOIN naeq_us_state_lookup AS naeq_state
        ON exposure.cntrycode COLLATE Latin1_General_100_BIN2 = 'US'
       AND naeq_state.state COLLATE Latin1_General_100_BIN2 = exposure.state
),
retained_exposure AS (
    SELECT
        *,
        CASE
            WHEN is_qs = 1 THEN pml * @qs_pct_retention
            WHEN is_srp = 1 THEN pml * @srp_pct_retention
            ELSE pml
        END AS net
    FROM classified_exposure
),
regional_wide AS (
    SELECT
        peril_id,
        bscr_entity,
        is_nahu,
        is_na_eq,
        is_jp,
        is_eu,
        is_us_all,
        is_geocoded,
        cntrycode,
        SUM(pml) AS sum_pml,
        SUM(net) AS sum_net,
        COUNT_BIG(*) AS count_policies
    FROM retained_exposure
    GROUP BY
        peril_id,
        bscr_entity,
        is_nahu,
        is_na_eq,
        is_jp,
        is_eu,
        is_us_all,
        is_geocoded,
        cntrycode
),
regional_long AS (
    SELECT
        wide.peril_id,
        wide.bscr_entity,
        mapped.region,
        wide.is_geocoded,
        wide.cntrycode,
        SUM(wide.sum_pml) AS sum_pml,
        SUM(wide.sum_net) AS sum_net,
        SUM(wide.count_policies) AS count_policies
    FROM regional_wide AS wide
    CROSS APPLY (VALUES
        ('is_nahu', wide.is_nahu),
        ('is_na_eq', wide.is_na_eq),
        ('is_jp', wide.is_jp),
        ('is_eu', wide.is_eu),
        ('is_us_all', wide.is_us_all)
    ) AS flags(source_flag, in_region)
    INNER JOIN region_peril_lookup AS mapped
        ON mapped.source_flag = flags.source_flag
       AND mapped.peril_id = wide.peril_id
    WHERE flags.in_region = 1
    GROUP BY
        wide.peril_id,
        wide.bscr_entity,
        mapped.region,
        wide.is_geocoded,
        wide.cntrycode
),
all_exposure AS (
    SELECT
        1 AS peril_id,
        cntrycode,
        bscr_entity,
        'ALL' AS region,
        SUM(pml) AS sum_pml,
        SUM(net) AS sum_net,
        COUNT_BIG(*) AS count_policies,
        is_geocoded
    FROM retained_exposure
    WHERE peril_id = 1
    GROUP BY
        cntrycode,
        bscr_entity,
        is_geocoded
),
final_output AS (
    SELECT
        cntrycode,
        bscr_entity,
        region,
        sum_pml,
        sum_net,
        count_policies,
        is_geocoded,
        peril_id
    FROM regional_long
    UNION ALL
    SELECT
        cntrycode,
        bscr_entity,
        region,
        sum_pml,
        sum_net,
        count_policies,
        is_geocoded,
        peril_id
    FROM all_exposure
)
SELECT
    cntrycode,
    bscr_entity,
    region,
    sum_pml * @gbp_to_usd AS sum_pml,
    sum_net * @gbp_to_usd AS sum_net,
    count_policies,
    is_geocoded,
    peril_id
FROM final_output
WHERE @bscr_entity IS NULL
   OR bscr_entity = @bscr_entity
ORDER BY
    region,
    bscr_entity,
    is_geocoded,
    cntrycode;

-- SQL-only BSCR aggregation.
-- Uses the legacy output schema with corrected policy/peril/geocode joins.
-- The peril header table below selects earthquake (1) and wind (2) together.
-- Region-to-peril routing is explicit in region_peril_lookup.
-- Set @bscr_entity to 33, HIC, HIG, HSA or 3624 for one entity.
-- Currency: pml/net stay in the database source currency and source units.
-- This SQL does not apply FX conversion or divide by 1,000,000.
-- The current workbook assumes GBP -> USD at Settings!B3 = 1.35, then /1m.
-- Retention parameters are fractions: 0.5 = 50%; 0.3333 = 33.33%.
-- Output headers: cntrycode, bscr_entity, region, sum_pml, sum_net,
-- count_policies, is_geocoded. Region names identify the peril routing.
-- Policy types match peril IDs. Limits apply per policy and exposure grouping.
-- The uncorrected bscr-extract.sql can differ from these corrected totals.
DECLARE @qs_pct_retention decimal(9, 6) = 0.5;
DECLARE @srp_pct_retention decimal(9, 6) = 0.3333;
DECLARE @bscr_entity varchar(20) = NULL;

WITH peril_selection AS (
    SELECT peril_id, peril_name
    FROM (VALUES
        (1, 'Earthquake'),
        (2, 'Wind')
    ) AS selected_perils(peril_id, peril_name)
),
region_peril_lookup AS (
    SELECT region, peril_id, source_flag
    FROM (VALUES
        ('is_nahu',    2, 'is_nahu'),
        ('is_eu',      2, 'is_eu'),
        ('is_jp',      2, 'is_jp'),
        ('is_na_eq',   1, 'is_na_eq'),
        ('is_jp_eq',   1, 'is_jp'),
        ('is_us_all',  1, 'is_us_all'),
        ('is_non_us',  1, 'is_non_us')
    ) AS mapped_regions(region, peril_id, source_flag)
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
    SELECT
        policy.accgrpid,
        policyid,
        policy.policytype AS peril_id,
        CASE WHEN blanlimamt = 0 THEN 0 ELSE partof END AS policy_limit,
        accgrp.userid1,
        accgrp.branchname,
        accgrp.UWritrname
    FROM policy
    INNER JOIN accgrp
        ON accgrp.accgrpid = policy.accgrpid
    WHERE policy.policytype IN (SELECT peril_id FROM peril_selection)
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
        loc_exposure.is_geocoded
    FROM loc_exposure
    INNER JOIN policies
        ON policies.accgrpid = loc_exposure.accgrpid
       AND policies.peril_id = loc_exposure.peril_id
    GROUP BY
        loc_exposure.peril_id,
        policies.accgrpid,
        policies.policyid,
        state,
        userid1,
        branchname,
        cntrycode,
        uwritrname,
        loc_exposure.is_geocoded,
        policy_limit
),
source_exposure AS (
    -- Keep the legacy intermediate branchname grouping, then remove it from
    -- the source contract exactly as old-process/BSCR_UKEU.py did.
    SELECT
        SUM(pml) AS pml,
        peril_id,
        accgrpid,
        uwritrname,
        state,
        userid1,
        cntrycode,
        is_geocoded
    FROM policy_exposure
    GROUP BY
        peril_id,
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
            WHEN exposure.cntrycode <> 'US' THEN 1
            WHEN exposure.state IS NULL THEN 1
            WHEN naeq_state.state IS NOT NULL THEN 1
            ELSE 0
        END AS is_na_eq,
        CASE WHEN exposure.cntrycode = 'JP' THEN 1 ELSE 0 END AS is_jp,
        CASE
            WHEN exposure.cntrycode IN (
                'GB', 'UK', 'FR', 'DE', 'BE', 'NL', 'LX',
                'AT', 'DK', 'SE', 'PL', 'CZ'
            ) THEN 1
            ELSE 0
        END AS is_eu,
        CASE WHEN exposure.cntrycode = 'US' THEN 1 ELSE 0 END AS is_us_all,
        CASE WHEN exposure.cntrycode = 'US' THEN 0 ELSE 1 END AS is_non_us
    FROM source_exposure AS exposure
    LEFT JOIN nahu_country_lookup AS nahu
        ON nahu.countrycode = exposure.cntrycode
    LEFT JOIN naeq_country_lookup AS naeq
        ON naeq.countrycode = exposure.cntrycode
    LEFT JOIN naeq_us_state_lookup AS naeq_state
        ON exposure.cntrycode = 'US'
       AND naeq_state.state = exposure.state
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
        is_non_us,
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
        is_non_us,
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
        ('is_us_all', wide.is_us_all),
        ('is_non_us', wide.is_non_us)
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
        is_geocoded
    FROM regional_long
    UNION ALL
    SELECT
        cntrycode,
        bscr_entity,
        region,
        sum_pml,
        sum_net,
        count_policies,
        is_geocoded
    FROM all_exposure
)
SELECT
    cntrycode,
    bscr_entity,
    region,
    sum_pml,
    sum_net,
    count_policies,
    is_geocoded
FROM final_output
WHERE @bscr_entity IS NULL
   OR bscr_entity = @bscr_entity
ORDER BY
    region,
    bscr_entity,
    is_geocoded,
    cntrycode;

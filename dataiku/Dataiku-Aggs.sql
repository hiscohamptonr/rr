/*
Databricks SQL / Dataiku
Multi-level OED aggregates for Core Aggs, PRA, BSCR and Lloyds.

Important:
- Edit physical source tables only in the input CTEs near the top.
- Edit OEDIDs only in selected_oedids.
- Source currency is LocCurrency.
- Rate_to_GBP is assumed to mean GBP for one unit of source currency.
- This version calculates gross TIV and GBP-converted gross TIV.
- Deductibles, limits, percentage share and Fine Art QS are not yet applied.
- PRA_REGION is configured but inactive until the mapping CSV is loaded.
- CRESTA is configured but inactive because the supplied OED columns do not
  contain a confirmed CRESTA field or CRESTA-zone mapping.
*/

WITH

/* -------------------------------------------------------------------------
   OEDIDS TO RUN
   ------------------------------------------------------------------------- */
selected_oedids AS (
    SELECT
        CAST(v.OEDID AS BIGINT) AS OEDID,
        CAST(v.DatasetLabel AS STRING) AS DatasetLabel
    FROM VALUES
        (42, 'UK'),
        (44, 'EU')
    AS v(OEDID, DatasetLabel)
),

/* -------------------------------------------------------------------------
   AGGREGATION LEVELS
   Duplicate levels across use cases are intentional.
   ------------------------------------------------------------------------- */
aggregation_levels AS (
    SELECT
        CAST(v.UseCase AS STRING) AS UseCase,
        CAST(v.AggregationLevel AS STRING) AS AggregationLevel,
        CAST(v.SortOrder AS INT) AS SortOrder,
        CAST(v.IsActive AS BOOLEAN) AS IsActive
    FROM VALUES
        ('Aggs',    'ACCOUNT',       10, TRUE),
        ('Aggs',    'COUNTRY',       20, TRUE),
        ('Aggs',    'STATE',         30, TRUE),
        ('Aggs',    'POSTCODE',      40, TRUE),
        ('Aggs',    'CRESTA',        50, FALSE),

        ('PRA',     'COUNTRY',       10, TRUE),
        ('PRA',     'STATE',         20, TRUE),
        ('PRA',     'PRA_REGION',    30, FALSE),

        ('BSCR',    'COUNTRY',       10, TRUE),
        ('BSCR',    'STATE',         20, TRUE),
        ('BSCR',    'NAHU',          30, TRUE),
        ('BSCR',    'NA_EQ',         40, TRUE),
        ('BSCR',    'JP',            50, TRUE),
        ('BSCR',    'EU',            60, TRUE),
        ('BSCR',    'US_ALL',        70, TRUE),
        ('BSCR',    'ALL_XUS',       80, TRUE),
        ('BSCR',    'ALL',           90, TRUE),

        ('Lloyds',  'COUNTRY',       10, TRUE),
        ('Lloyds',  'STATE',         20, TRUE),
        ('Lloyds',  'POSTCODE',      30, TRUE),
        ('Lloyds',  'CRESTA',        40, FALSE)
    AS v(UseCase, AggregationLevel, SortOrder, IsActive)
),

/* -------------------------------------------------------------------------
   INPUT TABLE 1: OED
   ------------------------------------------------------------------------- */
input_oed AS (
    SELECT
        ids.DatasetLabel,
        oed.OEDID,
        oed.OEDName,
        oed.OEDSource,
        oed.LocNumber,
        oed.AccNumber,
        oed.BranchName,
        oed.AccUserDef1,
        oed.AccUserDef2,
        oed.AccUserDef3,
        oed.AccUserDef4,
        oed.AccUserDef5,
        oed.PolUserDef5,
        oed.Country,
        oed.CountryCode,
        oed.County,
        oed.AreaCode,
        oed.PostalCode,
        oed.AddressMatch,
        oed.BuildingTIV,
        oed.ContentsTIV,
        oed.BITIV,
        oed.OtherTIV,
        oed.LocCurrency,
        oed.LocUserDef1,
        oed.LocParticipation
    FROM `prod_group_kairos_sandbox`.`dataiku`.`ukeu_validator_oed` AS oed
    INNER JOIN selected_oedids AS ids
        ON oed.OEDID = ids.OEDID
),

/* -------------------------------------------------------------------------
   INPUT TABLE 2: GC LOB MAPPING
   ------------------------------------------------------------------------- */
input_lob_mapping AS (
    SELECT DISTINCT
        mapping.AccUserDef2,
        mapping.AccUserDef3,
        mapping.AccUserDef4,
        mapping.AccUserDef5,
        mapping.BranchName,
        mapping.LocUserDef1,
        mapping.modelled_lob
    FROM `prod_group_kairos_sandbox`.`dataiku_temp`.`RETAILROLLUPDATA_map_lob_mapping_gc` AS mapping
),

/* -------------------------------------------------------------------------
   INPUT TABLE 3: FX RATES
   ------------------------------------------------------------------------- */
input_fx_rates AS (
    SELECT
        UPPER(TRIM(fx.CurrencyCode)) AS CurrencyCode,
        TRY_CAST(fx.Rate_to_GBP AS DECIMAL(24, 12)) AS RateToGBP
    FROM `prod_group_kairos_sandbox`.`dataiku_temp`.`RETAILROLLUPDATA_map_fx_rates` AS fx
),

/* PRA region mapping is not yet available as a Databricks table. */

fx_rates AS (
    SELECT
        CurrencyCode,
        MAX(RateToGBP) AS RateToGBP,
        COUNT(1) AS RateRecordCount
    FROM input_fx_rates
    WHERE CurrencyCode IS NOT NULL
    GROUP BY CurrencyCode
),

enriched_oed AS (
    SELECT
        oed.DatasetLabel,
        oed.OEDID,
        oed.OEDName,
        oed.OEDSource,
        oed.LocNumber,
        oed.AccNumber,
        oed.BranchName,
        oed.AccUserDef1 AS AccountReference,
        oed.AccUserDef2,
        oed.AccUserDef3,
        oed.AccUserDef4,
        oed.AccUserDef5,
        oed.PolUserDef5,
        oed.Country,
        UPPER(TRIM(oed.CountryCode)) AS CountryCode,
        oed.County,
        oed.AreaCode,
        oed.PostalCode,
        oed.AddressMatch,
        oed.BuildingTIV,
        oed.ContentsTIV,
        oed.BITIV,
        oed.OtherTIV,
        oed.LocCurrency,
        oed.LocUserDef1,
        oed.LocParticipation,
        lob.modelled_lob AS ModelledLOB,
        UPPER(TRIM(oed.LocCurrency)) AS SourceCurrency,
        fx.RateToGBP AS SourceCurrencyRateToGBP,
        fx.RateRecordCount,
        CASE
            WHEN fx.CurrencyCode IS NULL THEN TRUE
            WHEN fx.RateToGBP IS NULL THEN TRUE
            WHEN fx.RateToGBP = 0 THEN TRUE
            ELSE FALSE
        END AS MissingOrInvalidFXRate
    FROM input_oed AS oed
    LEFT JOIN input_lob_mapping AS lob
        ON COALESCE(TRIM(oed.AccUserDef2), '__NULL__')
         = COALESCE(TRIM(lob.AccUserDef2), '__NULL__')
        AND COALESCE(TRIM(oed.AccUserDef3), '__NULL__')
         = COALESCE(TRIM(lob.AccUserDef3), '__NULL__')
        AND COALESCE(TRIM(oed.AccUserDef4), '__NULL__')
         = COALESCE(TRIM(lob.AccUserDef4), '__NULL__')
        AND COALESCE(TRIM(oed.AccUserDef5), '__NULL__')
         = COALESCE(TRIM(lob.AccUserDef5), '__NULL__')
        AND COALESCE(TRIM(oed.BranchName), '__NULL__')
         = COALESCE(TRIM(lob.BranchName), '__NULL__')
        AND COALESCE(TRIM(oed.LocUserDef1), '__NULL__')
         = COALESCE(TRIM(lob.LocUserDef1), '__NULL__')
    LEFT JOIN fx_rates AS fx
        ON UPPER(TRIM(oed.LocCurrency)) = fx.CurrencyCode
),

normalised_rows AS (
    SELECT
        DatasetLabel,
        OEDID,
        OEDName,
        OEDSource,
        LocNumber,
        AccNumber,
        AccountReference,
        BranchName,
        AccUserDef2,
        AccUserDef3,
        AccUserDef4,
        AccUserDef5,
        PolUserDef5,
        ModelledLOB,
        CountryCode,
        COALESCE(NULLIF(TRIM(Country), ''), CountryCode, 'UNKNOWN') AS CountryValue,
        CASE
            WHEN CountryCode = 'US' THEN
                COALESCE(NULLIF(TRIM(County), ''), NULLIF(TRIM(AreaCode), ''), 'UNKNOWN')
            ELSE 'NOT_APPLICABLE'
        END AS StateValue,
        COALESCE(NULLIF(TRIM(PostalCode), ''), 'UNKNOWN') AS PostcodeValue,
        CAST(NULL AS STRING) AS CrestaValue,
        CASE
            WHEN CountryCode = 'US' THEN
                UPPER(COALESCE(NULLIF(TRIM(County), ''), NULLIF(TRIM(AreaCode), ''), 'UNKNOWN'))
            ELSE UPPER(COALESCE(NULLIF(TRIM(Country), ''), CountryCode, 'UNKNOWN'))
        END AS PRARegionLookupKey,
        CASE
            WHEN AddressMatch IS NULL THEN FALSE
            WHEN TRIM(CAST(AddressMatch AS STRING)) = '' THEN FALSE
            WHEN TRIM(CAST(AddressMatch AS STRING)) = '0' THEN FALSE
            ELSE TRUE
        END AS IsGeocoded,
        SourceCurrency,
        SourceCurrencyRateToGBP,
        RateRecordCount,
        MissingOrInvalidFXRate,
        COALESCE(TRY_CAST(BuildingTIV AS DECIMAL(38, 6)), CAST(0 AS DECIMAL(38, 6)))
            AS BuildingTIVSource,
        COALESCE(TRY_CAST(ContentsTIV AS DECIMAL(38, 6)), CAST(0 AS DECIMAL(38, 6)))
            AS ContentsTIVSource,
        COALESCE(TRY_CAST(BITIV AS DECIMAL(38, 6)), CAST(0 AS DECIMAL(38, 6)))
            AS BITIVSource,
        COALESCE(TRY_CAST(OtherTIV AS DECIMAL(38, 6)), CAST(0 AS DECIMAL(38, 6)))
            AS OtherTIVSource
    FROM enriched_oed
),

calculated_rows AS (
    SELECT
        n.DatasetLabel,
        n.OEDID,
        n.OEDName,
        n.OEDSource,
        n.LocNumber,
        n.AccNumber,
        n.AccountReference,
        n.BranchName,
        n.AccUserDef2,
        n.AccUserDef3,
        n.AccUserDef4,
        n.AccUserDef5,
        n.PolUserDef5,
        n.ModelledLOB,
        n.CountryCode,
        n.CountryValue,
        n.StateValue,
        n.PostcodeValue,
        n.CrestaValue,
        CAST('UNAVAILABLE_REGION_MAPPING' AS STRING) AS PRARegion,
        CAST('UNAVAILABLE_REGION_MAPPING' AS STRING) AS StandardFormulaRegion,
        n.IsGeocoded,
        n.SourceCurrency,
        n.SourceCurrencyRateToGBP,
        n.RateRecordCount,
        n.MissingOrInvalidFXRate,
        n.BuildingTIVSource,
        n.ContentsTIVSource,
        n.BITIVSource,
        n.OtherTIVSource,
        n.BuildingTIVSource
        + n.ContentsTIVSource
        + n.BITIVSource
        + n.OtherTIVSource AS GrossTIVSource,
        CASE
            WHEN UPPER(COALESCE(n.ModelledLOB, '')) LIKE '%HIG%' THEN 'HIG'
            WHEN UPPER(COALESCE(n.ModelledLOB, '')) LIKE '%HSA%' THEN 'HSA'
            WHEN UPPER(COALESCE(n.ModelledLOB, '')) LIKE '%3624%' THEN '3624'
            WHEN UPPER(COALESCE(n.ModelledLOB, '')) LIKE '%S33%' THEN '33'
            WHEN UPPER(COALESCE(n.ModelledLOB, '')) LIKE '%HIC%' THEN 'HIC'
            ELSE 'UNMAPPED'
        END AS BSCREntity
    FROM normalised_rows AS n
),

level_rows AS (
    SELECT
        'Aggs' AS UseCase,
        'ACCOUNT' AS AggregationLevel,
        CAST(AccNumber AS STRING) AS AggregationValue,
        c.*
    FROM calculated_rows AS c

    UNION ALL

    SELECT
        'Aggs' AS UseCase,
        'COUNTRY' AS AggregationLevel,
        CountryValue AS AggregationValue,
        c.*
    FROM calculated_rows AS c

    UNION ALL

    SELECT
        'Aggs' AS UseCase,
        'STATE' AS AggregationLevel,
        StateValue AS AggregationValue,
        c.*
    FROM calculated_rows AS c

    UNION ALL

    SELECT
        'Aggs' AS UseCase,
        'POSTCODE' AS AggregationLevel,
        PostcodeValue AS AggregationValue,
        c.*
    FROM calculated_rows AS c

    UNION ALL

    SELECT
        'PRA' AS UseCase,
        'COUNTRY' AS AggregationLevel,
        CountryValue AS AggregationValue,
        c.*
    FROM calculated_rows AS c

    UNION ALL

    SELECT
        'PRA' AS UseCase,
        'STATE' AS AggregationLevel,
        StateValue AS AggregationValue,
        c.*
    FROM calculated_rows AS c

    UNION ALL

    SELECT
        'PRA' AS UseCase,
        'PRA_REGION' AS AggregationLevel,
        PRARegion AS AggregationValue,
        c.*
    FROM calculated_rows AS c

    UNION ALL

    SELECT
        'BSCR' AS UseCase,
        'COUNTRY' AS AggregationLevel,
        CountryValue AS AggregationValue,
        c.*
    FROM calculated_rows AS c

    UNION ALL

    SELECT
        'BSCR' AS UseCase,
        'STATE' AS AggregationLevel,
        StateValue AS AggregationValue,
        c.*
    FROM calculated_rows AS c

    UNION ALL

    SELECT
        'BSCR' AS UseCase,
        'NAHU' AS AggregationLevel,
        'NAHU' AS AggregationValue,
        c.*
    FROM calculated_rows AS c
    WHERE CountryCode IN ('US', 'CB', 'TC', 'BH', 'JM', 'VI', 'MX')

    UNION ALL

    SELECT
        'BSCR' AS UseCase,
        'NA_EQ' AS AggregationLevel,
        'NA_EQ' AS AggregationValue,
        c.*
    FROM calculated_rows AS c
    WHERE CountryCode IN ('US', 'CA')

    UNION ALL

    SELECT
        'BSCR' AS UseCase,
        'JP' AS AggregationLevel,
        'JP' AS AggregationValue,
        c.*
    FROM calculated_rows AS c
    WHERE CountryCode = 'JP'

    UNION ALL

    SELECT
        'BSCR' AS UseCase,
        'EU' AS AggregationLevel,
        'EU' AS AggregationValue,
        c.*
    FROM calculated_rows AS c
    WHERE CountryCode IN ('GB', 'UK', 'FR', 'DE', 'BE', 'NL', 'LX', 'AT', 'DK', 'SE', 'PL', 'CZ')

    UNION ALL

    SELECT
        'BSCR' AS UseCase,
        'US_ALL' AS AggregationLevel,
        'US_ALL' AS AggregationValue,
        c.*
    FROM calculated_rows AS c
    WHERE CountryCode = 'US'

    UNION ALL

    SELECT
        'BSCR' AS UseCase,
        'ALL_XUS' AS AggregationLevel,
        'ALL_XUS' AS AggregationValue,
        c.*
    FROM calculated_rows AS c
    WHERE COALESCE(CountryCode, 'UNKNOWN') NOT IN ('US')

    UNION ALL

    SELECT
        'BSCR' AS UseCase,
        'ALL' AS AggregationLevel,
        'ALL' AS AggregationValue,
        c.*
    FROM calculated_rows AS c

    UNION ALL

    SELECT
        'Lloyds' AS UseCase,
        'COUNTRY' AS AggregationLevel,
        CountryValue AS AggregationValue,
        c.*
    FROM calculated_rows AS c

    UNION ALL

    SELECT
        'Lloyds' AS UseCase,
        'STATE' AS AggregationLevel,
        StateValue AS AggregationValue,
        c.*
    FROM calculated_rows AS c

    UNION ALL

    SELECT
        'Lloyds' AS UseCase,
        'POSTCODE' AS AggregationLevel,
        PostcodeValue AS AggregationValue,
        c.*
    FROM calculated_rows AS c
),

active_level_rows AS (
    SELECT
        rows.UseCase,
        rows.AggregationLevel,
        levels.SortOrder,
        rows.AggregationValue,
        rows.DatasetLabel,
        rows.OEDID,
        rows.LocNumber,
        rows.AccNumber,
        rows.BranchName,
        rows.ModelledLOB,
        rows.BSCREntity,
        rows.CountryCode,
        rows.IsGeocoded,
        rows.SourceCurrency,
        rows.SourceCurrencyRateToGBP,
        rows.RateRecordCount,
        rows.MissingOrInvalidFXRate,
        rows.GrossTIVSource
    FROM level_rows AS rows
    INNER JOIN aggregation_levels AS levels
        ON rows.UseCase = levels.UseCase
        AND rows.AggregationLevel = levels.AggregationLevel
        AND levels.IsActive = TRUE
)

SELECT
    OEDID,
    DatasetLabel,
    UseCase,
    AggregationLevel,
    AggregationValue,
    SortOrder AS AggregationSortOrder,
    BranchName,
    ModelledLOB,
    BSCREntity,
    CountryCode,
    IsGeocoded,
    SourceCurrency,
    SourceCurrencyRateToGBP,
    RateRecordCount,
    COUNT(1) AS SourceRowCount,
    COUNT(DISTINCT AccNumber) AS DistinctAccountCount,
    COUNT(DISTINCT LocNumber) AS DistinctLocationCount,
    SUM(GrossTIVSource) AS GrossTIVSourceCurrency,
    SUM(GrossTIVSource * SourceCurrencyRateToGBP) AS GrossTIVGBP,
    SUM(
        CASE
            WHEN ModelledLOB IS NULL THEN 1
            ELSE 0
        END
    ) AS UnmappedLOBRowCount,
    SUM(
        CASE
            WHEN MissingOrInvalidFXRate THEN 1
            ELSE 0
        END
    ) AS MissingOrInvalidFXRowCount
FROM active_level_rows
GROUP BY
    OEDID,
    DatasetLabel,
    UseCase,
    AggregationLevel,
    AggregationValue,
    SortOrder,
    BranchName,
    ModelledLOB,
    BSCREntity,
    CountryCode,
    IsGeocoded,
    SourceCurrency,
    SourceCurrencyRateToGBP,
    RateRecordCount
ORDER BY
    OEDID,
    UseCase,
    AggregationSortOrder,
    AggregationValue,
    BranchName,
    ModelledLOB,
    SourceCurrency;


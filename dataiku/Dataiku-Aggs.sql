/*
Dataiku / Databricks SQL
OED aggregates with policy terms, participation and Fine Art QS.

Measures:
    TIV   = BuildingTIV + ContentsTIV + BITIV + OtherTIV
    GROSS = TIV after applicable deductible and peril limit
    NET   = GROSS after LocParticipation and Fine Art QS cession

Policy-term precedence used here:
    1. A populated peril deductible overrides the blanket deductible.
    2. Otherwise a populated blanket deductible overrides coverage deductibles.
    3. Otherwise coverage deductibles are applied to Building, Contents and BI.
    4. A populated peril limit caps the post-deductible amount.

The output is split by PerilCode. Do not sum different PerilCode values.
Every output is also split by IsFloodRe so Flood Re rows can be retained,
excluded or set to zero by the user. This query does not zero them.
PRA_REGION and CRESTA remain inactive until controlled mappings exist.
*/

WITH

selected_oedids AS (
    SELECT
        CAST(v.OEDID AS BIGINT) AS OEDID,
        CAST(v.DatasetLabel AS STRING) AS DatasetLabel,
        CAST(v.ParticipationScale AS DECIMAL(20, 8)) AS ParticipationScale
    FROM VALUES
        (42, 'UK', 100.0),
        (44, 'EU',   1.0)
    AS v(OEDID, DatasetLabel, ParticipationScale)
),

run_parameters AS (
    SELECT
        CAST(0.0 AS DECIMAL(20, 8)) AS MissingFineArtCessionDefault,
        CAST('CURRENT_OED_COUNTRY_AREA_APPROXIMATION' AS STRING) AS GeographyMappingBasis
),

aggregation_levels AS (
    SELECT
        CAST(v.UseCase AS STRING) AS UseCase,
        CAST(v.AggregationLevel AS STRING) AS AggregationLevel,
        CAST(v.SortOrder AS INT) AS SortOrder,
        CAST(v.IsActive AS BOOLEAN) AS IsActive
    FROM VALUES
        ('Aggs',   'COUNTRY',       20, TRUE),
        ('Aggs',   'STATE',         30, TRUE),
        ('Aggs',   'POSTCODE',      40, TRUE),
        ('Aggs',   'CRESTA',        50, FALSE),
        ('PRA',    'COUNTRY',       10, TRUE),
        ('PRA',    'STATE',         20, TRUE),
        ('PRA',    'PRA_REGION',    30, FALSE),
        ('BSCR',   'COUNTRY',       10, TRUE),
        ('BSCR',   'STATE',         20, TRUE),
        ('BSCR',   'NA_HU',         30, TRUE),
        ('BSCR',   'NA_EQ',         40, TRUE),
        ('BSCR',   'JP',            50, TRUE),
        ('BSCR',   'EU',            60, TRUE),
        ('BSCR',   'US_ALL',        70, TRUE),
        ('BSCR',   'ALL_EX_US',     80, TRUE),
        ('BSCR',   'ALL',           90, TRUE),
        ('Lloyds', 'COUNTRY',       10, TRUE),
        ('Lloyds', 'STATE',         20, TRUE),
        ('Lloyds', 'POSTCODE',      30, TRUE),
        ('Lloyds', 'CRESTA',        40, FALSE)
    AS v(UseCase, AggregationLevel, SortOrder, IsActive)
),

country_reference AS (
    SELECT
        CAST(v.CountryCode AS STRING) AS CountryCode,
        CAST(v.CountryName AS STRING) AS CountryName
    FROM VALUES
        ('AT', 'Austria'), ('BA', 'Bosnia and Herzegovina'),
        ('BE', 'Belgium'), ('BG', 'Bulgaria'), ('BR', 'Brazil'),
        ('CA', 'Canada'), ('CH', 'Switzerland'),
        ('CZ', 'Czech Republic'), ('DE', 'Germany'),
        ('DK', 'Denmark'), ('EE', 'Estonia'), ('ES', 'Spain'),
        ('FI', 'Finland'), ('FR', 'France'),
        ('GB', 'United Kingdom'), ('GR', 'Greece'),
        ('HR', 'Croatia'), ('HU', 'Hungary'), ('IE', 'Ireland'),
        ('IT', 'Italy'), ('JP', 'Japan'), ('LU', 'Luxembourg'),
        ('NL', 'Netherlands'), ('NO', 'Norway'), ('PL', 'Poland'),
        ('PT', 'Portugal'), ('RO', 'Romania'), ('SE', 'Sweden'),
        ('SI', 'Slovenia'), ('SK', 'Slovakia'), ('US', 'United States')
    AS v(CountryCode, CountryName)
),

/* Physical inputs. Change source tables only here. */
input_oed AS (
    SELECT
        ids.DatasetLabel,
        ids.ParticipationScale,
        oed.OEDID,
        oed.LocNumber,
        oed.AccNumber,
        oed.BranchName,
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
        oed.LocDed6All,
        oed.LocDed1Building,
        oed.LocDed3Contents,
        oed.LocDed4BI,
        oed.LocCurrency,
        oed.EQ_Flag,
        oed.FL_Flag,
        oed.WS_Flag,
        oed.FR_Flag,
        oed.EQ_Deductible,
        oed.FL_Deductible,
        oed.WS_Deductible,
        oed.FR_Deductible,
        oed.EQ_Limit,
        oed.FL_Limit,
        oed.WS_Limit,
        oed.FR_Limit,
        oed.LocUserDef1,
        oed.LocUserDef2,
        oed.LocUserDef3,
        oed.LocParticipation
    FROM `prod_group_kairos_sandbox`.`dataiku`.`ukeu_validator_oed` AS oed
    INNER JOIN selected_oedids AS ids
        ON oed.OEDID = ids.OEDID
),

input_lob_mapping AS (
    SELECT
        mapping.AccUserDef2,
        mapping.AccUserDef3,
        mapping.AccUserDef4,
        mapping.AccUserDef5,
        mapping.BranchName,
        mapping.LocUserDef1,
        mapping.modelled_lob
    FROM `prod_group_kairos_sandbox`.`dataiku_temp`.`RETAILROLLUPDATA_map_lob_mapping_gc` AS mapping
),

input_fx_rates AS (
    SELECT
        UPPER(TRIM(fx.CurrencyCode)) AS CurrencyCode,
        TRY_CAST(fx.Rate_to_GBP AS DECIMAL(24, 12)) AS RateToGBP
    FROM `prod_group_kairos_sandbox`.`dataiku_temp`.`RETAILROLLUPDATA_map_fx_rates` AS fx
),

normalised_lob_mapping AS (
    SELECT DISTINCT
        UPPER(TRIM(COALESCE(AccUserDef2, '__NULL__'))) AS Key2,
        UPPER(TRIM(COALESCE(AccUserDef3, '__NULL__'))) AS Key3,
        UPPER(TRIM(COALESCE(AccUserDef4, '__NULL__'))) AS Key4,
        UPPER(TRIM(COALESCE(AccUserDef5, '__NULL__'))) AS Key5,
        UPPER(TRIM(COALESCE(BranchName, '__NULL__'))) AS KeyBranch,
        UPPER(TRIM(COALESCE(LocUserDef1, '__NULL__'))) AS KeyLoc1,
        TRIM(modelled_lob) AS ModelledLOB
    FROM input_lob_mapping
    WHERE modelled_lob IS NOT NULL
),

lob_cardinality AS (
    SELECT
        Key2, Key3, Key4, Key5, KeyBranch, KeyLoc1,
        COUNT(DISTINCT ModelledLOB) AS ModelledLOBCount
    FROM normalised_lob_mapping
    GROUP BY Key2, Key3, Key4, Key5, KeyBranch, KeyLoc1
),

valid_lob_mapping AS (
    SELECT
        mapping.Key2, mapping.Key3, mapping.Key4, mapping.Key5,
        mapping.KeyBranch, mapping.KeyLoc1,
        MAX(mapping.ModelledLOB) AS ModelledLOB
    FROM normalised_lob_mapping AS mapping
    INNER JOIN lob_cardinality AS control
        ON mapping.Key2 = control.Key2
        AND mapping.Key3 = control.Key3
        AND mapping.Key4 = control.Key4
        AND mapping.Key5 = control.Key5
        AND mapping.KeyBranch = control.KeyBranch
        AND mapping.KeyLoc1 = control.KeyLoc1
    WHERE control.ModelledLOBCount = 1
    GROUP BY
        mapping.Key2, mapping.Key3, mapping.Key4, mapping.Key5,
        mapping.KeyBranch, mapping.KeyLoc1
),

fx_controls AS (
    SELECT
        CurrencyCode,
        COUNT(1) AS FXRecordCount,
        COUNT(DISTINCT RateToGBP) AS FXDistinctRateCount,
        CASE
            WHEN COUNT(DISTINCT RateToGBP) = 1
             AND MAX(RateToGBP) BETWEEN CAST(0.000000000001 AS DECIMAL(24, 12))
                                    AND CAST(999999999999.0 AS DECIMAL(24, 12))
                THEN MAX(RateToGBP)
            ELSE CAST(NULL AS DECIMAL(24, 12))
        END AS RateToGBP,
        CASE
            WHEN COUNT(DISTINCT RateToGBP) = 0 THEN 'INVALID'
            WHEN COUNT(DISTINCT RateToGBP) != 1 THEN 'CONFLICTING'
            WHEN COUNT(1) != 1 THEN 'DUPLICATE_CONSISTENT'
            ELSE 'VALID'
        END AS FXRateStatus
    FROM input_fx_rates
    WHERE CurrencyCode IS NOT NULL
    GROUP BY CurrencyCode
),

source_enriched AS (
    SELECT
        oed.DatasetLabel,
        oed.ParticipationScale,
        oed.OEDID,
        oed.LocNumber,
        oed.AccNumber,
        oed.BranchName,
        oed.AccUserDef2,
        oed.AccUserDef3,
        oed.AccUserDef4,
        oed.AccUserDef5,
        oed.PolUserDef5,
        COALESCE(country.CountryName, NULLIF(TRIM(oed.Country), ''),
                 UPPER(TRIM(oed.CountryCode)), 'UNKNOWN') AS CountryName,
        UPPER(TRIM(oed.CountryCode)) AS CountryCode,
        oed.County,
        oed.AreaCode,
        oed.PostalCode,
        oed.AddressMatch,
        oed.BuildingTIV,
        oed.ContentsTIV,
        oed.BITIV,
        oed.OtherTIV,
        oed.LocDed6All,
        oed.LocDed1Building,
        oed.LocDed3Contents,
        oed.LocDed4BI,
        oed.EQ_Flag,
        oed.FL_Flag,
        oed.WS_Flag,
        oed.FR_Flag,
        oed.EQ_Deductible,
        oed.FL_Deductible,
        oed.WS_Deductible,
        oed.FR_Deductible,
        oed.EQ_Limit,
        oed.FL_Limit,
        oed.WS_Limit,
        oed.FR_Limit,
        oed.LocUserDef2,
        oed.LocUserDef3,
        oed.LocParticipation,
        mapping.ModelledLOB,
        CASE
            WHEN cardinality.ModelledLOBCount IS NULL THEN 'UNMAPPED'
            WHEN cardinality.ModelledLOBCount = 1 THEN 'MAPPED'
            ELSE 'AMBIGUOUS'
        END AS LOBMappingStatus,
        UPPER(TRIM(oed.LocCurrency)) AS SourceCurrency,
        fx.RateToGBP,
        COALESCE(fx.FXRecordCount, 0) AS FXRecordCount,
        COALESCE(fx.FXDistinctRateCount, 0) AS FXDistinctRateCount,
        COALESCE(fx.FXRateStatus, 'MISSING') AS FXRateStatus
    FROM input_oed AS oed
    LEFT JOIN country_reference AS country
        ON UPPER(TRIM(oed.CountryCode)) = country.CountryCode
    LEFT JOIN lob_cardinality AS cardinality
        ON UPPER(TRIM(COALESCE(oed.AccUserDef2, '__NULL__'))) = cardinality.Key2
        AND UPPER(TRIM(COALESCE(oed.AccUserDef3, '__NULL__'))) = cardinality.Key3
        AND UPPER(TRIM(COALESCE(oed.AccUserDef4, '__NULL__'))) = cardinality.Key4
        AND UPPER(TRIM(COALESCE(oed.AccUserDef5, '__NULL__'))) = cardinality.Key5
        AND UPPER(TRIM(COALESCE(oed.BranchName, '__NULL__'))) = cardinality.KeyBranch
        AND UPPER(TRIM(COALESCE(oed.LocUserDef1, '__NULL__'))) = cardinality.KeyLoc1
    LEFT JOIN valid_lob_mapping AS mapping
        ON UPPER(TRIM(COALESCE(oed.AccUserDef2, '__NULL__'))) = mapping.Key2
        AND UPPER(TRIM(COALESCE(oed.AccUserDef3, '__NULL__'))) = mapping.Key3
        AND UPPER(TRIM(COALESCE(oed.AccUserDef4, '__NULL__'))) = mapping.Key4
        AND UPPER(TRIM(COALESCE(oed.AccUserDef5, '__NULL__'))) = mapping.Key5
        AND UPPER(TRIM(COALESCE(oed.BranchName, '__NULL__'))) = mapping.KeyBranch
        AND UPPER(TRIM(COALESCE(oed.LocUserDef1, '__NULL__'))) = mapping.KeyLoc1
    LEFT JOIN fx_controls AS fx
        ON UPPER(TRIM(oed.LocCurrency)) = fx.CurrencyCode
),

numeric_rows AS (
    SELECT
        source.DatasetLabel,
        source.ParticipationScale,
        source.OEDID,
        source.LocNumber,
        source.AccNumber,
        source.BranchName,
        source.AccUserDef4,
        source.AccUserDef5,
        source.PolUserDef5,
        source.CountryName,
        source.CountryCode,
        source.County,
        source.AreaCode,
        source.PostalCode,
        source.AddressMatch,
        source.LocUserDef2,
        source.LocUserDef3,
        source.ModelledLOB,
        source.LOBMappingStatus,
        source.SourceCurrency,
        source.RateToGBP,
        source.FXRecordCount,
        source.FXDistinctRateCount,
        source.FXRateStatus,
        TRY_CAST(source.BuildingTIV AS DECIMAL(38, 6)) AS BuildingTIV,
        TRY_CAST(source.ContentsTIV AS DECIMAL(38, 6)) AS ContentsTIV,
        TRY_CAST(source.BITIV AS DECIMAL(38, 6)) AS BITIV,
        TRY_CAST(source.OtherTIV AS DECIMAL(38, 6)) AS OtherTIV,
        TRY_CAST(source.LocDed6All AS DECIMAL(38, 6)) AS BlanketDeductible,
        TRY_CAST(source.LocDed1Building AS DECIMAL(38, 6)) AS BuildingDeductible,
        TRY_CAST(source.LocDed3Contents AS DECIMAL(38, 6)) AS ContentsDeductible,
        TRY_CAST(source.LocDed4BI AS DECIMAL(38, 6)) AS BIDeductible,
        TRY_CAST(source.LocParticipation AS DECIMAL(20, 8)) AS RawParticipation,
        TRY_CAST(source.PolUserDef5 AS DECIMAL(20, 8)) AS RawQSCession,
        source.EQ_Flag, source.FL_Flag, source.WS_Flag, source.FR_Flag,
        TRY_CAST(source.EQ_Deductible AS DECIMAL(38, 6)) AS EQ_Deductible,
        TRY_CAST(source.FL_Deductible AS DECIMAL(38, 6)) AS FL_Deductible,
        TRY_CAST(source.WS_Deductible AS DECIMAL(38, 6)) AS WS_Deductible,
        TRY_CAST(source.FR_Deductible AS DECIMAL(38, 6)) AS FR_Deductible,
        TRY_CAST(source.EQ_Limit AS DECIMAL(38, 6)) AS EQ_Limit,
        TRY_CAST(source.FL_Limit AS DECIMAL(38, 6)) AS FL_Limit,
        TRY_CAST(source.WS_Limit AS DECIMAL(38, 6)) AS WS_Limit,
        TRY_CAST(source.FR_Limit AS DECIMAL(38, 6)) AS FR_Limit,
        CASE
            WHEN source.BuildingTIV IS NOT NULL
             AND TRY_CAST(source.BuildingTIV AS DECIMAL(38, 6)) IS NULL THEN TRUE
            WHEN source.ContentsTIV IS NOT NULL
             AND TRY_CAST(source.ContentsTIV AS DECIMAL(38, 6)) IS NULL THEN TRUE
            WHEN source.BITIV IS NOT NULL
             AND TRY_CAST(source.BITIV AS DECIMAL(38, 6)) IS NULL THEN TRUE
            WHEN source.OtherTIV IS NOT NULL
             AND TRY_CAST(source.OtherTIV AS DECIMAL(38, 6)) IS NULL THEN TRUE
            ELSE FALSE
        END AS InvalidTIVFlag
    FROM source_enriched AS source
),

base_rows AS (
    SELECT
        rows.DatasetLabel, rows.ParticipationScale, rows.OEDID,
        rows.LocNumber, rows.AccNumber, rows.BranchName,
        rows.AccUserDef4, rows.AccUserDef5, rows.PolUserDef5,
        rows.CountryName, rows.CountryCode, rows.County, rows.AreaCode,
        rows.PostalCode, rows.AddressMatch, rows.LocUserDef2, rows.LocUserDef3,
        rows.ModelledLOB, rows.LOBMappingStatus, rows.SourceCurrency,
        rows.RateToGBP, rows.FXRecordCount, rows.FXDistinctRateCount,
        rows.FXRateStatus, rows.BuildingTIV, rows.ContentsTIV, rows.BITIV,
        rows.OtherTIV, rows.BlanketDeductible, rows.BuildingDeductible,
        rows.ContentsDeductible, rows.BIDeductible, rows.InvalidTIVFlag,
        CASE
            WHEN rows.InvalidTIVFlag THEN CAST(NULL AS DECIMAL(38, 6))
            ELSE COALESCE(rows.BuildingTIV, 0) + COALESCE(rows.ContentsTIV, 0)
               + COALESCE(rows.BITIV, 0) + COALESCE(rows.OtherTIV, 0)
        END AS TIV,
        CASE
            WHEN rows.RawParticipation IS NULL THEN CAST(1 AS DECIMAL(20, 8))
            WHEN rows.RawParticipation / rows.ParticipationScale
                 BETWEEN CAST(0 AS DECIMAL(20, 8)) AND CAST(1 AS DECIMAL(20, 8))
                THEN rows.RawParticipation / rows.ParticipationScale
            ELSE CAST(NULL AS DECIMAL(20, 8))
        END AS ParticipationFactor,
        CASE
            WHEN rows.RawParticipation IS NULL THEN TRUE ELSE FALSE
        END AS ParticipationDefaultedFlag,
        CASE
            WHEN rows.RawParticipation IS NULL THEN FALSE
            WHEN rows.RawParticipation / rows.ParticipationScale
                 BETWEEN CAST(0 AS DECIMAL(20, 8)) AND CAST(1 AS DECIMAL(20, 8))
                THEN FALSE ELSE TRUE
        END AS InvalidParticipationFlag,
        CASE
            WHEN UPPER(COALESCE(rows.ModelledLOB, '')) RLIKE '(^|_)FA(_|$)' THEN TRUE
            WHEN UPPER(TRIM(COALESCE(rows.AccUserDef4, ''))) = 'FINE ART' THEN TRUE
            WHEN UPPER(TRIM(COALESCE(rows.AccUserDef5, ''))) = 'FINE ART' THEN TRUE
            ELSE FALSE
        END AS IsFineArt,
        rows.RawQSCession,
        rows.EQ_Flag, rows.FL_Flag, rows.WS_Flag, rows.FR_Flag,
        rows.EQ_Deductible, rows.FL_Deductible,
        rows.WS_Deductible, rows.FR_Deductible,
        rows.EQ_Limit, rows.FL_Limit, rows.WS_Limit, rows.FR_Limit
    FROM numeric_rows AS rows
),

peril_rows AS (
    SELECT 'EQ' AS PerilCode, EQ_Deductible AS PerilDeductible,
        EQ_Limit AS PerilLimit, rows.*
    FROM base_rows AS rows
    WHERE UPPER(TRIM(CAST(EQ_Flag AS STRING))) IN ('1', 'TRUE', 'Y', 'YES')

    UNION ALL
    SELECT 'FL', FL_Deductible, FL_Limit, rows.*
    FROM base_rows AS rows
    WHERE UPPER(TRIM(CAST(FL_Flag AS STRING))) IN ('1', 'TRUE', 'Y', 'YES')

    UNION ALL
    SELECT 'WS', WS_Deductible, WS_Limit, rows.*
    FROM base_rows AS rows
    WHERE UPPER(TRIM(CAST(WS_Flag AS STRING))) IN ('1', 'TRUE', 'Y', 'YES')

    UNION ALL
    SELECT 'FR', FR_Deductible, FR_Limit, rows.*
    FROM base_rows AS rows
    WHERE UPPER(TRIM(CAST(FR_Flag AS STRING))) IN ('1', 'TRUE', 'Y', 'YES')
),

terms_rows AS (
    SELECT
        rows.*,
        CASE
            WHEN COALESCE(rows.PerilDeductible, 0) != 0
                THEN rows.PerilDeductible
            WHEN COALESCE(rows.BlanketDeductible, 0) != 0
                THEN rows.BlanketDeductible
            ELSE CAST(NULL AS DECIMAL(38, 6))
        END AS AppliedSingleDeductible,
        CASE
            WHEN COALESCE(rows.PerilDeductible, 0) != 0 THEN 'PERIL'
            WHEN COALESCE(rows.BlanketDeductible, 0) != 0 THEN 'BLANKET'
            ELSE 'COVERAGE'
        END AS DeductibleBasis,
        CASE
            WHEN rows.TIV IS NULL THEN CAST(NULL AS DECIMAL(38, 6))
            WHEN COALESCE(rows.PerilDeductible, 0) != 0
                THEN GREATEST(rows.TIV - rows.PerilDeductible, 0)
            WHEN COALESCE(rows.BlanketDeductible, 0) != 0
                THEN GREATEST(rows.TIV - rows.BlanketDeductible, 0)
            ELSE GREATEST(COALESCE(rows.BuildingTIV, 0)
                          - COALESCE(rows.BuildingDeductible, 0), 0)
               + GREATEST(COALESCE(rows.ContentsTIV, 0)
                          - COALESCE(rows.ContentsDeductible, 0), 0)
               + GREATEST(COALESCE(rows.BITIV, 0)
                          - COALESCE(rows.BIDeductible, 0), 0)
               + COALESCE(rows.OtherTIV, 0)
        END AS TIVAfterDeductible
    FROM peril_rows AS rows
),

measure_rows AS (
    SELECT
        rows.*,
        CASE
            WHEN rows.TIVAfterDeductible IS NULL THEN CAST(NULL AS DECIMAL(38, 6))
            WHEN COALESCE(rows.PerilLimit, 0) != 0
                THEN LEAST(rows.TIVAfterDeductible, rows.PerilLimit)
            ELSE rows.TIVAfterDeductible
        END AS GROSS,
        CASE
            WHEN NOT rows.IsFineArt THEN CAST(1 AS DECIMAL(20, 8))
            WHEN rows.RawQSCession IS NULL
                THEN CAST(1 AS DECIMAL(20, 8))
            WHEN rows.RawQSCession BETWEEN CAST(0 AS DECIMAL(20, 8))
                                       AND CAST(1 AS DECIMAL(20, 8))
                THEN CAST(1 AS DECIMAL(20, 8)) - rows.RawQSCession
            ELSE CAST(NULL AS DECIMAL(20, 8))
        END AS RetentionFactor,
        CASE
            WHEN rows.AddressMatch IS NULL THEN FALSE
            WHEN TRIM(CAST(rows.AddressMatch AS STRING)) IN ('', '0') THEN FALSE
            ELSE TRUE
        END AS IsGeocoded,
        CASE
            WHEN rows.CountryCode = 'US' THEN COALESCE(
                NULLIF(TRIM(rows.County), ''), NULLIF(TRIM(rows.AreaCode), ''),
                'UNKNOWN')
            ELSE CAST(NULL AS STRING)
        END AS StateValue,
        COALESCE(NULLIF(TRIM(rows.PostalCode), ''), 'UNKNOWN') AS PostcodeValue,
        CASE
            WHEN UPPER(COALESCE(rows.ModelledLOB, '')) LIKE '%HIG%' THEN 'HIG'
            WHEN UPPER(COALESCE(rows.ModelledLOB, '')) LIKE '%HSA%' THEN 'HSA'
            WHEN UPPER(COALESCE(rows.ModelledLOB, '')) LIKE '%3624%' THEN '3624'
            WHEN UPPER(COALESCE(rows.ModelledLOB, '')) LIKE '%S33%' THEN '33'
            WHEN UPPER(COALESCE(rows.ModelledLOB, '')) LIKE '%HIC%' THEN 'HIC'
            ELSE 'UNMAPPED'
        END AS BSCREntity
    FROM terms_rows AS rows
),

complete_rows AS (
    SELECT
        rows.*,
        CASE
            WHEN rows.GROSS IS NULL THEN CAST(NULL AS DECIMAL(38, 6))
            WHEN rows.ParticipationFactor IS NULL THEN CAST(NULL AS DECIMAL(38, 6))
            WHEN rows.RetentionFactor IS NULL THEN CAST(NULL AS DECIMAL(38, 6))
            ELSE rows.GROSS * rows.ParticipationFactor * rows.RetentionFactor
        END AS NET,
        CASE WHEN rows.RateToGBP IS NULL THEN CAST(NULL AS DECIMAL(38, 6))
             ELSE rows.TIV * rows.RateToGBP END AS TIV_GBP,
        CASE WHEN rows.RateToGBP IS NULL THEN CAST(NULL AS DECIMAL(38, 6))
             ELSE rows.GROSS * rows.RateToGBP END AS GROSS_GBP,
        CASE WHEN rows.RateToGBP IS NULL THEN CAST(NULL AS DECIMAL(38, 6))
             ELSE rows.GROSS * rows.ParticipationFactor
                  * rows.RetentionFactor * rows.RateToGBP END AS NET_GBP,
        CASE WHEN UPPER(TRIM(COALESCE(rows.LocUserDef2, ''))) IN
            ('1', 'TRUE', 'Y', 'YES') THEN TRUE ELSE FALSE END AS IsFloodRe,
        CASE WHEN UPPER(TRIM(COALESCE(rows.LocUserDef3, ''))) IN
            ('1', 'TRUE', 'Y', 'YES') THEN TRUE ELSE FALSE END AS FACFlag
    FROM measure_rows AS rows
),

/* Use canonical CountryCode in AggregationCountry to collapse source-label variants. */
level_rows AS (
    SELECT 'Aggs', 'COUNTRY', COALESCE(CountryCode, 'UNKNOWN'),
        COALESCE(CountryCode, 'UNKNOWN'), NULL, NULL, NULL, rows.* FROM complete_rows AS rows

    UNION ALL
    SELECT 'Aggs', 'STATE', CONCAT('US_', REGEXP_REPLACE(UPPER(StateValue), '[^A-Z0-9]+', '_')),
        COALESCE(CountryCode, 'UNKNOWN'), StateValue, NULL, NULL, rows.*
    FROM complete_rows AS rows WHERE StateValue IS NOT NULL


    UNION ALL
    SELECT 'Aggs', 'POSTCODE',
        CONCAT(COALESCE(CountryCode, 'UNKNOWN'), '_', REGEXP_REPLACE(UPPER(PostcodeValue), '[^A-Z0-9]+', '')),
        COALESCE(CountryCode, 'UNKNOWN'), StateValue, NULL, PostcodeValue, rows.*
    FROM complete_rows AS rows WHERE PostcodeValue != 'UNKNOWN'
    UNION ALL
    SELECT 'PRA', 'COUNTRY', COALESCE(CountryCode, 'UNKNOWN'),
        COALESCE(CountryCode, 'UNKNOWN'), NULL, NULL, NULL, rows.* FROM complete_rows AS rows

    UNION ALL
    SELECT 'PRA', 'STATE', CONCAT('US_', REGEXP_REPLACE(UPPER(StateValue), '[^A-Z0-9]+', '_')),
        COALESCE(CountryCode, 'UNKNOWN'), StateValue, NULL, NULL, rows.*
    FROM complete_rows AS rows WHERE StateValue IS NOT NULL

    UNION ALL
    SELECT 'BSCR', 'COUNTRY', COALESCE(CountryCode, 'UNKNOWN'),
        COALESCE(CountryCode, 'UNKNOWN'), NULL, NULL, NULL, rows.* FROM complete_rows AS rows

    UNION ALL
    SELECT 'BSCR', 'STATE', CONCAT('US_', REGEXP_REPLACE(UPPER(StateValue), '[^A-Z0-9]+', '_')),
        COALESCE(CountryCode, 'UNKNOWN'), StateValue, NULL, NULL, rows.*
    FROM complete_rows AS rows WHERE StateValue IS NOT NULL

    UNION ALL
    SELECT 'BSCR', 'NA_HU', 'BSCR_NA_HU', NULL, NULL, 'NA_HU', NULL, rows.*
    FROM complete_rows AS rows
    WHERE CountryCode IN ('US', 'CB', 'TC', 'BH', 'JM', 'VI', 'MX')

    UNION ALL
    SELECT 'BSCR', 'NA_EQ', 'BSCR_NA_EQ', NULL, NULL, 'NA_EQ', NULL, rows.*
    FROM complete_rows AS rows WHERE CountryCode IN ('US', 'CA')

    UNION ALL
    SELECT 'BSCR', 'JP', 'BSCR_JP', NULL, NULL, 'JP', NULL, rows.*
    FROM complete_rows AS rows WHERE CountryCode = 'JP'

    UNION ALL
    SELECT 'BSCR', 'EU', 'BSCR_EU', NULL, NULL, 'EU', NULL, rows.*
    FROM complete_rows AS rows
    WHERE CountryCode IN ('GB', 'UK', 'FR', 'DE', 'BE', 'NL', 'LU', 'AT', 'DK', 'SE', 'PL', 'CZ')

    UNION ALL
    SELECT 'BSCR', 'US_ALL', 'BSCR_US_ALL', NULL, NULL, 'US_ALL', NULL, rows.*
    FROM complete_rows AS rows WHERE CountryCode = 'US'

    UNION ALL
    SELECT 'BSCR', 'ALL_EX_US', 'BSCR_ALL_EX_US', NULL, NULL, 'ALL_EX_US', NULL, rows.*
    FROM complete_rows AS rows WHERE COALESCE(CountryCode, 'UNKNOWN') != 'US'

    UNION ALL
    SELECT 'BSCR', 'ALL', 'BSCR_ALL', NULL, NULL, 'ALL', NULL, rows.*
    FROM complete_rows AS rows

    UNION ALL
    SELECT 'Lloyds', 'COUNTRY', COALESCE(CountryCode, 'UNKNOWN'),
        COALESCE(CountryCode, 'UNKNOWN'), NULL, NULL, NULL, rows.* FROM complete_rows AS rows

    UNION ALL
    SELECT 'Lloyds', 'STATE', CONCAT('US_', REGEXP_REPLACE(UPPER(StateValue), '[^A-Z0-9]+', '_')),
        COALESCE(CountryCode, 'UNKNOWN'), StateValue, NULL, NULL, rows.*
    FROM complete_rows AS rows WHERE StateValue IS NOT NULL

    UNION ALL
    SELECT 'Lloyds', 'POSTCODE',
        CONCAT(COALESCE(CountryCode, 'UNKNOWN'), '_', REGEXP_REPLACE(UPPER(PostcodeValue), '[^A-Z0-9]+', '')),
        COALESCE(CountryCode, 'UNKNOWN'), StateValue, NULL, PostcodeValue, rows.*
    FROM complete_rows AS rows WHERE PostcodeValue != 'UNKNOWN'
),

active_rows AS (
    SELECT
        levels.SortOrder,
        rows.*
    FROM level_rows AS rows
    INNER JOIN aggregation_levels AS levels
        ON rows.UseCase = levels.UseCase
        AND rows.AggregationLevel = levels.AggregationLevel
        AND levels.IsActive = TRUE
),

reporting_rows AS (
    SELECT
        rows.*,
        CASE WHEN rows.UseCase = 'BSCR' THEN rows.BSCREntity
             ELSE rows.BranchName END AS ReportingEntity,
        CASE WHEN rows.UseCase = 'BSCR' THEN CAST(NULL AS STRING)
             ELSE rows.ModelledLOB END AS ReportingLOB,
        CASE
            WHEN rows.UseCase = 'BSCR'
             AND rows.AggregationLevel IN
                ('NA_HU', 'NA_EQ', 'JP', 'EU', 'US_ALL', 'ALL_EX_US', 'ALL')
                THEN CAST(NULL AS STRING)
            ELSE rows.CountryCode
        END AS ReportingCountryCode
    FROM active_rows AS rows
)

SELECT
    OEDID,
    DatasetLabel,
    UseCase,
    AggregationLevel,
    AggregationValue,
    SortOrder AS AggregationSortOrder,
    AggregationCountry,
    AggregationState,
    AggregationRegion,
    AggregationPostcode,
    ReportingEntity,
    ReportingLOB,
    PerilCode,
    ReportingCountryCode AS CountryCode,
    IsGeocoded,
    SourceCurrency,
    RateToGBP,
    DeductibleBasis,
    IsFloodRe,
    FACFlag,
    COUNT(1) AS SourceRowCount,
    COUNT(DISTINCT AccNumber) AS DistinctAccountCount,
    COUNT(DISTINCT LocNumber) AS DistinctLocationCount,
    SUM(TIV) AS TIV_SOURCE,
    SUM(GROSS) AS GROSS_SOURCE,
    SUM(NET) AS NET_SOURCE,
    SUM(TIV_GBP) AS TIV_GBP,
    SUM(GROSS_GBP) AS GROSS_GBP,
    SUM(NET_GBP) AS NET_GBP,
    SUM(CASE WHEN InvalidTIVFlag THEN 1 ELSE 0 END) AS InvalidTIVRowCount,
    SUM(CASE WHEN InvalidParticipationFlag THEN 1 ELSE 0 END) AS InvalidParticipationRowCount,
    SUM(CASE WHEN ParticipationDefaultedFlag THEN 1 ELSE 0 END) AS MissingParticipationRowCount,
    SUM(CASE WHEN LOBMappingStatus = 'AMBIGUOUS' THEN 1 ELSE 0 END) AS AmbiguousLOBRowCount,
    SUM(CASE WHEN LOBMappingStatus = 'UNMAPPED' THEN 1 ELSE 0 END) AS UnmappedLOBRowCount,
    SUM(CASE WHEN FXRateStatus IN ('MISSING', 'INVALID', 'CONFLICTING') THEN 1 ELSE 0 END)
        AS InvalidFXRowCount,
    parameters.GeographyMappingBasis
FROM reporting_rows
CROSS JOIN run_parameters AS parameters
GROUP BY
    OEDID, DatasetLabel, UseCase, AggregationLevel, AggregationValue,
    SortOrder, AggregationCountry, AggregationState, AggregationRegion,
    AggregationPostcode, ReportingEntity, ReportingLOB, PerilCode,
    ReportingCountryCode, IsGeocoded, SourceCurrency, RateToGBP,
    DeductibleBasis, IsFloodRe, FACFlag, parameters.GeographyMappingBasis;

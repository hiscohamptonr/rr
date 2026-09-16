/*
 * Edited by hamptonr @ 11.2.2026
 * Do i liek this script no. I edited the original script to include
 * the application of QS for Fine Art based on the 2026 EDM structure.
 * 
 * The QS is applied based on portfolio name.
 * 
 */
USE HISCO_UKEU_01JAN2026_010126_ROLLUP_KEEP_EDM
		
DECLARE @GBPUSD float
SET @GBPUSD = (select XFACTOR from [RMS_USERCONFIG].[dbo].[currfx] where CODE in ('GBP'))

	SELECT	
			poi.PORTNAME
			,'' as 'Reclassification'
			,loc.country as 'Countrycode'
			,geo.COUNTRY
			,accgrp.accgrpid
			,accgrp.ACCGRPNUM
			,'Currency' = LIMITCUR
			,'TSI' = SUM(loccvg.VALUEAMT * (
							CASE 
						WHEN pol.blanlimamt = 0 THEN 1
						ELSE pol.blanlimamt
						END
						))
			,'TSI_NET' = SUM(loccvg.VALUEAMT * (
							CASE 
						WHEN pol.blanlimamt = 0 THEN 1
						ELSE pol.blanlimamt
						END
						)
						* 
						
			case
				when poi.portnum like '%_QS' and poi.portnum like '%_FA_%' then 0.5
				when poi.portnum like '%_SRP' and poi.portnum like '%_FA_%' then 0.33333
				else 1.0
			end
			)
			
			,'TSI_GBP' = SUM(loccvg.VALUEAMT * (
							CASE 
						WHEN pol.blanlimamt = 0 THEN 1
						ELSE pol.blanlimamt
						END
						) * @GBPUSD / currfx.XFACTOR)
			,'TSI_USD_NET' = SUM(loccvg.VALUEAMT * (
							CASE 
						WHEN pol.blanlimamt = 0 THEN 1
						ELSE pol.blanlimamt
						END
						) / currfx.XFACTOR
						*
			case
				when poi.portnum like '%_QS' and poi.portnum like '%_FA_%' then 0.5
				when poi.portnum like '%_SRP' and poi.portnum like '%_FA_%' then 0.33333
				else 1.0
			end
			)
					
	FROM	
	loccvg
			inner join loc on loccvg.locid = loc.LOCID
			inner join property prop on loc.LOCID = prop.LOCID
			INNER JOIN accgrp accgrp ON prop.ACCGRPID = accgrp.ACCGRPID
			INNER JOIN policy pol ON accgrp.ACCGRPID = pol.ACCGRPID
			INNER JOIN portacct poa ON accgrp.accgrpid = poa.accgrpid
			INNER JOIN portinfo poi ON poa.portinfoid = poi.portinfoid
			

			INNER JOIN [RMS_GEOGRAPHY].dbo.country geo on geo.ISO2A = loc.COUNTRY
			INNER JOIN [RMS_USERCONFIG].[dbo].[currfx] currfx ON loccvg.LIMITCUR = currfx.CODE
			 
	WHERE PERIL = 3

		AND POLICYTYPE = 3
		AND (PORTNAME LIKE '%33%' OR PORTNAME LIKE '%3624%')
	
	GROUP BY 
		poi.PORTNAME
			,loc.COUNTRY
			,geo.Country
			,ACCGRP.ACCGRPID
			,ACCGRP.ACCGRPNUM
			,loccvg.LIMITCUR

	ORDER BY
		poi.PORTNAME
			,CountryCode
			,geo.Country

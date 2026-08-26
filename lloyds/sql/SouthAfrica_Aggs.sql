USE HISCO_UKEU_01JAN26_010126_ROLLUP_ByLOB_GC_v25_EDM
		
DECLARE @GBPUSD float
SET @GBPUSD = (select XFACTOR from [RMS_USERCONFIG].[dbo].[currfx] where CODE in ('GBP'))

	SELECT	
			poi.PORTNAME
			,'' as 'Reclassification'
			,loc.country as 'Countrycode'
			,geo.COUNTRY
			,loc.CITY
			,Loc.cresta
			,loc.COUNTY
			,LOC.STATE
			,loc.latitude
			,loc.longitude
			,loc.ADDRMATCH
			,loc.Zone3Name
			,accgrp.USERTXT2 as 'ACCGRPNAME'
			,loccvg.VALUECUR AS  'LIMITCUR'
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
end	)	
						
					
	FROM	loccvg
			inner join loc on loccvg.locid = loc.LOCID
			inner join property prop on loc.LOCID = prop.LOCID
			INNER JOIN accgrp accgrp ON prop.ACCGRPID = accgrp.ACCGRPID
			INNER JOIN policy pol ON accgrp.ACCGRPID = pol.ACCGRPID
			INNER JOIN portacct poa ON accgrp.accgrpid = poa.accgrpid
			INNER JOIN portinfo poi ON poa.portinfoid = poi.portinfoid
			

			INNER JOIN [RMS_GEOGRAPHY].dbo.country geo on geo.ISO2A = loc.COUNTRY
			INNER JOIN [RMS_USERCONFIG].[dbo].[currfx] currfx ON loccvg.LIMITCUR = currfx.CODE
			 
	WHERE PERIL =1

		AND POLICYTYPE = 1
		--AND PORTNAME NOT IN ('PROPERTY ALL', 'HIC ALL')
		--AND geo.Country = 'United States'
		AND LOC.cntrycode = 'ZA'
		AND (PORTNAME LIKE '%33%' OR PORTNAME LIKE '%3624%')
	GROUP BY 
		poi.PORTNAME
			,loc.COUNTRY
			,geo.Country
			,prop.ACCGRPID
			,ACCGRPNUM
			,ACCGRPNAME
			,accgrp.USERTXT2
			,loc.LATITUDE
			,loc.LONGITUDE
			,CEDANTID
			,LIMITCUR
			,loc.cresta
			,loc.CITY
			,LOC.STATE
			,loc.ADDRMATCH
			,loc.COUNTY
			,loccvg.VALUECUR
			,loc.Zone3Name
	ORDER BY
		poi.PORTNAME
			,CountryCode
			,geo.Country
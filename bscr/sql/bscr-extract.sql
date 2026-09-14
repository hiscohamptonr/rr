-- BSCR extraction query. Set @peril and @policy_type before execution.
DECLARE @peril int = 1;
DECLARE @policy_type int = 1;



with loc_tiv as (
	select
		locid,
		peril,
		deductamt,
		deductcur,
		sum(valueamt) valueamt

	from loccvg
	where peril = @peril
	group by
		locid,
		peril,
		deductamt,
		deductcur,
		limitamt,
		limitcur

	)



, gross_loctiv as (


	select
		case when valueamt < deductamt then 0
		else valueamt
		end as pml,
		*

		from loc_tiv

)


, selected_locs as (

select  locid, accgrpid, locnum,
case when addrmatch = 0 then 0 else 1 end as is_geocoded,
case when cntrycode = 'US' then state else '' end as state,
cntrycode, country
from loc

	)


, loc_exposure as (

	select

	sum(gross_loctiv.pml) as pml,
	selected_locs.accgrpid,
	state, cntrycode, country,
	is_geocoded
	from gross_loctiv
	inner join selected_locs on selected_locs.locid = gross_loctiv.locid
	group by accgrpid, state, cntrycode, country, is_geocoded

	)


, policies as (

	select distinct policy.accgrpid, policyid, partof,
	case when blanlimamt = 0 then 0 else partof end as policy_limit,
	undcovamt, blandedamt, accgrp.userid1, accgrp.branchname, accgrp.UWritrname, is_geocoded
	from policy
	inner join accgrp on accgrp.accgrpid = policy.accgrpid
	inner join  loc_exposure on loc_exposure.accgrpid = accgrp.accgrpid and loc_exposure.accgrpid = policy.accgrpid
	where policy.policytype = @policy_type

	)



, policy_exposure as (

		select
			case when sum(pml) > policy_limit then policy_limit else sum(pml) end as pml,
			policies.accgrpid,
			uwritrname,
			state,
			userid1,
			branchname,
			cntrycode,
			policies.is_geocoded
	from loc_exposure
	inner join policies on policies.accgrpid = loc_exposure.accgrpid
	group by
			policies.accgrpid,
			uwritrname,
			state,
			userid1,
			branchname,
			cntrycode,
			policies.is_geocoded,
			policy_limit

	)




select sum(pml) as pml, accgrpid, uwritrname, state, userid1, branchname, cntrycode, is_geocoded from policy_exposure
group by state, cntrycode, userid1, uwritrname, branchname, is_geocoded, accgrpid
order by sum(pml) desc


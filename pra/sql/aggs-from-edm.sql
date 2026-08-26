
with loc_tiv as (
	select
		locid,
		peril,
		deductamt,
		deductcur,
		sum(valueamt) valueamt

	from loccvg
	where peril = 2
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

select locid, accgrpid, locnum,

case when cntrycode = 'US' then state else '' end as state,
cntrycode, country  from loc

	)



, loc_exposure as (

	select

	sum(gross_loctiv.pml) as pml,
	selected_locs.accgrpid,
	state, cntrycode, country
	from gross_loctiv
	inner join selected_locs on selected_locs.locid = gross_loctiv.locid
	group by accgrpid, state, cntrycode, country

	)



, policies as (

	select distinct policy.accgrpid, policyid, partof,

	case when blanlimamt = 0 then 0 else partof end as policy_limit,

	undcovamt, blandedamt, accgrp.userid1, accgrp.branchname, accgrp.UWritrname from policy
	inner join accgrp on accgrp.accgrpid = policy.accgrpid
	inner join  loc_exposure on loc_exposure.accgrpid = accgrp.accgrpid and loc_exposure.accgrpid = policy.accgrpid
	where policy.policytype = 2

	)



, policy_exposure as (

		select
			case when pml > policy_limit then policy_limit else pml end as pml,
			policies.accgrpid,
			uwritrname,
			state,
			userid1,
			branchname,
			cntrycode
	from loc_exposure
	inner join policies on policies.accgrpid = loc_exposure.accgrpid

	)




select sum(pml), state,userid1,cntrycode,uwritrname from policy_exposure
group by state,cntrycode,userid1,uwritrname




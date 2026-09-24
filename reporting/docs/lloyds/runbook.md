---
Report: RDS
Time: 3d
---

# Lloyd's — RDS and Supplementary

Work from the `reporting/` directory. Use working copies from
`lloyds/workbooks/`; match the filename endings below. The checked-in files
are workings/source evidence, not the final RDS submission template. Do not
treat cached values, embedded emails, or a successful SQL command as producer
or approval evidence.

Before every branch, confirm the approved reporting-period source, producer,
measure (gross/net), currency/unit, FX date/direction, scale/retention factors,
geography mapping, and final destination. The SQL files require an external
EDM/SQL Server and credentials; no database connection is available in this
repository. Run an approved SQL client from the stated working directory and
retain the exact command, database identity, parameters, raw export, and
reconciliations.


## RDS Events
The RDS events are selected from the ELTs using the `lloyds/rds/eventids_for_rds.xlsx` workbook (path relative to `reporting/`).

This lists the events to be selected from both Verisk and Risklink.

Select the eventids and copy the results to the RDS workbook ('2026 Lloyds RDS UKEU Retail.xlsx')

Where possible the blending approach was used, e.g. EU WS is 100% weighted to risklink therefore the risklink loss was used.

As of January 2026 only EUWS and UKFL were the only perils to be updated. Going forward you should have model results for international
perils, therefore the blending will need to be done on the RDS losses too.


## South Africa

1. Review and approve `lloyds/sql/SouthAfrica_Aggs.sql` before execution. It
   hard-codes `HISCO_UKEU_01JAN26_010126_ROLLUP_ByLOB_GC_v25_EDM`, `PERIL = 1`,
   `POLICYTYPE = 1`, `LOC.cntrycode = 'ZA'`, and broad portfolio-name filters.
   Its grouped output is A:R: `PORTNAME, Reclassification, Countrycode,
   COUNTRY, CITY, CRESTA, COUNTY, STATE, latitude, longitude, ADDRMATCH,
   Zone3Name, ACCGRPNAME, LIMITCUR, TSI, TSI_NET, TSI_GBP, TSI_USD_NET`.
2. Stop until the currency control is resolved: the output labels
   `loccvg.VALUECUR` as `LIMITCUR`, but the FX join uses
   `loccvg.LIMITCUR` (`SouthAfrica_Aggs.sql:20,71`). The query also joins
   account/policy/portfolio tables at account-group grain; capture
   before/after-join row and amount checks.
3. In a working copy of the workbook ending `South Africa EQ - Jan 2026.xlsx`,
   preserve `Core data!S` (`SCALE_FACTOR`) and the helper columns. Paste the
   approved A:R export into `Core data!A2`, then fill the approved formulas
   through the complete source range: `T` is `S*O` (`scaled_tsi`) and `U`
   derives a two-character suffix from `Zone3Name` (`cresta_2_digit`). The
   checked-in workbook seeds these formulas at rows 2:3 and uses shared
   formulas through row 53; verify the complete approved range after loading
   rather than assuming its cached helper values are current.
4. The report `05 South Africa EQ Aggs` is dated `01/01/2024` and its
   `C8:C102` formulas sum `Core data!T:T` by a fixed `Core data!U1:U53`
   range. Reconcile this report range, date, scaling, CRESTA coverage, and
   excluded/unmapped rows before any refresh; do not call the cached report a
   January-2026 result.

## California

1. Confirm the wildfire proxy/PML, producer, report date, and county mapping
   before running `lloyds/sql/FA_California_Aggs.sql`. The query hard-codes
   `HISCO_UKEU_01JAN26_010126_ROLLUP_ByLOB_GC_v25_EDM`, `PERIL = 4`,
   `POLICYTYPE = 4`, California/US scope, and the same broad portfolio filter.
   It returns A:M: `PORTNAME, cntrycode, COUNTRY, statecode, county, cresta,
   accgrpid, ACCGRPNUM, Currency, TSI, TSI_NET, TSI_GBP, TSI_USD_NET`; it does
   not itself establish a wildfire PML or approved proxy.
2. In a working copy of the workbook ending `California WF.xlsx`, paste the
   approved A:M export into `Core data!A2`, preserve N, and fill the county
   helper through the complete source range. `Core data!N` extracts text before
   `"County"` from column E, while `06 California Wildfire Aggs!C8:C65`
   sums column M by that helper. Check blank/non-matching county values and
   formula errors rather than silently dropping them.
3. The checked-in report says `Static property exposure data as at 01/01/2025
   (USD units)` (`06 California Wildfire Aggs!B3`), whereas the SQL database
   name is a January-2026 EDM. Resolve the as-of date, lineage, proxy/PML, and
   currency before using or refreshing the report.

## Rest of World

1. Obtain separately approved EQ, FR, FL, and WS extracts. The checked-in
   `lloyds/sql/Supplementary Info - Workings - ROW Aggs - SQL.sql` is not four
   peril queries: it hard-codes `PERIL = 3` and `POLICYTYPE = 3`, and filters
   portfolio names with `%33%` or `%3624%`. Its grouped A:K output is
   `PORTNAME, Reclassification, Countrycode, COUNTRY, accgrpid, ACCGRPNUM,
   Currency, TSI, TSI_NET, TSI_GBP, TSI_USD_NET`. It also reads live FX and
   joins policy/portfolio membership at account-group grain. Treat its output
   as a single candidate extract, not as four approved perils.
2. In the workbook ending `ROW.xlsx`, paste each approved A:K extract with
   headers into row 2 of the matching sheets (`EQ Extract - Open Market`,
   `FR Extract  - Open Market` [two spaces before `-`], `FL Extract - Open
   Market`, and `WS Extract - Open Market`). Preserve L and fill approved M
   formulas (`TSI_USD_Scaled = I*L`) through the complete source range.
   Retain the scale-factor source and reconcile source, USD, net, and scaled
   measures separately.
3. Do not infer row counts from worksheet dimensions. Current defined/filter
   ranges include EQ/FR `A1:M6757`, FL `A1:T5676`, and WS `A1:M4988`, while
   stale helper rows/formulas extend beyond some of those ranges. Reconcile
   headers, rows, totals, currencies, and stale helper errors before changing
   pivot sources. Then refresh `3. RoW Exposure Monitoring` only after its
   country/peril mapping and pivot-range changes are approved.
4. The report is labelled `Exposure data as at 1st Jan 2026 (USD units)` but
   the SQL is not a four-peril producer and the workbook contains broken
   defined names/external links. Do not blindly refresh links or present the
   cached report as a lineage-complete submission.

## Europe

1. Obtain separately approved earthquake and flood extracts. There is no
   matching EU producer/query in the repository; `lloyds/sql/rds-event-select.sql`
   is empty. The checked-in EU workbook is therefore not a runnable SQL
   workflow.
2. In a working copy of the workbook ending `EU Cresta.xlsx`, paste approved
   source columns A:R into `Core data EQ!A2` and `Core data FL!A2`, preserve
   S:U, and verify scale and formula coverage before refresh. The report
   `11 LIC EU CRESTA` sums `Core data EQ!U:U` and `Core data FL!U:U` by CRESTA
   keys in columns C and G.
3. Stop on the current measure/FX defect. `Core data FL` uses
   `T2=S2*R2`, `T3:T7822=S*P`, and `T7823:T7891=S*R`; every U row then applies
   `T*Fx!$C$7`, where `Fx!C7 = 1.25/1.21`. The report is labelled `As at
   01/07/2024 (EURO units)`. The FL source/filter ends at row 7,891, but
   helper formulas continue through row 8,699; quarantine those trailing rows
   before changing ranges. Do not fill down, refresh, or describe this as a
   current EUR result until the source measure, FX basis/direction/date, and
   uniform formula pattern are approved and reconciled.
4. Reconcile unmatched/blank/`GBR_*` CRESTA keys and all included plus
   excluded exposure before using `11 LIC EU CRESTA`. Preserve the source
   workbook and any received instructions as provenance.

## Finish

1. Check currency, units, scales, dates, missing geography, unmapped CRESTA or
   county values, stale rows, external links, and formula errors. Clear only
   controlled source rows; never overwrite headers, formulas, mappings, pivots,
   validation, or raw evidence.
2. Reconcile each report at its stated grain to the approved extract,
   including all agreed exclusions and source-to-USD/EUR movements. Save the
   reviewed workbook and raw/grouped outputs together in a run-specific
   location.

**Still needed:** the final Lloyd's submission template and destination-cell
map for all four branches, plus approved producers/proxies, source lineage,
and reviewer sign-off.

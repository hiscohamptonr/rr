# Calculation discrepancy register

[Start here](../README.md) · [Actionable decision register](decisions.md) ·
[Shared controls](operating-controls.md)

This register preserves observed defect evidence. Track the missing decisions,
responsible roles, and resolution artifacts in the linked decision register;
neither document grants production approval.

**Scope:** checked-in January 2026 code, SQL, source workbooks, and calculation
workbooks. This is an evidence register, not a proposed logic fix. A result is
not approved for production until its required owner decision is recorded in a
run pack.

**Method:** Python/SQL and OOXML workbook formulas, pivot caches, named ranges,
source ranges and cached values were inspected. BSCR entries below distinguish
the current SQL-only workflow and workbook from historical evidence. The other
January-baseline line references are historical unless explicitly labelled
current; use the current process runbooks for paths and execution instructions.
PRA no longer contains the raw BSCR helper/SQL sheets; Global Exposures now
calculates from offline CSVs. These workflow changes do not establish approval
or resolve the remaining financial issues. No live SQL Server execution or
Excel recalculation is claimed by this review.

## How to use this register

- **Critical/High:** stop the affected handoff or calculation route.
- **Medium:** resolve before a changed input, refresh, or next reporting cycle;
  it may be a prospective control rather than a proven current misstatement.
- An owner decision must identify the authoritative source/methodology and the
  supporting evidence. “The command completed” is not a decision.

## Global Exposures

| ID | Severity | Verified evidence | Effect | Required owner decision |
|---|---|---|---|---|
| GEX-001 | High | `exposures.py:203-206` matches Fine Art factors against `PI.Portnum LIKE`; `PORTNAME` is merely selected at `:234`. `_` is a SQL wildcard. | The documented/assumed portfolio-name rule can apply to the wrong population. | Approve `PORTNUM` versus `PORTNAME` and literal/wildcard pattern semantics. |
| GEX-002 | High | `BLANLIMAMT` is reduced with `MAX` (`:199-201`, `:223-229`), multiplied into TIV, and an unmatched policy defaults to `1` (`:244-248`). | A monetary limit may be used as a factor; policy absence is silently treated as no adjustment. | Approve policy-term formula, grain, null/zero behaviour, and unmatched-policy treatment. |
| GEX-003 | High | Every qualifying `portacct` membership is joined to locations (`:231-252`) without a cardinality/allocation control. | Multiple memberships duplicate TIV/loss; accounts without membership disappear. | Approve portfolio membership cardinality/allocation and unmatched-account treatment. |
| GEX-004 | High | Only null PML is checked after merge (`:295-303`); missing-PML override leaves null loss (`:334-335`) and grouped pandas sums skip nulls (`:354-362`, `:389-398`). | Invalid/missing PML can select unintended results or report zero aggregate loss as success. | Approve PML key, range, and referential rules; prohibit/replace the override or make loss unknown-preserving. |
| GEX-005 | High | Empty/unusable exposure, no polygons, and no impacts become non-error statuses (`:469-513`); summary is Complete unless Error (`:427`), and main can return zero (`:661-664`). | A zero result can look complete without proving a valid zero population. | Define approved zero-data outcomes and required independent evidence. |
| GEX-006 | High | Bad shape points/small polygons are dropped (`:163-174`), geometries repaired (`:187-190`), and location coordinates dropped/range-filtered (`:274-277`) without a persisted reconciliation. | TIV or polygon area can silently disappear/change. | Approve rejection/repair tolerance and required dropped-row/TIV/geometry evidence. |
| GEX-007 | Medium | Existing output directories are accepted (`:446-447`); files are overwritten sequentially (`:563-578`); empty result frames have no fixed schema (`:339-341`, `:371-373`, `:547-551`). | A reused directory can contain mixed/partial runs; empty CSVs can lack headers. | Require controlled run-specific/atomic publication and fixed schemas, or formally accept external controls. |
| GEX-008 | Medium | Default connection string has `TrustServerCertificate=yes` (`:59-77`). | Database certificate identity is not validated. | Approve this exception or require validated TLS. |
| GEX-009 | Medium | Connection identity/time is collected (`:84-92`) but not written with the output pack (`:563-595`). | The pack cannot prove configuration, database identity, revision, or checksums. | Approve external evidence or require a persisted manifest. |

## BSCR Schedule X

**Current population route:** `bscr-output.sql` → `BSCR_Auto_Population.xlsx`.
Findings about the older `BSCR_Workings.xlsx` or historical templates remain
reference evidence; they do not describe the generated population workbook.
The two-step refresh and separate reconciliation evidence are in the
[BSCR guide](bscr/runbook.md).
The legacy workings workbook was subsequently restored to revision `d6aedfe`
(21 September 2026). Cell-range findings below describe the previously audited
versions, not a new audit of that restored file; native Excel opening must still
be confirmed.

| ID | Severity | Verified evidence | Effect | Required owner decision |
|---|---|---|---|---|
| BSCR-001 | High — older workbook | Historical `output!A:F` was static. The later `BSCR_Workings.xlsx` uses `SUMIFS` but has a fixed list of 69 entity/region/geocode keys. The new `BSCR_Auto_Population.xlsx` instead reads the eight-column `BSCRInput` table directly, with no intermediate fixed key list. | The older route can omit added keys. The new route avoids that specific defect but still needs complete input and entity coverage. | Use the documented current population route; retain the older workbook as reference and approve coverage for each run. |
| BSCR-002 | High | Verified on the supplied EDM snapshot: the legacy policy-side geocode join duplicates exposure for 184 accounts with both geocode flags. Restoring the original SQL and Python reproduces all 452 historical CSV rows; fixing only that join explains the USD 4.813bn gross / USD 3.051bn net reduction and 285 fewer grouped rows in `ALL`. `bscr-output.sql` contains the correction; `bscr-extract-legacy.sql` intentionally preserves the historical defect for comparison. | The geocode duplication is confirmed, not an unexplained source loss. Policy-ID grouping has no material effect on this snapshot because no account has multiple type-1 policies. Caps still apply by policy/geography/geocode group, not necessarily once per contract. | Retain the geocode correction; separately approve the intended policy-cap allocation grain. See `bscr/reconcile/results/BSCR_Reconciliation.xlsx` for replay evidence. |
| BSCR-003 | High | Current SQL includes every US state in NAHU, preserving the historical Python/CSV all-US behaviour. February workings omitted the US portion; the later March USD workings and April templates restored it. | The February omission is a workbook-version difference, not the intended current mapping. State-restricted alternatives remain a methodology question. | Do not copy the February omission to force agreement; approve the geographic scope for the reporting run. |
| BSCR-004 | High | Both retained queries count grouped source rows rather than distinct policy IDs. The new population workbook sums those values and implements the agreed geocode proxy for X(f). | These figures reproduce the existing counting convention, not a proven distinct-contract count. | Confirm acceptance of grouped-row counts or supply a controlled contract-identity/counting rule. |
| BSCR-005 | High — historical templates | Each supplied entity template retains 39 cached X(b) `#REF!` errors, an X(f) `#VALUE!` and external workbook links. The generated population workbook has no external workbook links and does not carry these broken formulas forward; missing supplemental inputs are blank. | Historical files are evidence, not automatically usable current returns. The new population workbook is still incomplete without manual inputs and review. | Review the generated workbook in Excel and identify the controlled filing template and remaining manual fields. |
| BSCR-006 | Medium | The retained queries emit final aggregates only. Uploaded EDM tables now support a verified local replay: 452 legacy rows, 737 current rows, and an isolated geocoding bridge explaining the complete `ALL` difference. | The reconciliation is evidenced for this snapshot, but final query output alone does not diagnose a later snapshot. | Preserve source metadata and evidence; repeat account/policy/location diagnostics when later differences arise. |
| BSCR-007 | Medium — older workbook | `BSCR_Workings.xlsx` has no source Excel table or Power Query connection. The new population workbook has the eight-column `BSCRInput` Excel table and direct formulas. | The old A:G loading instructions do not apply to the new workbook. Stale rows beneath a shorter paste can still contaminate any manual refresh. | Clear previous data rows while preserving the new table/headers, then paste all eight current-output columns. |
| BSCR-008 | High — older workbook | `BSCR_Workings.xlsx` reverses Japanese earthquake/typhoon region references. The new population workbook explicitly uses `is_jp_eq`/peril 1 for earthquake and `is_jp`/peril 2 for typhoon. | The old reference workbook is unsafe as a direct current-output consumer; the new route corrects this mapping. | Use and review the current mapping; do not carry the old reversed formulas into the final return. |
| BSCR-009 | High — older workbook | The old output pivot references only `BSCR Output!A1:J50`, omitting later `is_jp_eq`/`is_non_us` rows. The new population workbook has no pivot dependency. | This fixed-pivot omission does not apply to the new direct-formula route. | Retain the finding if the old workbook is reused; otherwise reconcile the new entity sheets directly to their intended input populations. |
| BSCR-010 | High — older workbook | Older workings contain hard-coded 1.35 conversions alongside a Settings FX cell. Current SQL converts to full USD; the new population workbook only divides by one million. | Loading USD into the old FX formulas would convert twice. Changing Settings alone would not fix all paths. | Keep FX in SQL for the current route. Do not add workbook FX or reuse the old conversion formulas. |
| BSCR-011 | Medium — archived Python | The two retained aggregate queries export eight columns including `peril_id`. `old-process/BSCR_UKEU_offline.py` is the older seven-column CSV workflow; `old-process/BSCR_UKEU.py` is the original Marimo application. | Neither archived script is the current population-workbook producer. Dropping `peril_id` to fit an older input contract would lose essential scope information. | Use current SQL and the eight-column workbook table. Keep historical replay and current populations separate. |
| BSCR-012 | High — historical currency | The corrected February template family (33 original and four v2 files) numerically matches pre-FX source amounts divided by 1,000, despite USD headings. The later workings explicitly apply 1.35. | Numerical agreement with the old output does not mean the templates were in the required currency. Currency conversion and million scaling were separate issues. | Retain the explicit currency finding in the reconciliation workbook. Current SQL produces USD; apply million scaling only in the population workbook. |
| BSCR-013 | High | The supplied current output has two GB European-wind rows with a blank entity, totalling approximately USD 26.353bn gross/net. They are retained in SQL input but not assigned to the five entity tabs. | Unclassified exposure is outside the entity schedule populations. This is not part of earthquake `ALL` and must not be silently assigned or treated as reconciled entity exposure. | Resolve the account/entity classification or retain an explicit controlled disposition before using the return. |

## PRA aggregates

| ID | Severity | Verified evidence | Effect | Required owner decision |
|---|---|---|---|---|
| PRA-001 | Critical | All four `pivot_eq` pivots resolve to `Table3`, not `Table32`; `pivot_eq!S6 = 255,773,631,164.60`, while `Table32` totals `233,586,155,482.80`. | Checked-in earthquake output is all-peril/stale. | Approve repointing all earthquake pivots to `Table32` and controlled refresh/reconciliation. |
| PRA-002 | High | All eight pivots use `Sum of pml` (`fld="0"`); `Table3!M`/`Table32!M` calculate `pml * 1.25`. Cached converted totals are `319,717,038,955.75` and `291,982,694,353.50`. | Pivot output omits the 1.25 conversion and cannot be described as Agg_USD without approval. | Approve reporting currency and whether the pivots sum `pml` or `Agg_USD`. |
| PRA-003 | High | `pivot_eq!K102,K219,K779` are populated PRA-region `#N/A` totalling `742,256,923.70`; nine populated CDS `#N/A` rows total `508,139,353.59` (`AC25:AD25` exposes the latter). | Geography/CDS output is incomplete. | Supply mappings or approve quantified exclusions before use. |
| PRA-004 | High | `pra/sql/aggs-from-edm.sql:11,71` hard-codes 2/2 and no database; Python defaults to `...v25_EDM` and 1/1; no cache proves Table3 lineage. | No artifact proves the approved all-peril database, producer, or scope. | Approve database/codes or provide original producer/run record. |
| PRA-005 | High | Workbook Table2 NAHU covers BH/MX/TC/JM/CB and seven US states; Python includes VI/other states and its current defect includes all non-null US states. | Workbook/Python overlapping BSCR populations materially differ. | Approve geography and implementation before selecting a route. |
| PRA-006 | Medium | Table2 applies 33%; Python uses 0.3333. Current SRP exposure is `5,049,115,707.19`, implying about `16.66m` difference. | Net SRP values differ by route. | Approve retention precision. |
| PRA-007 | Medium | `Table32` remains `A1:M838`; only A:E rows 2–832 are populated, leaving 833–838 residual blank formula rows. | A refreshed cache can include blank/error categories. | Resize to populated range during controlled load. |
| PRA-008 | Medium | `Table2!Q2:Q270675` is empty; the North American earthquake panel `AC55:AF60` is blank. | This workbook cannot calculate the NA earthquake panel. | Declare it out of scope or approve an authoritative calculation route. |

## Lloyd's supplementary information

| ID | Severity | Verified evidence | Effect | Required owner decision |
|---|---|---|---|---|
| LLOYD-001 | Critical | EU flood `T2=S2*R2`, `T3:T7822=S*P`, `T7823:T7891=S*R`; `U=T*Fx!C7`. `Fx!C7=1.25/1.21`; report is dated 01/07/2024 EUR while email gives 2026 GBP/EUR 1.15. | Flood EUR output mixes source and USD measures with incompatible/stale FX. | Approve one measure, FX base/direction/date, and uniform 2026 formula pattern. |
| LLOYD-002 | High | EU EQ core U is `31.0595bn` with `8.4589bn` report-matched; FL is `23.0958bn` with `10.2890bn` matched. Blank/`GBR_*` keys have no defined eligibility. | Most cached exposure is silently outside report keys. | Define eligibility and quarantine/reconcile every unmatched CRESTA value. |
| LLOYD-003 | High | SA report says USD but `Core data!T2=S2*O2` uses gross source TSI; `91.074m` across 15 blank-zone rows is absent from report. `U` uses `RIGHT(Zone3Name,2)` while Notes has a different province map. | Basis is unresolved and 38.5% of cached exposure is excluded. | Approve gross/net/currency, CRESTA derivation, and unmapped-zone treatment. |
| LLOYD-004 | High | `SouthAfrica_Aggs.sql` labels output currency from `VALUECUR` (`:20`) but FX joins on `LIMITCUR` (`:71`). | Label and FX denominator can be different currencies. | Approve one currency field for output, FX join, and grouping. |
| LLOYD-005 | High | RoW M is source-currency `TSI_NET * L`, but M/report say USD; all four extracts have the same 4,987 rows and country totals (`22.3138bn`); SQL is only 3/3. | Peril values are neither evidenced as USD nor distinct approved extracts. | Approve source measure/unit and distinct producer or explicit proxy per peril. |
| LLOYD-006 | High | Email says wildfire needs discussion; California report is dated 01/01/2025 while SQL names January-2026 EDM. S33 Weather has California data but no county. | Cached USD `16.2908m` reconciles arithmetically, but proxy, lineage, and as-of date are unapproved. | Approve proxy/PML, county producer, and applicable date. |
| LLOYD-007 | High | Each SQL joins policy/portfolio at account-group grain, multiplies by `blanlimamt`, uses wildcard QS/SRP patterns, broad `%33%/%3624%` filters, and live FX. | SQL-derived results can change through duplication, terms, filters, or rates without evidence. | Approve query grain, limit semantics, literal lists, frozen FX, and before/after join checks. |
| LLOYD-008 | High | Workbook audit summaries hold blank run-record instructions, not producer evidence. Email `Rawdata.xlsx` equals the checked-in 27-column S33 workbook, which cannot populate county/CRESTA schemas. | Cached inputs have no demonstrated approved lineage. | Evidence producer/extract for each report or classify cache as non-production. |
| LLOYD-009 | Medium | RoW inputs end at 4,988 (pivot sources `A1:M4988`), but FL L:M rows 4,989–5,676 each contain 688 cached `#N/A` values; EQ/FR M also extends past input rows. SA inputs end at 50 within its fixed `SUMIF` range. EU FL inputs end at 7,891 but T:U continues to 8,699; reports use whole-column `SUMIFS`. | Current RoW pivots exclude stale helper errors, but expanding ranges can include them; worksheet dimensions overstate input populations. | Approve input-row, stale-helper and formula-coverage checks before changed loads or range expansion. |
| LLOYD-010 | Medium | RoW has `#REF!` defined names; SA/California/EU retain external links and a `CRESTA` name resolving to `[1]Reference!#REF!`. | Workbooks violate their stated link/error gate and may update unavailable sources. | Identify output-relevant names/links and approve/remediate each. |

## Dataiku OED aggregates — historical baseline
The entries below document the superseded uncapped baseline at commit
`d264675` (`dataiku/Dataiku-Aggs.sql` before the current canonical query).
Revalidate them against the canonical policy-terms query before using them as
current defects.

| ID | Severity | Verified evidence | Effect | Required owner decision |
|---|---|---|---|---|
| DATAIKU-001 | Medium | Raw TIV is summed and only FX applied (`Dataiku-Aggs.sql:282-285,519-520`); `LocParticipation` is selected (`:100,170`) but unused. | Current “gross TIV” terminology is ground-up, not participation-adjusted gross. | Confirm terminology or relabel the current baseline. |
| DATAIKU-002 | High | Raw LOB rows are deduplicated before trim/null-safe matching (`:109-119`, `:182-194`). | One OED row can multiply exposure and counts. | Approve normalised key and zero/multiple mapping treatment. |
| DATAIKU-003 | High | FX uses `MAX(RateToGBP)` (`:124-141`); selected exception logic misses negative/conflicting raw rates (`:175-180`, `:519-520`). | GBP can use arbitrary/conflicting or negative rates with hidden defects. | Define valid/conflict rules and missing/invalid GBP treatment. |
| DATAIKU-004 | High | Components are `COALESCE(TRY_CAST(...),0)` with no validity flags (`:239-246`). | Malformed values are indistinguishable from null/zero and can understate exposure. | Approve component/row eligibility and exception counts. |
| DATAIKU-005 | High | No retention is calculated; entity uses substring precedence (`:286-293`); only GrossTIV reaches aggregation (`:493,519-520`). | QS/SRP net and deterministic entity logic are not implemented. | Approve markers, precedence, retention, and both/no-marker handling. |
| DATAIKU-006 | Medium | Current code is `NA_EQ` (`:56,391`) and regional sets are hard-coded (`:385,395,405,415,425,435`). | Planned `NAEQ` is a compatibility change; membership is unversioned approximation. | Approve migration and versioned country sets. |

## Dataiku OED aggregates — current query

| ID | Severity | Verified evidence | Effect | Required owner decision |
|---|---|---|---|---|
| DATAIKU-007 | High | `Dataiku-Aggs.sql` `fx_controls` nulls non-positive rates, but its separate count-only status CASE labels a unique rate `VALID` (repeated identical rates: `DUPLICATE_CONSISTENT`). Final `InvalidFXRowCount` counts neither status. | GBP measures can be null without an FX exception; aggregate sums can omit those amounts. | Require independent rate-positivity/null-GBP reconciliation before relying on totals, and approve corrected FX controls. See the [current technical guide](dataiku/current-technical-guide.md#enrichment-and-mapping-controls). |

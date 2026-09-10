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

**Method:** the referenced Python/SQL and OOXML workbook formulas, pivot caches,
named ranges, source ranges, and cached values were inspected. Workbook findings
describe the checked-in state; Excel refresh behaviour still requires validation
in a controlled copy.

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

| ID | Severity | Verified evidence | Effect | Required owner decision |
|---|---|---|---|---|
| BSCR-001 | High | Workings `output!A2:F50` are static; `piv` sources `output!A1:J50`. `Sheet1!D384:E384` is `121,288,000,000` while `output!C16:D16` is `121,287,644,939.62`; cached pivot is about USD 0.479m stale after conversion. | Refreshing pivots does not load current `Sheet1`; mapped limits can be stale. | Approve authoritative data and an exact rebuild/clear/reconcile procedure for `output!A:F`. |
| BSCR-002 | High | `BSCR_UKEU.py:120-153` forms policy × account/geography/geocode rows, rejoins on `accgrpid`, uses policy-side geocode, and groups without `policyid`. | Exposure/geocode can be cross-multiplied; caps are not demonstrably once per contract. | Approve policy/geography/geocode grain and cardinality reconciliation, or a corrected query. |
| BSCR-003 | High | `is_nahu()` at `BSCR_UKEU.py:345-372` nests its state list under `state is None`; every non-null US state returns true. | All US exposure is currently NA hurricane rather than only listed states. | Approve all-US behaviour or authoritative state mapping. |
| BSCR-004 | High | `count_policies` is `pl.len()` (`:490-496`, `:534-540`); no policy ID is exported. Schedule X(f) requests contract counts, e.g. `E8`, `H8`, `K8`. | It is a contributing-row count, not a distinct contract count. | Define contract identifier/counting and provide a controlled source for X(f). |
| BSCR-005 | High | HIC X(b) has 39 `#REF!` formulas (`I33:I48`, `I51:I55`, `I58:I59`, `I62:I67`, `I70:I77`, `F67:G67`); X(f)`!D3` has cached `#VALUE!`; X(b) imports from a 2017 workbook and schedules link to 2024 material. | Final template contains broken/uncontrolled calculations and links. | Select current template; repair/replace or explicitly scope out every affected field. |
| BSCR-006 | Medium | The executable prints final diagnostics but not per-CTE counts or distinct policies/accounts (`BSCR_UKEU.py:278-315`), although the LLM gate needs them. | The policy-grain gate cannot be evidenced by the documented command. | Provide approved diagnostic SQL/instrumentation and acceptance checks. |
| BSCR-007 | Medium | `Sheet1` has no Excel table; its local pivot uses fixed `A1:K1048576`. | A table-resize instruction would create an uncontrolled workbook change. | Retain the actual fixed-range contract or approve a controlled table redesign. |

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

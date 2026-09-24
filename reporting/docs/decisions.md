# Production decisions and missing artifacts

[Start here](../README.md) · [Shared controls](operating-controls.md) ·
[Calculation discrepancy evidence](calculation-discrepancies.md)

## Status and responsibility

All entries below are **OPEN: resolution evidence is not supplied in this
repository**. This does not assert that approval cannot exist elsewhere. Before
execution, the return owner must identify the named accountable person and the
controlled evidence location in the run record. Roles below identify who needs
to supply a decision; they are not claimed assignments or approvals.

For each resolution, retain: decision ID, reporting period, named owner and
reviewer, selected rule/producer/template version, controlled artifact location,
approval reference/date, and reconciliation evidence. Mark an item resolved only
for that evidenced scope. A code change, matching schema, cached number, or
successful command alone does not close a decision. An out-of-scope decision
must name the affected fields and be approved; it must not silently narrow a return.

Use the discrepancy register for detailed observed defects and the process
handoff pages for traced workbook paths. This register tracks the required
answers, not a second calculation specification. Do not place credentials or
restricted extracts in these docs.

## COMMON-01

**Scope:** every controlled run. **Required role:** return owner, source-data
owner, and reviewer.

Supply the approved reporting date and database snapshot, server/driver and
certificate policy, peril/policy meanings, entities/portfolios, mapping versions,
retention factors, source currency, FX direction/date, output units, controlled
workbook versions, and independent reconciliation tolerances. Record exact
commands and immutable input/output locations. Name the controlled template and
sign-off/submission route if submission is in scope. Those locations and named
approvers are not currently supplied by the repository.

**Close with:** the completed pre-run record and approved reference pack required
by [operating controls](operating-controls.md), including baseline versus
current-period comparison rules. Historical January totals are not standing
acceptance targets for later periods.

## BSCR-01

**Scope:** policy grain, classifications, and diagnostics. **Required role:**
BSCR methodology owner and EDM/query owner. **Evidence:** BSCR-002, BSCR-003,
BSCR-004, BSCR-006, BSCR-011 and PRA-005/PRA-006 in the discrepancy register.

The geocoding join correction is numerically verified on the uploaded snapshot:
184 affected accounts explain the entire earthquake `ALL` reduction of
USD 4.813bn gross, USD 3.051bn net and 285 grouped rows. This part is no longer
an unexplained reconciliation difference. Policy-ID grouping has no material
effect on this snapshot; policy caps still apply by geography/geocode group.

The population workbook implements the agreed proxy: geocoded means
modellable/modelled/detailed; ungeocoded means not modellable/not modelled/data
deficient. It uses the existing grouped-row count. This is not a distinct-contract
definition or a reproduction of April's separate manual allocations.

Remaining decisions: approve cap allocation grain, all-US NAHU coverage, entity
null handling, distinct-contract identity, retention precision and reporting
acceptance. Current SQL matches policy type to each selected peril; wind feeds
NAHU/Europe/Japan typhoon and earthquake feeds `ALL` and earthquake regions.
The legacy query uses peril/policy type 1 throughout and is diagnostic only.

**Close with:** versioned query/mappings and diagnostic results on an approved
snapshot, plus the separately identified contract-count producer.

## BSCR-02

**Scope:** current SQL → Excel input table → five entity schedule tabs.
**Required role:** BSCR workbook owner. **Evidence:** the population workbook,
BSCR runbook, reconciliation workbook and BSCR-001/007/008/009/010.

`BSCR_Auto_Population.xlsx` has a `BSCRInput` Excel table containing all eight
SQL columns. Its entity schedules use direct formulas, with no intermediate
fixed key list or pivot. Monetary values arrive in USD and are divided by one
million only. Japanese earthquake and typhoon use their corresponding explicit
peril/region keys. There is no historical tab or legacy mode in this workbook.

The user procedure is two steps: clear old data rows while keeping the table
and headers, then paste current SQL results. Final work-laptop Excel testing,
controlled use and handling of unmapped entities remain to be signed off.
The fixed-range, reversed-Japan and repeated-FX findings apply to the older
`BSCR_Workings.xlsx`, which remains reference material, not the current route.

**Close with:** approved refreshed-output examples in Excel, complete entity
coverage, handling of blank/unknown entities and a controlled workbook version.

## BSCR-03

**Scope:** final Schedule X input mapping and supplemental sources. **Required
role:** BSCR return owner, modelling owner, and final-template reviewer.

An implemented field map now exists in `build_population_workbook.py`, with
630 automatic mappings checked against the supplied current output. It applies
the agreed geocoding proxy and historical all-other-lines exposure mapping.
The reconciliation workbook demonstrates the template/old-output/legacy/current
chain separately from the routine population workbook.

Provide remaining sources for EP/model losses, premiums, statutory
property-catastrophe inputs and narratives; blue fields are intentionally blank.
Confirm the controlled final return layout and decide whether grouped-row counts
are acceptable or need replacement with a distinct-contract source. Do not treat
the available exposure formulas as complete population of every Schedule X field.

**Close with:** an approved final-cell map and traceable sources for every
in-scope field, then a run-specific transfer/review log. Do not infer approval
from labels, colours or cached workbook values.

## BSCR-04

**Scope:** controlled HIC template. **Required role:** BSCR template owner.
**Evidence:** BSCR-005.

The top-level April templates supply the layout of the new population workbook;
their original cached errors/external links are not carried into the generated
file. The population workbook has no external workbook links or macros, but still
requires work-laptop Excel review and manual supplemental inputs. Select the
controlled final filing template and explicitly scope any unpopulated fields;
historical filenames and matching totals do not establish submission approval.

**Close with:** controlled template identity and a formula/link review showing
that every in-scope output and editable destination is usable.

## PRA-01

**Scope:** confirmed all-peril producer and database. **Required role:** PRA
return owner and EDM/query owner. **Evidence:** PRA-004.

Confirm the original Table3 population/producer or approve a replacement.
Python `1/1` is a regeneration candidate, not a proven all-peril definition;
legacy SQL `2/2` and database names are not interchangeable proof of scope.

**Close with:** exact source snapshot, query/parameters, population definition,
producer lineage, and independently reconciled raw/aggregate outputs. Same-
snapshot reproduction may use the January baseline; a new period needs its own
approved controls and movement explanation.

## PRA-02

**Scope:** pivot sources, currency, mappings and overlapping BSCR aids.
**Required role:** PRA workbook/methodology owner. **Evidence:** PRA-001,
PRA-002, PRA-003 and PRA-005 through PRA-008.

Approve repointing all earthquake pivots to Table32; choose `pml` versus
`Agg_USD` and the source/target currency and 1.25 basis. Resolve populated
PRA-region/CDS mapping errors, table boundaries and retention/geography
conflicts. The empty NA earthquake panel is not a usable output.

**Close with:** approved workbook changes/mappings and a recalculated example
reconciled from raw input through the selected pivot measure.

## PRA-03

**Scope:** final PRA template and cell map. **Required role:** PRA return owner.

The checked-in PRA workbook is a calculation workbook. Supply the controlled
final template and exact calculation-output-to-destination mapping, including
report section, measure, gross/net basis, currency, units and reporting date.

**Close with:** template/version/location, approved final-cell map and review
requirements; the final PRA submission template remains to be located.

## LLOYDS-01

**Scope:** branch producers, scale factors, proxy and source lineage. **Required
role:** Lloyd's return owner, exposure-data owner, and modelling/proxy owner.
**Evidence:** LLOYD-005 through LLOYD-008.

Select an approved producer for each RoW peril, South Africa EQ, California
wildfire and EU EQ/flood. The RoW SQL is only 3/3; no matching EU producer is
checked in. Supply missing county/CRESTA transformations, scale-factor sources,
query-grain controls, frozen FX and explicit portfolio/retention rules. Approve
any cross-peril or wildfire proxy. Identify the authoritative received workbook
and email and evidence each extract's lineage; matching headers are insufficient.

**Close with:** versioned commands/queries or transformations, source snapshots,
approved mappings/proxies and source-to-extract control totals for every branch.

## LLOYDS-02

**Scope:** report measures, currency/FX, geography and workbook maintenance.
**Required role:** Lloyd's methodology and workbook owners. **Evidence:**
LLOYD-001 through LLOYD-004, LLOYD-006, LLOYD-009 and LLOYD-010.

Choose RoW and South Africa gross/net/source-versus-USD measures; resolve the
South Africa FX currency-field mismatch and CRESTA derivation. Supply uniform EU
flood T/U formulas with an approved conversion direction/date. Resolve report
dates, unmatched geography eligibility, row/formula/pivot coverage and relevant
broken names/external links. Do not substitute the email GBP/EUR rate directly
for a USD/EUR cross-rate without proving the currency basis.

**Close with:** approved formula/mapping/rate versions and reconciliations of
included plus approved excluded/unmapped amounts to each core total.

## LLOYDS-03

**Scope:** final RDS template and transfer. **Required role:** Lloyd's return owner.

Supply the controlled final RDS template and report-range-to-final-cell map for
all four branches. The received S33 workbook is source evidence, not that final
template. Identify preparer/reviewer and controlled sign-off/submission route.

**Close with:** template identity/location, approved final-cell map, handoff
review procedure and required submission evidence.

## GLOBAL-01

**Scope:** Global Exposures production methodology and controls. **Required
role:** Global Exposures methodology, source-data and pipeline owners.
**Evidence:** GEX-001 through GEX-009.

Resolve policy-limit-as-factor and portfolio membership semantics; Fine Art
matching; PML validity and missing-data handling; geometry/coordinate
rejections; independent zero-impact evidence; complete output publication and
provenance. Provide the external pre/post-join controls currently required by
the runbook. Do not disable `fail_on_missing_pml` to bypass unknown loss.

**Close with:** approved methodology/producer and a reconciled CSV output pack
with manifest and event-level evidence. No final Excel cell map is applicable.

## DATAIKU-01

**Scope:** current provisional aggregation FX controls. **Required role:**
Dataiku query and source-data owners. **Evidence:** DATAIKU-007.

Approve a rate-positivity and null-GBP control that covers the current
`InvalidFXRowCount` blind spot. Zero exceptions do not prove complete conversion.

**Close with:** independently reconciled source/GBP totals and approved
exception treatment or corrected query controls. This does not approve Dataiku
as a replacement for the regulatory-return routes.

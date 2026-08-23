# Regulatory return data-flow map

## Data sources

- SQL Server EDM tables configured in [`bscr/BSCR_UKEU.py`](../../bscr/BSCR_UKEU.py), [`aggregates/aggs-from-edm.sql`](../../aggregates/aggs-from-edm.sql), and the checked-in supplementary SQL files.
- Received S33 exposure package: [`UKEU S33 Contingency/Supplementary Info UKEU S33.xlsx`](../../UKEU%20S33%20Contingency/Supplementary%20Info%20UKEU%20S33.xlsx) and its companion Outlook message.
- Checked-in calculation workbooks under [`bscr/`](../../bscr/), [`pra/`](../../pra/), and [`lloyds/`](../../lloyds/).
- Regulatory templates, instructions, mapping tables, FX rates, and scale factors embedded in those workbooks or held outside this repository.

This is the canonical end-to-end map of the repository's regulatory-return artefacts. It is based on static inspection of source code, SQL, workbook sheet manifests, formulas, cached values, and the S33 email text. No workbook was opened, recalculated, refreshed, or connected to a database during this review.

## Evidence labels

- **Direct**: a checked-in formula, query, relationship, or email instruction establishes the connection.
- **Structural match**: schemas and formulas line up, but the repository has no run record or checksum proving that the checked-in workbook was populated by that exact query run.
- **Manual handoff**: the destination has no formula link to the source; values must be copied or entered under review.
- **Unresolved**: the repository does not contain enough provenance to establish the step safely.

## Whole-process map

```mermaid
flowchart TD
    EDM[(SQL Server EDM)]
    S33[Received S33 workbook\nWeather / Quake / EU exposure]
    EMAIL[S33 instruction email]

    EDM -->|Direct query| BSCRPY[bscr/BSCR_UKEU.py]
    BSCRPY -->|CSV A:G| BSCRWORK[BSCR workings\nSheet1 -> output -> piv]
    BSCRWORK -->|Manual handoff| HIC[2026 HIC BSCR workbook\nSchedules X(a), X(b), X(c), X(f)]

    EDM -->|Aggregate SQL copied into workbook| PRA[PRA_BSCR_Aggs.xlsx]
    PRA -->|PRA pivots and BSCR calculation panels| PRAOUT[PRA return handoff / BSCR green cells]

    EMAIL --> S33
    S33 -->|Weather instructed| ROW[RoW workings]
    S33 -->|Weather instructed| CA[California wildfire workings]
    S33 -->|Quake instructed| ZA[South Africa earthquake workings]
    S33 -->|EU exposure instructed| EU[EU CRESTA workings]

    EDM -.->|Structural match: checked-in SQL extracts| ROW
    EDM -.->|Structural match: checked-in SQL extract| CA
    EDM -.->|Structural match: checked-in SQL extract| ZA

    ROW -->|Manual workbook/template handoff| LLOYDS[Lloyd's supplementary return]
    CA -->|Manual workbook/template handoff| LLOYDS
    ZA -->|Manual workbook/template handoff| LLOYDS
    EU -->|Manual workbook/template handoff| LLOYDS
```

The solid arrows are established by checked-in code, formulas, or the instruction email. Dotted arrows are reproducible-looking alternatives whose exact use for the current cached workbook values is not proven.

## Artefact inventory and ownership

| Artefact | Role | Input | Calculations or transformation | Output / consumer | Status |
|---|---|---|---|---|---|
| `bscr/BSCR_UKEU.py` | Executable BSCR extractor | Configured SQL Server `loc`, `policy`, `accgrp`, `loccvg` tables | PML allocation, policy-limit cap, entity and geography flags, QS/SRP retention, grouped gross/net totals | CSV for `Workings_with_geocodingFW - Including blanks USD.xlsx` | Active; assumptions below require review |
| `bscr/Workings_with_geocodingFW - Including blanks USD.xlsx` | BSCR calculation/pivot workbook | Script CSV pasted into `Sheet1` columns A:G | GBP-to-USD factor `1.35`, USD millions, entity/region/geocoding pivots | Regional values used in the HIC BSCR schedules | Active workings; manual handoff |
| `bscr/2026 BSCR - UKEU - HIC.xlsx` | HIC BSCR return workbook | Approved BSCR workings and template inputs | Schedule formulas and green input cells | Schedules X(a), X(b), X(c), X(f) | Current checked-in return workbook; not formula-linked to the workings file |
| `aggregates/aggs-from-edm.sql` | Aggregate SQL copied into PRA workbook | `HISCO_UKEU_01JAN26_010126_ROLLUP_ByLoB_GC_v25` | Location PML allocation and policy-limit cap; peril `2`, policy type `2` | `pra/PRA_BSCR_Aggs.xlsx` SQL/raw-data route | Direct logic match; population run not recorded |
| `pra/PRA_BSCR_Aggs.xlsx` | Combined PRA and BSCR workings | Aggregate query results plus embedded geography/class mappings | All-peril and earthquake pivots; PRA region/class assignment; BSCR earthquake splits and schedule calculation panels | PRA figures and BSCR green-cell handoff | Active calculation workbook; no final PRA template checked in |
| `pra/UKEU/PRA_BSCR_Aggs.xlsx` | Duplicate workbook copy | Same as above | Same as above | None distinct | Exact SHA-256 duplicate of `pra/PRA_BSCR_Aggs.xlsx`; do not edit both |
| `FA_California_Aggs.sql` | California extract | `KEEP_EDM`, peril/policy type `4`, California, portfolios `33` and `3624` | TSI, net TSI, GBP and USD conversions | California `Core data` sheet | Structural match |
| `lloyds/UKEU - Supplementary Info - RDL - Jan26 - Workings - California WF.xlsx` | California county workings | `Core data` plus county helper | `N = county text from E`; county report sums column M | Lloyd's section 5/6 handoff | Report banner says 01/01/2025 while query points to Jan-2026 EDM |
| `SouthAfrica_Aggs.sql` | South Africa extract | `KEEP_EDM`, peril/policy type `1`, South Africa, portfolios `33` and `3624` | Location TSI, account-level netting, GBP and USD conversions | South Africa `Core data` sheet | Structural match |
| `Supplementary Info - Workings - South Africa EQ - SQL.sql.txt` | Duplicate South Africa SQL | Same as above | Same as above | None distinct | Byte-for-byte duplicate of `SouthAfrica_Aggs.sql` |
| `lloyds/UKEU - Supplementary Info - Workings - South Africa EQ - Jan 2026.xlsx` | South Africa CRESTA workings | `Core data`, row scale factors, zone text, embedded FX/panel lookups | `scaled_tsi = factor * TSI`; two-digit zone helper; report `SUMIF` by zone | Lloyd's South Africa earthquake section | Report and FX tabs are dated 2024; current SQL points to Jan-2026 EDM |
| `Supplementary Info - Workings - ROW Aggs - SQL.sql` | RoW extract template | `KEEP_EDM`; currently hard-coded peril/policy type `3` | TSI and net TSI with GBP/USD conversions | RoW EQ/FR/FL/WS extract tabs | Only one of the four required peril runs is encoded |
| `lloyds/UKEU - Supplementary Info - RDL - Jan26 - Workings - ROW.xlsx` | Worldwide country/peril workings | Four extract tabs plus `UKEU Exposure scale factors` | Extract helper `M = I * L`; summary lookups by country and peril | Lloyd's global RoW aggregates | Jan-2026 banner; exact population lineage unresolved |
| `lloyds/UKEU - Supplementary Info - RDL - Jan26 - Workings - EU Cresta.xlsx` | EU earthquake/flood CRESTA workings | Separate EQ and FL core-data sheets, country/CRESTA maps, FX | Core amounts times row factors and `Fx!C7`; `SUMIFS` by CRESTA | Lloyd's Europe/Brussels section | No matching producer SQL checked in; report says 01/07/2024 |
| `UKEU S33 Contingency/Supplementary Info UKEU S33.xlsx` | Received S33 source package | Exposure-report output | `HIS net QS = Share Insured Value USD * (1 - RI Cession PC)`; separate Weather, Quake, and EU-exposure tabs | Instructed source for RoW, California, South Africa, EU, Canada/OFSI requests | Direct email provenance |
| `UKEU S33 Contingency/RE RDS Supplementary Information - UKEU 33.msg` | Source instruction and provenance | Email thread dated 22 Jan 2026 | Identifies which received tab to use and current Lloyd's FX rates | Controls interpretation of the S33 workbook | Retain with the received workbook |
| `globalexposures/exposures.py` | Separate event-footprint reporting CLI | `GlobalExposures` SQL tables `data.Events`, `data.ShapeFiles`, `data.PML` | Polygon construction, location intersection, PML/loss attribution | CSV output pack | Supporting analysis; not a direct producer of the return workbooks above |
| `main.py` | Repository entry-point pointer | None | Prints the documentation start path | Human operator | No regulatory calculations |
| `globalexposures/main.py` | Package entry-point pointer | None | Prints the `globalexposures/exposures.py --help` command | Human operator | No exposure calculations |

## BSCR calculation chain

### 1. EDM extraction

`bscr/BSCR_UKEU.py` reads one configured EDM and applies:

1. `loccvg` building, contents, business-interruption, and other limits are summed by `locid`.
2. Missing coverage limits fall back to `loc.tiv`; zero TIV produces zero PML.
3. Location PML is `account_pml * location_tiv / account_tiv`.
4. Location PML is zero where `locdetstatus = 15` or `locid = 0`.
5. Location PML is capped first by location deductible and then by policy limit.
6. Each row is classified into BSCR entity and one or more regional flags.
7. Retention is applied from the underwriting-reference suffix: `_QS` uses `0.50`; `_SRP` uses `0.3333`; all other rows retain `1.00`.
8. The script writes `cntrycode`, `bscr_entity`, `region`, `sum_pml`, `sum_net`, `count_policies`, and `is_geocoded`.

The `ALL` region is produced separately from region-specific rows. A row can appear in more than one regional bucket, so regional totals must not be summed as if mutually exclusive.

### 2. BSCR workings workbook

`Workings_with_geocodingFW - Including blanks USD.xlsx` contains:

| Sheet | Role |
|---|---|
| `Sheet1` | Script-shaped detail/aggregate input. Columns A:G match the current script CSV. Formula columns calculate USD and USD-millions values. |
| `output` | Consolidates values by entity, region, and geocoding status; formula columns again apply `1.35` and divide by `1,000,000`. |
| `piv` | Pivots `sum_pml_usd/1m` and `sum_net_usd/1m` by BSCR entity, region, and geocoding flags. |

The visible HIC regional pivot values correspond to the HIC Schedule X(c) regional rows in `2026 BSCR - UKEU - HIC.xlsx`, including Atlantic hurricane, North American earthquake, European windstorm, and Japanese earthquake. The final transfer is manual: the HIC workbook has no external formula relationship to the workings workbook.

### 3. Final HIC workbook

The checked-in HIC workbook contains **Schedules X(a), X(b), X(c), and X(f)**. It is not Schedule V. Green cells are the controlled handoff points for approved computed values; formulas and template-provided cells must not be replaced indiscriminately.

The workbook still contains external formula relationships to old files, including a 2025 HIC workbook, a blank 2026 HIG template, and a 2017 template. Schedule X(b) formulas reference an external `Import` sheet. Those links are stale dependencies until the return owner validates or removes them.

## PRA and combined BSCR workbook chain

`pra/PRA_BSCR_Aggs.xlsx` has seven sheets:

| Sheet | Observed role |
|---|---|
| `region_mappings` | Country/territory to Standard Formula and PRA region mapping. |
| `pivot_allperil` | 838-row aggregate table plus PRA class/geography formulas and all-peril pivots. |
| `pivot_eq` | Separate 838-row aggregate table with the same formula family and earthquake-labelled pivots. |
| `raw_data_for_bscr_splits_eq` | 270,675-row table of earthquake exposure rows, retention flags, and BSCR Schedule X(c) calculation panels. |
| `cds_mapping` | Portfolio/CDS class lookup. |
| `rms_geog` | RMS country and region lookup. |
| `sql` | Embedded aggregate query using peril `2` and policy type `2`; its logic matches `aggregates/aggs-from-edm.sql`. |

The two pivot input tables calculate:

- Fine-art classification from `uwritrname`.
- Country display from the country-code lookup.
- US, by-country, and by-state labels.
- PRA region from `region_mappings`.
- CDS class from `cds_mapping`.
- `Agg_USD = pml * 1.25`.

The raw BSCR-split table identifies HIG rows, `_SRP`, `_QS`, and North American hurricane/earthquake groups. Its formulas use `33%` for SRP and `50%` for QS, then feed calculation panels positioned to the right of the raw table. Those panels are the source-side calculations for BSCR green-cell entry; they are not a final PRA submission template.

`pra/UKEU/PRA_BSCR_Aggs.xlsx` is byte-identical to the root PRA workbook. Treat `pra/PRA_BSCR_Aggs.xlsx` as the canonical editable copy until the owner chooses whether to delete or archive the duplicate.

## Lloyd's supplementary chain

### Received instructions

The companion S33 email establishes these direct source instructions:

- RoW/global aggregates: use the `Weather` tab for worldwide events and proxy exposures.
- South Africa earthquake: use the `Quake` tab.
- California wildfire: use weather exposure, then review the numbers.
- Europe/Brussels earthquake and flood: use the isolated EU-exposure tab.
- Canada climate reporting: use `Weather`.
- OFSI Canada earthquake: included in `Quake`.
- 2026 Lloyd's FX rates: `1 GBP = 1.35 USD`, `1 GBP = 1.15 EUR`, `1 GBP = 1.84 CAD`.

The email also records that wildfire was not monitored separately and required a proxy/PML discussion. That is an unresolved business decision, not a calculation to infer in code or documentation.

### Working workbook mechanics

#### California wildfire

`FA_California_Aggs.sql` returns 13 columns ending in `TSI_USD_NET`. That schema fits the workbook's `Core data` through column M. The workbook parses county text into helper column N and sums column M by county into the report. This is a structural match, not proof that the cached core data came from the current SQL run.

#### South Africa earthquake

`SouthAfrica_Aggs.sql` and its `.sql.txt` duplicate return location/account exposure with CRESTA-zone text and currency-converted measures. The workbook adds a row factor, calculates `scaled_tsi`, derives a two-digit zone from the zone text, and sums scaled exposure by zone. The report banner and embedded FX table still show 2024 assumptions.

#### Rest of World

The workbook has separate EQ, FR, FL, and WS extract tabs plus a manually maintained scale-factor tab. Each extract calculates a scaled amount from the pasted data and factor; the report uses country/peril lookups. The checked-in SQL currently represents only one hard-coded peril/policy-type run (`3`), so it does not reproduce all four tabs without undocumented edits or additional queries.

#### EU CRESTA

The workbook has separate flood and earthquake core-data tabs, applies row factors and an embedded FX factor, and aggregates by mapped CRESTA. `Fx!C7` is `1.25 / 1.21 = 1.0330578512`, not the email's 2026 EUR rate of `1.15`. No checked-in SQL uniquely produces these two core-data tabs.

#### S33 contingency source workbook

The received workbook contains `Weather`, `Quake`, and `EU exposure - S33`. Its shared formula computes `HIS net QS` from share insured value and RI cession. It is source evidence, not a final Lloyd's template. Keep it and the message together.

## Known mismatches and unresolved controls

These are release blockers until a named return owner resolves them or records an approved exception:

1. **BSCR North American hurricane code defect.** `is_nahu()` currently returns true for every non-null US state because the state tests sit under `state is None`. The intended state lists therefore do not control US classification.
2. **BSCR geography divergence.** Script country/state lists differ from the workbook formulas, including Caribbean codes and US coastal states. No approved canonical mapping is recorded.
3. **Retention divergence.** The script uses `0.3333`, the PRA workbook uses `33%`, and checked-in SQL uses `0.33333` for `_SRP`. These produce different totals at scale.
4. **FX divergence.** BSCR workings use `1.35`; PRA pivot formulas use `1.25`; the South Africa workbook embeds 2024 FX; EU CRESTA uses `1.25/1.21`; the S33 email mandates 2026 rates of `1.35 USD`, `1.15 EUR`, and `1.84 CAD` per GBP.
5. **As-of-date divergence.** California says 01/01/2025, South Africa says 01/01/2024, and EU CRESTA says 01/07/2024, while their paths or checked-in SQL point to the Jan-2026 cycle.
6. **PRA pivot refresh risk.** The cached earthquake pivot view displays totals also seen in the all-peril view. Refresh state and source range must be confirmed before use.
7. **Missing PRA producer.** The embedded query is earthquake-specific; the repository does not contain the exact all-peril producer or a recorded population procedure for both 838-row pivot tables.
8. **Missing EU producer.** No checked-in SQL or script uniquely rebuilds the EU flood and earthquake core-data tabs.
9. **Incomplete RoW producer.** One hard-coded SQL peril cannot regenerate EQ, FR, FL, and WS tabs without undocumented parameter changes.
10. **Stale external links.** The HIC return workbook references older external templates, including 2025 and 2017 files.
11. **Manual green-cell handoff.** The workings and final return workbooks are not formula-linked. Every transferred value needs source cell/range, destination cell, unit, currency, as-of date, preparer, and reviewer evidence.
12. **Duplicate artefacts.** The PRA workbook exists twice identically, and the South Africa SQL exists twice identically. Duplicate copies are not separate controls or corroboration.
13. **Wildfire proxy decision.** The source email explicitly says wildfire is not monitored separately and the proxy/PML requires discussion. The repository records no approved decision.

## Controlled operating sequence

1. Freeze the EDM/database name, source workbook versions, mapping tables, rate set, and report as-of date.
2. Record which SQL/script version produced each pasted data tab and retain row counts and source totals.
3. Resolve the mismatches above before refreshing pivots or entering return values.
4. Populate only the designated raw/input areas; preserve workbook formulas, pivot definitions, validation, and template structure.
5. Refresh the intended pivots and record the exact source ranges.
6. Reconcile gross, net, row counts, currencies, and units at every boundary.
7. For each green cell, retain a handoff record: source artefact and cell/range, calculation, destination cell, value, unit, currency, as-of date, preparer, and reviewer.
8. Run formula, stale-link, date, FX, and duplicate checks before sign-off.
9. Keep final submissions separate from working files and preserve the approved evidence pack.

## Canonical documentation

- [BSCR process](bscr.md)
- [PRA process](pra.md)
- [Lloyd's supplementary process](lloyds-supplementary.md)
- [Controls](controls.md)
- [BSCR script runbook](../../bscr/bscr-runbook.md)
- [BSCR calculation guide](../../bscr/bscr_guide.md)

Historical and superseded notes are retained under [`docs/archive/`](../archive/) and must not be used as current operating instructions.

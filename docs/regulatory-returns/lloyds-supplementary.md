# Lloyd's supplementary information

## Data sources

- Received source workbook: [`UKEU S33 Contingency/Supplementary Info UKEU S33.xlsx`](../../UKEU%20S33%20Contingency/Supplementary%20Info%20UKEU%20S33.xlsx), with `Weather`, `Quake`, and `EU exposure - S33` tabs.
- Companion instruction/provenance email: `UKEU S33 Contingency/RE RDS Supplementary Information - UKEU 33.msg`.
- Checked-in SQL extracts: [`FA_California_Aggs.sql`](../../FA_California_Aggs.sql), [`SouthAfrica_Aggs.sql`](../../SouthAfrica_Aggs.sql), and [`Supplementary Info - Workings - ROW Aggs - SQL.sql`](../../Supplementary%20Info%20-%20Workings%20-%20ROW%20Aggs%20-%20SQL.sql).
- Calculation workbooks under [`lloyds/`](../../lloyds/).
- Lloyd's templates, guidance, and final approved submission held outside this repository.

See the [complete data-flow map](data-flow.md) for workbook mechanics, script/schema matches, and unresolved issues.

## Source instructions from the 2026 email

The email dated 22 January 2026 directs the process as follows:

| Return section | Instructed source |
|---|---|
| RoW/global country-peril aggregates | `Weather`; use proxy exposures where required |
| South Africa earthquake by CRESTA | `Quake` |
| California wildfire by county | Weather exposure, followed by review |
| Europe/Brussels earthquake and flood by CRESTA | `EU exposure - S33` |
| Canada climate reporting | `Weather` |
| OFSI Canada earthquake | `Quake` |

The same email sets 2026 Lloyd's rates to `1 GBP = 1.35 USD`, `1 GBP = 1.15 EUR`, and `1 GBP = 1.84 CAD`.

It also says wildfire is not monitored separately and the proxy/PML requires discussion. Do not silently choose a proxy or reuse another peril without owner approval.

## Workings map

### Rest of World

`lloyds/UKEU - Supplementary Info - RDL - Jan26 - Workings - ROW.xlsx` contains:

- report sheet `3. RoW Exposure Monitoring`;
- `UKEU Exposure scale factors`;
- separate `Extract - EQ`, `Extract - FR`, `Extract - FL`, and `Extract - WS` tabs;
- a checked-in SQL text tab.

Each extract calculates a scaled amount from pasted exposure and a row factor; the report retrieves the corresponding country/peril total. The repository SQL currently hard-codes peril/policy type `3`, so it cannot reproduce all four extract tabs without undocumented parameter changes or additional queries.

### South Africa earthquake

`lloyds/UKEU - Supplementary Info - Workings - South Africa EQ - Jan 2026.xlsx` contains the output sheet, `Core data`, SQL, portfolio lookup, and FX tabs. Core formulas multiply exposure by a row scale factor, derive a two-digit zone from CRESTA/zone text, and feed a report `SUMIF`.

`SouthAfrica_Aggs.sql` structurally fits the core sheet. `Supplementary Info - Workings - South Africa EQ - SQL.sql.txt` is a byte-for-byte duplicate of that SQL and is not independent corroboration.

### California wildfire

`lloyds/UKEU - Supplementary Info - RDL - Jan26 - Workings - California WF.xlsx` contains the county report and `Core data`. `FA_California_Aggs.sql` returns 13 columns ending in `TSI_USD_NET`, fitting core columns A:M. Helper column N extracts county text; the report sums column M by county.

This is a structural match only. The workbook has no run record proving that its cached data came from the current checked-in SQL execution.

### EU CRESTA

`lloyds/UKEU - Supplementary Info - RDL - Jan26 - Workings - EU Cresta.xlsx` contains:

- `11 LIC EU CRESTA` report;
- separate `Core data - FL` and `Core data - EQ` tabs;
- `Cresta to Country Mapping` and `EU Cresta Mapping`;
- `Fx`.

Core formulas apply row factors and `Fx!C7`, then the report aggregates by CRESTA. No matching SQL or Python producer for both core tabs is checked in.

### Received S33 workbook

`Supplementary Info UKEU S33.xlsx` is source evidence rather than a final return template. It contains event/location exposure on `Weather` and `Quake` plus an isolated EU view. Its shared formula calculates:

```text
HIS net QS = Share Insured Value USD * (1 - RI Cession PC)
```

Keep the workbook and companion message together to preserve provenance.

## Mandatory unresolved checks

- California's report says 01/01/2025 although its SQL names a Jan-2026 EDM.
- South Africa's report and FX table say 2024 although its SQL names a Jan-2026 EDM.
- EU CRESTA says 01/07/2024, and `Fx!C7` is `1.25 / 1.21 = 1.0330578512`, not the email's 2026 EUR rate `1.15`.
- Establish whether current core/extract tabs came from the received S33 workbook, a SQL run, or another source; schemas alone do not prove lineage.
- Record the exact peril-code runs and scale-factor derivation for every RoW tab.
- Resolve the wildfire proxy/PML decision with the owner.
- Confirm units, gross/net basis, currency, FX, as-of date, and portfolio scope before any template handoff.

## Controlled handoff

For every populated return value, record:

- source workbook/tab or SQL result;
- calculation workbook and source cell/range;
- mapping, scale-factor, and FX versions;
- destination template and green cell;
- value, unit, currency, and as-of date;
- preparer and reviewer.

Do not overwrite formulas, validation, template structure, or non-green cells unless a controlled template change is explicitly approved.

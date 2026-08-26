# Global Exposures — LLM calculation and validation contract

This describes observed `globalexposures/exposures.py` behaviour for review and
test design. It is **not** approval to operate the current pipeline in
production; see the blockers in [global-exposures.md](global-exposures.md).

## Current calculation path

```text
GroundUpTIV = SUM(loccvg.VALUEAMT) by location/currency/peril
PolicyFactor = MAX(CASE BLANLIMAMT WHEN 0 THEN 1 ELSE BLANLIMAMT END)
FineArtFactor = `PORTNUM` SQL-`LIKE` pattern factor
PolicyAdjustedTIV = GroundUpTIV * COALESCE(PolicyFactor, 1) * COALESCE(FineArtFactor, 1)
GroundUpLoss = GroundUpTIV * PML
GULoss = PolicyAdjustedTIV * PML
```

`BLANLIMAMT` is a named monetary-limit field and must not be assumed to be a
dimensionless factor. The policy result is account-level; `portacct` membership
is then joined to location rows and can multiply exposure. The exported
`edm_exposures.csv` is post-join, so it cannot be the sole duplicate control.

Fine Art patterns test `PORTNUM` (not `PORTNAME`) with SQL `LIKE`; an underscore
is a wildcard in the current patterns, not a literal underscore. The selected
peril filters both coverage peril and policy type.

## Spatial contract

- Polygon points are latitude/longitude and assumed WGS84; construct each
  polygon in DrawOrder.
- A point is impacted when it `intersects` the geometry: boundary points count.
- If several polygons intersect, current code retains one: highest PML, then
  lowest PolygonID. This is a selection rule, not an additive loss calculation.
- Invalid geometries may be repaired with `buffer(0)`; polygons with too few
  usable points can be dropped. Neither outcome is approval to continue.

## Hard stops for an autonomous agent

Stop and escalate if any condition below occurs; do not infer an override.

1. Missing, non-numeric, duplicate, out-of-range, or unmatched polygon/PML
   data; overlapping polygons without an owner-approved rule.
2. Empty EDM extract, dropped/null/out-of-range coordinates, no polygons, or no
   impacted locations without independently approved zero-impact evidence.
3. Multiple policy or portfolio memberships without an approved cardinality and
   allocation rule; missing policy factor; unapproved Fine Art pattern/factor.
4. Any use of `--allow-missing-pml`. Current grouped pandas sums can report
   missing loss as zero and a `Success` status.
5. Reused/nonempty output directory, partial event status, exit code other than
   zero, missing expected CSV, or an output lacking headers.

## Required evidence and checks

Before final use, produce independently preserved controls at these grains:

```text
location coverage before policy join
after policy join (account, policy count, factor)
after portfolio join (account, portfolio count)
valid / dropped coordinates and TIV
polygon/PML key match and geometry validation
event, account, location, currency, TIV, and loss totals
```

Require a run manifest containing resolved non-secret arguments, database
identity/time, code and lock revision, start/end times, status/exit code,
output checksums, and pre/post-join counts and totals. Publish only a complete
run-specific directory. An LLM must never describe status `No impacted
exposures` or `No polygons` as a complete result without that evidence.

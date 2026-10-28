# Error analysis: why the estimate misses, and what fixes it

Public data only. Run `uv run python -m aoi_budget.evaluate` to reproduce every number here.

## Summary

The error comes mainly from **inputs**, not the formula: two inputs a seller supplies (finish
level; seats instead of area for workstation orders) and two weaknesses in our test data (totals
that are partial or only a bound). With only **4 headline projects**, every percentage below is a
direction, not a measured accuracy.

| Variant | Headline n | Coverage | Median abs error | Median band width |
|---|---|---|---|---|
| published (band only) | 4 | 0% | 86% | 40% |
| adjusted (+ sourced factors) | 4 | 75% | 15% | 40% |
| informed (+ recorded finish) | 4 | 50% | 17% | 31% |

Gross and building-sf areas now convert to usable with a **sourced building-efficiency factor by
segment** (office 0.78, academic 0.63; UNM guidelines averaging SCUP data), declared before
scoring. Before it, informed was 75% / 14% and adjusted 75% / 20%. Effect: the office project
(Palmyra) went from +15% to +3% and now passes; academic buildings now run low (-16% to -32%)
because net assignable area excludes circulation that "usable" includes. The tool's users quote
offices, where the factor helps; the academic factor is labeled conservative.

Headline projects: UNL Mabel Lee (+12%), Palmyra admin (+15%, just outside), Chadron State Math
Science (+16%; a project the partner furnished, per its public case study), Wayne State Center
for Applied Technology (-6%). The last two come from Nebraska State College System capital
reports, which give net and gross square footage and a furnishings line.

## Input by input (one-at-a-time what-ifs)

| Input | Problem | Measured effect |
|---|---|---|
| **Finish level** | Public test projects were scored with "unknown" finish (the whole band). Competitive public bids buy value furniture. | Mabel Lee +24% → +12%; Palmyra +28% → +15% at the basic finish |
| **Seats → area** | Seat-only orders are converted at 200 usable sf/person and priced by $/sf. A workstation order concentrates cost in seats. | Manassas Park: -47% at 200 sf/person, +6% at 400 |
| **The test total itself** | Mabel Lee's award may be one of several packages; DSM Police's "40 workstations" is a minimum. | DSM: -26% at 40 seats, -8% at 50 |
| **Public contract price level** | Palmyra bought on a state cooperative contract, priced below the single public factor. | Palmyra still +15% after the finish fix |
| **Gross vs usable area** | Gross building area is converted with the rentable factor (0.87). NSCS buildings run 0.64-0.78 net/gross. | With 0.71: error 14% → 7%, but Wayne State flips to a fail. Not adopted: that factor came from two test buildings (leakage). Needs an independent published gross-to-usable factor. |

## Rules declared before scoring (no fitting to results)

- `finish` in `data/public/eval_projects.csv`: competitive public procurement (low bid, RFQ,
  state contract) is scored at **basic**; everything else stays **unknown**. Used only by the
  `informed` variant; `adjusted` is unchanged for comparison.
- `certainty`: `exact`, `uncertain`, `budget`, or `upper_bound`. An `upper_bound` total is scored
  as an envelope (estimate at or below it). Reuse-heavy projects stay floors.
- `procurement`: how it was bought (`rfq`, `low_bid`, `state_contract`, `contract`, `budget`).

## Still open

- **Academic gross-to-usable**: find a usable (not net assignable) efficiency for campus
  buildings; the current 0.63 undercounts.

- **Per-seat orders** (Manassas Park) need per-workstation pricing, not area. Planned as part of
  the bottom-up estimator (#14).
- **Palmyra** suggests public cooperative contracts need their own price level.
- **More headline projects** are the biggest lever: the local portal search
  (`docs/local-portal-search-guide.md`) and the partner's past projects with final totals.

# Error analysis: why the estimate misses, and what fixes it

Public data only. Run `uv run python -m aoi_budget.evaluate` to reproduce every number here.

## Summary

The error comes mainly from **inputs**, not the formula: two inputs a seller supplies (finish
level; seats instead of area for workstation orders) and two weaknesses in our test data (totals
that are partial or only a bound). With only **2 headline projects**, every percentage below is a
direction, not a measured accuracy.

| Variant | Headline n | Coverage | Median abs error | Median band width |
|---|---|---|---|---|
| published (band only) | 2 | 0% | 95% | 40% |
| adjusted (+ sourced factors) | 2 | 50% | 26% | 40% |
| **informed (+ recorded finish)** | 2 | 50% | **14%** | **22%** |

## Input by input (one-at-a-time what-ifs)

| Input | Problem | Measured effect |
|---|---|---|
| **Finish level** | Public test projects were scored with "unknown" finish (the whole band). Competitive public bids buy value furniture. | Mabel Lee +24% → +12%; Palmyra +28% → +15% at the basic finish |
| **Seats → area** | Seat-only orders are converted at 200 usable sf/person and priced by $/sf. A workstation order concentrates cost in seats. | Manassas Park: -47% at 200 sf/person, +6% at 400 |
| **The test total itself** | Mabel Lee's award may be one of several packages; DSM Police's "40 workstations" is a minimum. | DSM: -26% at 40 seats, -8% at 50 |
| **Public contract price level** | Palmyra bought on a state cooperative contract, priced below the single public factor. | Palmyra still +15% after the finish fix |
| Area basis | Not a cause: treating Palmyra's building area as usable made it worse. | +28% → +47% |

## Rules declared before scoring (no fitting to results)

- `finish` in `data/public/eval_projects.csv`: competitive public procurement (low bid, RFQ,
  state contract) is scored at **basic**; everything else stays **unknown**. Used only by the
  `informed` variant; `adjusted` is unchanged for comparison.
- `certainty`: `exact`, `uncertain`, `budget`, or `upper_bound`. An `upper_bound` total is scored
  as an envelope (estimate at or below it). Reuse-heavy projects stay floors.
- `procurement`: how it was bought (`rfq`, `low_bid`, `state_contract`, `contract`, `budget`).

## Still open

- **Per-seat orders** (Manassas Park) need per-workstation pricing, not area. Planned as part of
  the bottom-up estimator (#14).
- **Palmyra** suggests public cooperative contracts need their own price level.
- **More headline projects** are the biggest lever: the local portal search
  (`docs/local-portal-search-guide.md`) and the partner's past projects with final totals.

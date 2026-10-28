# Accuracy target, validation rules and stop rule

Written 2026-10-19, **before** the calibration numbers were run and before any partner totals for
the pre-registered projects are seen. Changes after that date go in a dated "Amendments" section.

## 1. What kind of estimate this is

The tool runs before any product is chosen, from square footage, headcount, space mix and finish
level. In AACE International's classification for building construction (Recommended Practice
56R-08, the building-sector companion to 18R-97), that is a **Class 5** estimate (project
definition about 0-2%), moving toward **Class 4** once a space program is entered. *Verify the
exact ranges against the RP text before quoting them externally.*

| Class | Typical accuracy range (low / high) |
|---|---|
| 5 | -20% to -30% / +30% to +50% |
| 4 | -10% to -20% / +20% to +30% |

**Target:** a Class 4 range at the inputs a seller has in the first conversation: the actual
furniture total falls inside the tool's range **about 80% of the time**, and the range is no
wider than about -20% / +30% around the midpoint.

## 2. Which error costs more

- **Under-quoting** (actual above the range) leads to sticker shock at the real quote and lost
  trust in the seller.
- **Over-quoting** (actual below the range) can lose the deal or shrink the client's scope.

Assumption until the partner says otherwise: under-quoting is costlier, so the range may be
**asymmetric, wider on the high side** (as the AACE ranges are). Report the share of projects
that land above the range ("under-quoted") separately.

## 3. How a range is scored

- **Coverage** of the stated range (target about 80%).
- **Interval score** for a central 80% range, relative to the actual: width plus 2/alpha (= 10)
  times any miss. Lower is better. This is the main score: it penalizes both vague and wrong.
- **Median absolute error** of the midpoint, for continuity with earlier reports.
- **Under-quoted share**, per section 2.
- With fewer than about 10 headline projects, every number is reported with n and treated as
  direction only. Conformal ranges with n < 10 are reported to show they are degenerate, not as
  a coverage claim.

## 4. Validation rules

1. **Leave-one-out** for anything learned from data (calibration, reference class, conformal).
2. **No parameter may come from a test project** (data leakage). A factor is adopted only from
   an independent source, and kept whatever its effect once declared.
3. **Pre-registration:** estimates for projects whose totals are not yet known are frozen in
   `data/public/preregistered_estimates.csv`, and the file's SHA-256 is recorded outside the
   repo with a timestamp, before any total is revealed. Partner-price (bottom-up) estimates are
   frozen the same way in a local, gitignored file; only their hash leaves the machine.
4. **Comparison rule for pre-registered projects:** estimates are in 2026 dollars, furniture
   product + freight/install excluded; a revealed total is converted to 2026 dollars with the
   office-furniture price index for its stated purchase year before scoring.
5. **Head-to-head (when available):** the tool, a partner estimator's own early budget, and a
   general-purpose chatbot are scored on the same specs with the same interval score.

## 5. Stop rule

Stop refining the model, and spend the time on data, when **both** hold on at least 10 headline
projects:

- coverage is within 10 points of 80% and the range is within the Class 4 band, **and**
- the median error is no larger than the **bid-tab noise floor**: the typical spread of
  competing bids on the same public specification (being measured from public bid tabulations).

Below that, an improvement that cannot be shown on new projects is not an improvement.

## Amendments

### 2026-10-19: noise floor measured

The bid-tab noise floor named in section 5 is now measured from public tabulations
(`data/public/bid_tabs.csv`, source-verified rows only; `aoi_budget.calibration.noise_floor`):

| Measure | Value |
|---|---|
| Tabulations / compliant bids | 19 / 73 (2016-2026; 13 Midwest in the full set) |
| Each bid vs the median of the other bids on the same spec (median absolute deviation) | **9.2%** |
| Winning (low) bid vs the tab median | **-7.8%** |

So, for section 5:

- **Noise floor = about 10%.** A median error near 10% on 10+ projects is as good as the market
  allows; stop refining the model there.
- Bids are right-skewed, which supports the asymmetric range in section 2.
- Awarded (low-bid) totals sit about 8% below a typical bid. Public award totals in the test set
  therefore read low against an estimate of the typical price; this is noted, not corrected for.

Caveats: only 7 tabs are classic office workstation bids; spread grows as specs allow
substitutes (single brand about 5%, "or equal" about 10-15%, catalog items much more); tabs give
spread, not $/sf (none state area). Cooperative-contract purchases produce no bid tab.

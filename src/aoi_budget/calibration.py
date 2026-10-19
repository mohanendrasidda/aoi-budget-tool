"""Is the RANGE honest? Interval scoring, a reference-class baseline and conformal ranges.

Run: uv run python -m aoi_budget.calibration

- Interval score (Winkler / Gneiting-Raftery) for a central (1 - alpha) range [l, u] and outcome y:
  (u - l) + (2 / alpha) * (l - y) if y < l, + (2 / alpha) * (y - u) if y > u. Lower is better. It
  rewards ranges that are both narrow and right. Reported relative to y so projects compare.
- Reference class (outside view): predict a project's $/usable sf from the median of the OTHER
  headline projects (leave-one-out), with their min..max as the range.
- Conformal (jackknife+ style, leave-one-out): take a method's midpoint and widen it by the
  quantiles of the log errors on the OTHER projects. With n < 10 the 80% range is degenerate
  (it becomes the min..max of n-1 errors); it is reported to show that, not to claim coverage.

Rules were declared in docs/accuracy-target.md before these numbers were run.
"""

from dataclasses import dataclass
from math import ceil, exp, log
from statistics import median

from aoi_budget.book import Book, load_book
from aoi_budget.estimator import GROSS_BASES, USABLE_BASES
from aoi_budget.evaluate import Scored, evaluate, load_projects

ALPHA = 0.2  # central 80% range


def interval_score(low: float, high: float, y: float, alpha: float = ALPHA) -> float:
    score = high - low
    if y < low:
        score += 2 / alpha * (low - y)
    if y > high:
        score += 2 / alpha * (y - high)
    return score


def relative_interval_score(s: Scored, alpha: float = ALPHA) -> float:
    return interval_score(s.low_psf, s.high_psf, s.actual_psf, alpha) / s.actual_psf


def _usable_share(s: Scored, book: Book) -> float:
    p = s.project
    if p.area_basis in GROSS_BASES and p.segment in book.gsf_to_usf:
        return book.gsf_to_usf[p.segment]
    return 1.0 if p.area_basis in USABLE_BASES else book.rsf_to_usf


def reference_class(headline: list[Scored], book: Book) -> list[Scored]:
    """Leave-one-out outside view on $/usable sf (price level ignored: years are close)."""
    usable_psf = {s.project.id: s.actual_psf / _usable_share(s, book) for s in headline}
    out = []
    for s in headline:
        others = [v for k, v in usable_psf.items() if k != s.project.id]
        if not others:
            continue
        share = _usable_share(s, book)
        out.append(
            Scored(
                s.project,
                "reference",
                s.area_sf,
                s.actual_psf,
                min(others) * share,
                max(others) * share,
            )
        )
    return out


def conformal(headline: list[Scored], alpha: float = ALPHA) -> list[Scored]:
    """Leave-one-out conformal range around each method's midpoint, on log errors."""
    out = []
    errors = {s.project.id: log(s.actual_psf / s.mid_psf) for s in headline}
    for s in headline:
        others = sorted(v for k, v in errors.items() if k != s.project.id)
        n = len(others)
        if n < 2:
            continue
        k_lo = max(0, ceil(n * alpha / 2) - 1)
        k_hi = min(n - 1, n - ceil(n * alpha / 2))
        out.append(
            Scored(
                s.project,
                f"conformal({s.variant})",
                s.area_sf,
                s.actual_psf,
                s.mid_psf * exp(others[k_lo]),
                s.mid_psf * exp(others[k_hi]),
            )
        )
    return out


@dataclass(frozen=True)
class Calibration:
    variant: str
    n: int
    coverage_pct: float
    median_abs_error_pct: float
    mean_rel_interval_score: float
    under_pct: float  # share of projects where the actual is ABOVE the range (we under-quoted)


def calibrate(scored: list[Scored]) -> list[Calibration]:
    out = []
    for v in dict.fromkeys(s.variant for s in scored):
        rows = [s for s in scored if s.variant == v]
        out.append(
            Calibration(
                v,
                len(rows),
                100 * sum(s.inside for s in rows) / len(rows),
                median(abs(s.error_pct) for s in rows),
                sum(relative_interval_score(s) for s in rows) / len(rows),
                100 * sum(s.actual_psf > s.high_psf for s in rows) / len(rows),
            )
        )
    return out


def run(book: Book | None = None) -> list[Calibration]:
    book = book or load_book()
    scored = [s for s in evaluate(load_projects(), book) if s.project.role == "headline"]
    base = [s for s in scored if s.variant in ("adjusted", "informed")]
    adjusted = [s for s in scored if s.variant == "adjusted"]
    extra = reference_class(adjusted, book) + conformal(adjusted)
    extra += conformal([s for s in scored if s.variant == "informed"])
    return calibrate(base + extra)


def main() -> None:
    print("| Variant | n | Coverage | Median abs error | Rel. interval score | Under-quoted |")
    print("|---|---|---|---|---|---|")
    for c in run():
        print(
            f"| {c.variant} | {c.n} | {c.coverage_pct:.0f}% | {c.median_abs_error_pct:.0f}% "
            f"| {c.mean_rel_interval_score:.2f} | {c.under_pct:.0f}% |"
        )


if __name__ == "__main__":
    main()


def noise_floor(path=None) -> dict[str, float]:
    """Market spread on identical specs: each compliant bid vs the median of the OTHER bids on
    the same public tabulation (data/public/bid_tabs.csv). No estimator can beat this on
    average, so it is the stop line in docs/accuracy-target.md."""
    import csv

    from aoi_budget.book import DATA_DIR

    path = path or DATA_DIR / "bid_tabs.csv"
    tabs: dict[str, list[float]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["compliant"] == "1":
                tabs.setdefault(r["tab_id"], []).append(float(r["total_usd"]))
    tabs = {k: v for k, v in tabs.items() if len(v) >= 2}
    loo, low = [], []
    for bids in tabs.values():
        low.append(min(bids) / median(bids) - 1)
        for i, b in enumerate(bids):
            loo.append(abs(b / median(bids[:i] + bids[i + 1 :]) - 1))
    return {
        "tabs": len(tabs),
        "bids": sum(len(v) for v in tabs.values()),
        "loo_median_abs_dev_pct": 100 * median(loo),
        "low_bid_vs_median_pct": 100 * median(low),
    }

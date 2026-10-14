"""One-at-a-time sensitivity (#14): which assumption moves the estimate most.

Each swing changes one input (or one book value) to a plausible low and high, keeps everything
else at the baseline, and records the estimate midpoint. Sorted widest first, this is a tornado.
"""

from collections.abc import Callable
from dataclasses import dataclass, replace

from aoi_budget.book import Book
from aoi_budget.estimator import Inputs, estimate


@dataclass(frozen=True)
class Swing:
    name: str
    low_label: str
    high_label: str
    low_total: float
    high_total: float

    @property
    def spread(self) -> float:
        return abs(self.high_total - self.low_total)


Change = Callable[[Inputs, Book], tuple[Inputs, Book]]


def _inputs(**changes) -> Change:
    return lambda i, b: (replace(i, **changes), b)


def _book(**changes) -> Change:
    return lambda i, b: (i, replace(b, **changes))


def _swings(base: Inputs, book: Book) -> list[tuple[str, str, Change, str, Change]]:
    next_year = str(max(int(p) for p in book.ppi if len(p) == 4) + 1)
    taxed = base.tax_scope or max(book.tax_pct, key=book.tax_pct.get)
    return [
        ("Finish level", "basic", _inputs(finish="basic"), "premium", _inputs(finish="premium")),
        (
            "Buyer pricing",
            "public / co-op",
            _inputs(buyer="public"),
            "commercial",
            _inputs(buyer="commercial"),
        ),
        (
            "Area measured as",
            "gross / rentable",
            _inputs(area_basis="RSF"),
            "usable",
            _inputs(area_basis="USF"),
        ),
        (
            "Market band",
            "US Tier 3",
            _inputs(tier="US Tier 3"),
            "US Tier 2",
            _inputs(tier="US Tier 2"),
        ),
        (
            "Freight, install, handling",
            "excluded",
            _inputs(include_adders=False),
            "included",
            _inputs(include_adders=True),
        ),
        (
            "Sales tax",
            "exempt",
            _inputs(tax_scope=None),
            taxed,
            _inputs(tax_scope=taxed),
        ),
        (
            "Purchase year",
            "now",
            _inputs(period=max(p for p in book.ppi if len(p) == 4)),
            next_year,
            _inputs(period=next_year),
        ),
        (
            "Public discount gap",
            "small (0.85)",
            _book(public_price_factor=0.85),
            "large (0.65)",
            _book(public_price_factor=0.65),
        ),
    ]


def tornado(base: Inputs, book: Book) -> tuple[float, list[Swing]]:
    """Return the baseline midpoint and the swings, widest first.

    Swings that cannot move this baseline (e.g. the public discount gap for a commercial buyer)
    are left out.
    """
    out = []
    for name, lo_label, lo_change, hi_label, hi_change in _swings(base, book):
        lo = estimate(*lo_change(base, book)).mid
        hi = estimate(*hi_change(base, book)).mid
        if lo != hi:
            out.append(Swing(name, lo_label, hi_label, lo, hi))
    out.sort(key=lambda s: s.spread, reverse=True)
    return estimate(base, book).mid, out

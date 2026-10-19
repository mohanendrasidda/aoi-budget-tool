"""Bottom-up price layer from AOI price books (#19). Feeds the bottom-up estimator (#14).

Run (needs the local, gitignored AOI file; prints a comparison against public projects):
    uv run python -m aoi_budget.price_layer

Method: space program counts x a kit per space type x representative list prices (by finish
tier) x an options uplift, then a discount picked by project size (AOI uses tiered discounts by
project size), then the same price-level, add-on and tax factors as the benchmark estimator.

AOI values live only in data/raw/aoi-derived/price_layer/items.csv (gitignored, ADR 0004).
This file holds code and labeled assumptions, never AOI prices.
"""

import csv
from dataclasses import dataclass
from math import inf
from pathlib import Path

from aoi_budget.book import DATA_DIR, Book, load_book
from aoi_budget.estimator import Inputs, factors_for, price_index
from aoi_budget.seller import Program, default_headcount, space_program

ITEMS_PATH = DATA_DIR.parent / "raw" / "aoi-derived" / "price_layer" / "items.csv"
PRICE_BOOK_PERIOD = "2026"  # books effective April 2026
TIERS = ("good", "better", "best")
FINISH_TIER = {"basic": "good", "standard": "better", "premium": "best", "unknown": "better"}

# Assumptions (labeled in the UI) until AOI confirms its own kits and discount tiers.
KITS = {
    # Typical L-shaped open-plan workstation: main surface + return, 3 screens/panels.
    "workstation": {"desk": 2, "screen": 3, "pedestal": 1, "task_chair": 1},
    "private_office": {
        "desk": 2,
        "pedestal": 1,
        "lateral_file": 1,
        "task_chair": 1,
        "guest_chair": 2,
    },
    "conference_room": {"conference_table": 1, "task_chair": 8},
    "huddle_room": {"huddle_table": 1, "guest_chair": 4},
}
OPTIONS_UPLIFT = {"task_chair": (1.20, 1.40)}  # arms, adjustments, casters over base config
DEFAULT_UPLIFT = (1.05, 1.15)  # finish and fabric price categories
ANCILLARY_PCT = 10.0  # lounge, cafe, accessories not in the kits
# (list total up to, discount low, discount high): bigger projects get deeper discounts.
DISCOUNT_TIERS = (
    (100_000, 0.50, 0.58),
    (500_000, 0.56, 0.64),
    (1_500_000, 0.60, 0.68),
    (inf, 0.63, 0.72),
)


@dataclass(frozen=True)
class PriceLayer:
    prices: dict[tuple[str, str], float]  # (category, tier) -> list price
    sources: dict[tuple[str, str], str]


def load_price_layer(path: Path = ITEMS_PATH) -> PriceLayer | None:
    """None when the AOI file is absent, so the app still runs on public data alone."""
    if not path.exists():
        return None
    rows: dict[tuple[str, str], list[tuple[float, str]]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            src = f"{r['book']} p.{r['page']}: {r['product']}"
            rows.setdefault((r["category"], r["tier"]), []).append((float(r["list_usd"]), src))
    prices, sources = {}, {}
    for key, vals in rows.items():
        prices[key] = sum(v for v, _ in vals) / len(vals)
        sources[key] = "; ".join(s for _, s in vals)
    for cat in {c for c, _ in rows}:  # fill a missing "better" with the good/best midpoint
        if (cat, "better") not in prices and {(cat, "good"), (cat, "best")} <= prices.keys():
            prices[(cat, "better")] = (prices[(cat, "good")] + prices[(cat, "best")]) / 2
            sources[(cat, "better")] = "midpoint of good and best"
    return PriceLayer(prices, sources)


@dataclass(frozen=True)
class Line:
    category: str
    count: int
    unit_list: float
    source: str


@dataclass(frozen=True)
class BottomUp:
    lines: tuple[Line, ...]
    list_low: float
    list_high: float
    discount: tuple[float, float]
    multiplier: float  # price level x adders x tax x reuse, from the benchmark estimator
    area_sf: float

    @property
    def low(self) -> float:
        return self.list_low * (1 - self.discount[1]) * self.multiplier

    @property
    def high(self) -> float:
        return self.list_high * (1 - self.discount[0]) * self.multiplier

    @property
    def psf_low(self) -> float:
        return self.low / self.area_sf

    @property
    def psf_high(self) -> float:
        return self.high / self.area_sf


def counts(program: Program) -> dict[str, int]:
    out: dict[str, int] = {}
    for space, n in (
        ("workstation", program.workstations),
        ("private_office", program.private_offices),
        ("conference_room", program.conference_rooms),
        ("huddle_room", program.huddle_rooms),
    ):
        for cat, k in KITS[space].items():
            out[cat] = out.get(cat, 0) + k * n
    return {c: n for c, n in out.items() if n}


def discount_for(list_total: float) -> tuple[float, float]:
    for upto, lo, hi in DISCOUNT_TIERS:
        if list_total <= upto:
            return lo, hi
    raise AssertionError("unreachable")


def bottom_up(program: Program, inputs: Inputs, layer: PriceLayer, book: Book) -> BottomUp:
    tier = FINISH_TIER[inputs.finish]
    lines, lo, hi = [], 0.0, 0.0
    for cat, n in counts(program).items():
        unit = layer.prices[(cat, tier)]
        up_lo, up_hi = OPTIONS_UPLIFT.get(cat, DEFAULT_UPLIFT)
        lo += n * unit * up_lo
        hi += n * unit * up_hi
        lines.append(Line(cat, n, unit, layer.sources[(cat, tier)]))
    anc = 1 + ANCILLARY_PCT / 100
    lo, hi = lo * anc, hi * anc
    # Same sourced factors as the benchmark, except the ones that do not apply to list prices:
    # the band's price level (replaced by the books' own date), area basis and public factor.
    skip = {"Price level", "Area basis", "Public / co-op pricing"}
    m = price_index(book, inputs.period) / price_index(book, PRICE_BOOK_PERIOD)
    for f in factors_for(inputs, book):
        if f.name not in skip:
            m *= f.multiplier
    return BottomUp(tuple(lines), lo, hi, discount_for((lo + hi) / 2), m, inputs.area_sf)


def program_for(area_sf: float | None, seats: int | None, book: Book) -> tuple[Program, float]:
    """Seat-only orders are workstations only; area-only projects get the default program."""
    if area_sf is None:
        return Program(seats, 0, 0, 0), seats * book.usf_per_person
    heads = default_headcount(area_sf, book.usf_per_person)
    return space_program(heads, "Balanced"), area_sf


def score(layer: PriceLayer, book: Book) -> list:
    """Bottom-up as an evaluation variant, scored with the same role rules as evaluate.py."""
    from aoi_budget.evaluate import Scored, load_projects

    out = []
    for p in load_projects():
        program, area = program_for(p.area_sf, p.seats, book)
        inputs = Inputs(area_sf=area, finish="unknown", buyer=p.buyer, period=p.year)
        bu = bottom_up(program, inputs, layer, book)
        out.append(Scored(p, "bottom_up", area, p.actual_usd / area, bu.psf_low, bu.psf_high))
    return out


def main() -> None:
    from aoi_budget.evaluate import evaluate, load_projects, report, summarize

    layer, book = load_price_layer(), load_book()
    if layer is None:
        print(f"No AOI price layer at {ITEMS_PATH}; nothing to compare.")
        return
    scored = evaluate(load_projects(), book) + score(layer, book)
    print(report([s for s in scored if s.variant in ("adjusted", "bottom_up")]))
    print()
    for s in summarize(scored):
        print(s)


if __name__ == "__main__":
    main()

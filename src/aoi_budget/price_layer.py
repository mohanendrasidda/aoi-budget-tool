"""Bottom-up price layer from AOI price books (#19). Feeds the bottom-up estimator (#14).

Run (needs the local, gitignored AOI file; prints a comparison against public projects):
    uv run python -m aoi_budget.price_layer

Method: space program counts x a kit per space type x representative list prices (by finish
tier) x an options uplift, then a discount off list BY PRODUCT CATEGORY (category moves the
discount ~45 points, order size ~1-3), then public -> commercial, then the same price-level,
add-on and tax factors as the benchmark estimator.

AOI values live only in data/raw/aoi-derived/price_layer/items.csv (gitignored, ADR 0004).
This file holds code and labeled assumptions, never AOI prices.
"""

import csv
from dataclasses import dataclass
from pathlib import Path

from aoi_budget.book import DATA_DIR, Book, load_book
from aoi_budget.estimator import GROSS_BASES, USABLE_BASES, Inputs, factors_for, price_index
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
# Public cooperative-contract discount off list, by category, for order tiers <= $50K,
# <= $150K and above: MillerKnoll NASPO ValuePoint MA3967, Amendment 2 (2024), lines matching
# the representative products. Transcribed in research notes; the PDF host's robots.txt blocks
# automated download, so a person must verify it in a browser (UNVERIFIED until then).
CATEGORY_DISCOUNT = {
    "task_chair": (0.5050, 0.5075, 0.5175),  # Sayl/Verus/Cosm lines
    "guest_chair": (0.5075, 0.5100, 0.5175),
    "screen": (0.5050, 0.5075, 0.5250),  # Layout Studio
    "desk": (0.6650, 0.6675, 0.6850),  # Everywhere tables
    "conference_table": (0.6650, 0.6675, 0.6850),
    "huddle_table": (0.6650, 0.6675, 0.6850),
    "pedestal": (0.6450, 0.6475, 0.6650),  # Tu
    "lateral_file": (0.6450, 0.6475, 0.6650),
}
ORDER_TIERS = (50_000, 150_000)  # list-price order size limits for the first two tiers
DISCOUNT_SPREAD = 0.02  # +/- negotiation around the contract discount (assumption)


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
    net_low: float  # after category discount and buyer type, before the multiplier
    net_high: float
    order_tier: int
    multiplier: float  # price level x adders x tax x reuse, from the benchmark estimator
    area_sf: float

    @property
    def low(self) -> float:
        return self.net_low * self.multiplier

    @property
    def high(self) -> float:
        return self.net_high * self.multiplier

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


def order_tier(list_total: float) -> int:
    return sum(list_total > limit for limit in ORDER_TIERS)


def bottom_up(program: Program, inputs: Inputs, layer: PriceLayer, book: Book) -> BottomUp:
    tier = FINISH_TIER[inputs.finish]
    lines, per_cat = [], {}
    for cat, n in counts(program).items():
        unit = layer.prices[(cat, tier)]
        up_lo, up_hi = OPTIONS_UPLIFT.get(cat, DEFAULT_UPLIFT)
        per_cat[cat] = (n * unit * up_lo, n * unit * up_hi)
        lines.append(Line(cat, n, unit, layer.sources[(cat, tier)]))
    anc = 1 + ANCILLARY_PCT / 100
    lo = sum(a for a, _ in per_cat.values()) * anc
    hi = sum(b for _, b in per_cat.values()) * anc
    t = order_tier((lo + hi) / 2)
    net_lo = sum(
        a * (1 - CATEGORY_DISCOUNT[c][t] - DISCOUNT_SPREAD) for c, (a, _) in per_cat.items()
    )
    net_hi = sum(
        b * (1 - CATEGORY_DISCOUNT[c][t] + DISCOUNT_SPREAD) for c, (_, b) in per_cat.items()
    )
    buyer = 1.0 if inputs.buyer == "public" else 1 / book.public_price_factor
    net_lo, net_hi = net_lo * anc * buyer, net_hi * anc * buyer
    # Same sourced factors as the benchmark, except the ones that do not apply to list prices:
    # the band's price level (replaced by the books' own date), area basis and public factor.
    skip = {"Price level", "Area basis", "Public / co-op pricing"}
    m = price_index(book, inputs.period) / price_index(book, PRICE_BOOK_PERIOD)
    for f in factors_for(inputs, book):
        if f.name not in skip:
            m *= f.multiplier
    return BottomUp(tuple(lines), lo, hi, net_lo, net_hi, t, m, inputs.area_sf)


def usable_area(area_sf: float, area_basis: str, segment: str, book: Book) -> float:
    """Usable sf that people sit in: same conversions as the benchmark's area factor."""
    if area_basis in GROSS_BASES and segment in book.gsf_to_usf:
        return area_sf * book.gsf_to_usf[segment]
    if area_basis in USABLE_BASES:
        return area_sf
    return area_sf * book.rsf_to_usf


def program_for(
    area_sf: float | None,
    seats: int | None,
    book: Book,
    area_basis: str = "USF",
    segment: str = "office",
) -> tuple[Program, float]:
    """Seat-only orders are workstations only; area projects get the default program sized
    from USABLE area (gross area would furnish corridors and mechanical rooms)."""
    if area_sf is None:
        return Program(seats, 0, 0, 0), seats * book.usf_per_person
    heads = default_headcount(usable_area(area_sf, area_basis, segment, book), book.usf_per_person)
    return space_program(heads, "Balanced"), area_sf


def score(layer: PriceLayer, book: Book) -> list:
    """Bottom-up as an evaluation variant, scored with the same role rules as evaluate.py."""
    from aoi_budget.evaluate import Scored, load_projects

    out = []
    for p in load_projects():
        program, area = program_for(p.area_sf, p.seats, book, p.area_basis, p.segment)
        inputs = Inputs(area_sf=area, finish=p.finish, buyer=p.buyer, period=p.year)
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

"""v0 benchmark estimator (#10): area x published $/sf band x named, sourced multipliers.

Pricing math is deterministic code. Every multiplier is returned as a Factor with its source, so
the UI can show the seller exactly where each part of the range came from.
"""

from dataclasses import dataclass
from math import prod

from aoi_budget.book import BAND_BASE_PERIOD, DEFAULT_TIER, Book

# Share of the published band each finish level uses (0 = band low, 1 = band high).
FINISH_POSITION = {
    "unknown": (0.0, 1.0),
    "basic": (0.0, 0.5),
    "standard": (0.25, 0.75),
    "premium": (0.5, 1.0),
}
USABLE_BASES = {"USF", "NSF"}
AREA_BASES = USABLE_BASES | {"RSF", "GSF", "building_sf"}
BUYERS = {"commercial", "public"}


@dataclass(frozen=True)
class Inputs:
    area_sf: float
    area_basis: str = "USF"
    finish: str = "standard"
    buyer: str = "commercial"
    period: str = "2026"  # price index period of the purchase: "2022", "2025-12", "2027"
    tier: str = DEFAULT_TIER
    include_adders: bool = False
    tax_scope: str | None = None  # a sales_tax_pct scope, or None for tax-exempt
    reuse_pct: float = 0.0  # share of furniture cost avoided by reusing existing pieces

    def __post_init__(self) -> None:
        if not self.area_sf > 0:
            raise ValueError("area_sf must be positive")
        if self.area_basis not in AREA_BASES:
            raise ValueError(f"area_basis must be one of {sorted(AREA_BASES)}")
        if self.finish not in FINISH_POSITION:
            raise ValueError(f"finish must be one of {sorted(FINISH_POSITION)}")
        if self.buyer not in BUYERS:
            raise ValueError(f"buyer must be one of {sorted(BUYERS)}")
        if not 0 <= self.reuse_pct < 100:
            raise ValueError("reuse_pct must be from 0 to under 100")


@dataclass(frozen=True)
class Factor:
    name: str
    multiplier: float
    source_id: str
    note: str


@dataclass(frozen=True)
class Estimate:
    area_sf: float
    psf_low: float  # after all factors
    psf_high: float
    factors: tuple[Factor, ...]

    @property
    def low(self) -> float:
        return self.psf_low * self.area_sf

    @property
    def high(self) -> float:
        return self.psf_high * self.area_sf

    @property
    def mid(self) -> float:
        return (self.low + self.high) / 2


def price_index(book: Book, period: str) -> float:
    """Index for a period; years past the data are projected at the book's escalation rate."""
    if period in book.ppi:
        return book.ppi[period]
    latest_year = max(int(p) for p in book.ppi if len(p) == 4)
    year = int(period[:4])
    if year <= latest_year:
        raise ValueError(f"no price index for period {period!r}")
    return book.ppi[str(latest_year)] * (1 + book.escalation_pct / 100) ** (year - latest_year)


def factors_for(inputs: Inputs, book: Book) -> tuple[Factor, ...]:
    s = book.sources
    esc = price_index(book, inputs.period) / book.ppi[BAND_BASE_PERIOD]
    out = [
        Factor(
            "Price level",
            esc,
            s["escalation"],
            f"office furniture price index {inputs.period} vs {BAND_BASE_PERIOD}",
        )
    ]
    if inputs.buyer == "public":
        out.append(
            Factor(
                "Public / co-op pricing",
                book.public_price_factor,
                s["public_price_factor"],
                "government vs commercial discount, same manufacturer",
            )
        )
    if inputs.area_basis not in USABLE_BASES:
        out.append(
            Factor(
                "Area basis",
                book.rsf_to_usf,
                s["area_basis"],
                f"{inputs.area_basis} treated as rentable: 200 usable / 230 rentable",
            )
        )
    if inputs.reuse_pct:
        out.append(
            Factor(
                "Reused furniture",
                1 - inputs.reuse_pct / 100,
                "seller input",
                f"{inputs.reuse_pct:g}% of furniture cost avoided (reused pieces assumed to match)",
            )
        )
    if inputs.include_adders:
        out.append(
            Factor(
                "Freight, install, handling",
                1 + book.adders_pct / 100,
                s["adders"],
                f"{book.adders_pct:g}% of furniture net",
            )
        )
    if inputs.tax_scope:
        rate = book.tax_pct[inputs.tax_scope]
        out.append(Factor("Sales tax", 1 + rate / 100, s["tax"], f"{inputs.tax_scope} {rate:g}%"))
    return tuple(out)


def estimate(inputs: Inputs, book: Book) -> Estimate:
    band_low, band_high = book.bands[inputs.tier]
    lo_pos, hi_pos = FINISH_POSITION[inputs.finish]
    width = band_high - band_low
    factors = factors_for(inputs, book)
    m = prod(f.multiplier for f in factors)
    return Estimate(
        area_sf=inputs.area_sf,
        psf_low=(band_low + width * lo_pos) * m,
        psf_high=(band_low + width * hi_pos) * m,
        factors=factors,
    )

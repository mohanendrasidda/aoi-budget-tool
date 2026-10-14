"""Assumption book: every number the estimator uses, loaded from data/public with its source.

Nothing here is tuned to the evaluation projects. Each value is read from a sourced row, so a
reviewer can trace any multiplier back to a URL in benchmarks.csv or ppi_office_furniture.csv.
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "public"

# C&W 2026 guide prices are "as of December 2025".
BAND_BASE_PERIOD = "2025-12"
DEFAULT_TIER = "US Tier 3"

# (government row, commercial row) from the same manufacturer and document.
PUBLIC_VS_COMMERCIAL_PAIRS = [
    ("Systems, manufacturer GSA (same disclosure)", "Systems, manufacturer commercial disclosure"),
    ("Seating, manufacturer GSA (same disclosure)", "Seating, manufacturer commercial disclosure"),
]


@dataclass(frozen=True)
class Book:
    bands: dict[str, tuple[float, float]]  # tier -> ($/sf low, $/sf high) at BAND_BASE_PERIOD
    ppi: dict[str, float]  # period ("2022", "2025-12") -> index
    escalation_pct: float  # per year, for periods past the latest index
    public_price_factor: float  # public/co-op price paid / commercial price paid
    rsf_to_usf: float
    adders_pct: float  # freight + install + handling, percent of furniture net
    tax_pct: dict[str, float]  # scope -> percent
    usf_per_person: float
    sources: dict[str, str]  # assumption name -> source_id


def _read(name: str, data_dir: Path) -> list[dict[str, str]]:
    with (data_dir / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _one(rows: list[dict[str, str]], metric: str, scope: str | None = None) -> dict[str, str]:
    hits = [r for r in rows if r["metric"] == metric and (scope is None or r["scope"] == scope)]
    if len(hits) != 1:
        raise ValueError(f"expected one {metric!r} row for scope {scope!r}, found {len(hits)}")
    return hits[0]


def _mid(row: dict[str, str]) -> float:
    if row["value"]:
        return float(row["value"])
    return (float(row["low"]) + float(row["high"])) / 2


def load_book(data_dir: Path = DATA_DIR) -> Book:
    rows = _read("benchmarks.csv", data_dir)

    bands = {}
    for r in rows:
        if r["metric"] == "furniture_cost_psf":
            tier = r["scope"].split(" markets")[0]
            bands[tier] = (float(r["low"]), float(r["high"]))

    # Price paid is (1 - discount). Public pays this share of what a commercial buyer pays.
    ratios = []
    for gov_scope, com_scope in PUBLIC_VS_COMMERCIAL_PAIRS:
        gov = _mid(_one(rows, "discount_off_list_gov", gov_scope)) / 100
        com = _mid(_one(rows, "discount_off_list_commercial", com_scope)) / 100
        ratios.append((1 - gov) / (1 - com))

    adders = [r for r in rows if r["metric"] == "adder_pct"]
    tax = {r["scope"]: float(r["value"]) for r in rows if r["metric"] == "sales_tax_pct"}
    ppi = {r["period"]: float(r["index"]) for r in _read("ppi_office_furniture.csv", data_dir)}

    return Book(
        bands=bands,
        ppi=ppi,
        escalation_pct=float(_one(rows, "escalation_pct_per_year")["value"]),
        public_price_factor=round(mean(ratios), 3),
        rsf_to_usf=float(_one(rows, "rentable_to_usable_ratio")["value"]),
        adders_pct=sum(float(r["value"]) for r in adders),
        tax_pct=tax,
        usf_per_person=float(_one(rows, "usable_sf_per_person")["value"]),
        sources={
            "band": "cw-fitout-2026",
            "escalation": "fred-ppi",
            "public_price_factor": "ne-contract-15378",
            "area_basis": "gsa-workspace-2012",
            "adders": "af-furniture-cost-guide",
            "tax": "ne-dor-tax",
            "usf_per_person": "gsa-workspace-2012",
        },
    )

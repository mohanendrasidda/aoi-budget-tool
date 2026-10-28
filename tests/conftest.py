"""Synthetic assumption book with round numbers, so expected values are easy to check by hand."""

import pytest

from aoi_budget.book import Book


@pytest.fixture
def book() -> Book:
    return Book(
        bands={"US Tier 3": (10.0, 20.0), "US Tier 2": (20.0, 30.0)},
        ppi={"2024": 100.0, "2025-12": 100.0, "2025": 100.0, "2026": 110.0},
        escalation_pct=10.0,
        public_price_factor=0.5,
        rsf_to_usf=0.8,
        adders_pct=20.0,
        tax_pct={"Test city": 10.0},
        usf_per_person=100.0,
        sources={
            k: "synthetic"
            for k in (
                "band",
                "escalation",
                "public_price_factor",
                "area_basis",
                "adders",
                "tax",
                "usf_per_person",
                "gross_basis",
            )
        },
    )

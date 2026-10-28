import pytest

from aoi_budget.book import load_book
from aoi_budget.estimator import Inputs, estimate, price_index


def test_unknown_finish_uses_full_band_at_base_price_level(book):
    e = estimate(Inputs(area_sf=1000, finish="unknown", period="2025-12"), book)
    assert (e.low, e.high) == (10_000, 20_000)
    assert e.factors[0].multiplier == 1.0


def test_finish_levels_pick_parts_of_the_band(book):
    def psf(finish):
        e = estimate(Inputs(area_sf=1, finish=finish, period="2025-12"), book)
        return e.psf_low, e.psf_high

    assert psf("basic") == (10, 15)
    assert psf("standard") == (12.5, 17.5)
    assert psf("premium") == (15, 20)


def test_every_factor_multiplies_and_is_listed(book):
    e = estimate(
        Inputs(
            area_sf=1,
            finish="unknown",
            period="2026",
            buyer="public",
            area_basis="GSF",
            include_adders=True,
            tax_scope="Test city",
        ),
        book,
    )
    # 1.1 escalation x 0.5 public x 0.8 area x 1.2 adders x 1.1 tax
    assert e.psf_low == pytest.approx(10 * 1.1 * 0.5 * 0.8 * 1.2 * 1.1)
    assert [f.name for f in e.factors] == [
        "Price level",
        "Public / co-op pricing",
        "Area basis",
        "Freight, install, handling",
        "Sales tax",
    ]


def test_future_years_project_at_escalation_rate(book):
    assert price_index(book, "2028") == pytest.approx(110 * 1.1**2)


def test_missing_past_period_is_an_error(book):
    with pytest.raises(ValueError):
        price_index(book, "2019")


@pytest.mark.parametrize(
    "bad",
    [{"area_sf": 0}, {"area_sf": 10, "finish": "gold"}, {"area_sf": 10, "buyer": "friend"}],
)
def test_inputs_are_validated(bad):
    with pytest.raises(ValueError):
        Inputs(**bad)


def test_public_book_loads_with_sourced_values():
    b = load_book()
    assert b.bands["US Tier 3"] == (23.39, 35.09)
    assert 0 < b.public_price_factor < 1
    assert b.adders_pct == 24
    assert "2025-12" in b.ppi


def test_reuse_lowers_the_estimate_and_is_listed(book):
    e = estimate(Inputs(area_sf=1000, finish="unknown", period="2025-12", reuse_pct=25), book)
    assert (e.low, e.high) == (7_500, 15_000)
    assert e.factors[-1].name == "Reused furniture"


def test_reuse_must_be_below_100():
    with pytest.raises(ValueError):
        Inputs(area_sf=10, reuse_pct=100)


def test_gross_area_uses_the_segment_efficiency_when_sourced(book):
    from dataclasses import replace

    b = replace(book, gsf_to_usf={"office": 0.5})
    office = estimate(Inputs(area_sf=1_000, area_basis="GSF", period="2025-12"), b)
    assert office.factors[-1].multiplier == 0.5
    assert office.factors[-1].source_id == "synthetic"
    other = estimate(Inputs(area_sf=1_000, area_basis="GSF", segment="housing"), b)
    assert [f.multiplier for f in other.factors if f.name == "Area basis"] == [0.8]  # rentable

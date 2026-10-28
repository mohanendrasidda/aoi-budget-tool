"""Synthetic price layer only: no AOI prices in tests (ADR 0004)."""

import csv

import pytest

from aoi_budget.estimator import Inputs
from aoi_budget.price_layer import (
    CATEGORY_DISCOUNT,
    DISCOUNT_SPREAD,
    bottom_up,
    counts,
    load_price_layer,
    order_tier,
    program_for,
    usable_area,
)
from aoi_budget.seller import Program

CATS = ("desk", "screen", "pedestal", "lateral_file", "task_chair", "guest_chair")
CATS += ("conference_table", "huddle_table")


@pytest.fixture
def layer(tmp_path):
    path = tmp_path / "items.csv"
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["category", "tier", "product", "list_usd", "book", "page", "note"])
        for cat in CATS:
            w.writerow([cat, "good", f"{cat} A", 100, "SYN", 1, ""])
            w.writerow([cat, "best", f"{cat} B", 300, "SYN", 2, ""])
    return load_price_layer(path)


def test_missing_file_means_no_layer(tmp_path):
    assert load_price_layer(tmp_path / "absent.csv") is None


def test_better_tier_is_the_midpoint_when_missing(layer):
    assert layer.prices[("desk", "better")] == 200
    assert layer.sources[("desk", "better")] == "midpoint of good and best"
    assert "SYN p.1" in layer.sources[("desk", "good")]


def test_kits_turn_a_program_into_item_counts():
    c = counts(Program(workstations=2, private_offices=1, conference_rooms=1, huddle_rooms=0))
    assert c["task_chair"] == 2 + 1 + 8
    assert c["desk"] == 2 * 2 + 2
    assert "huddle_table" not in c


def test_order_tiers_follow_the_contract_limits():
    assert [order_tier(x) for x in (10_000, 50_000, 50_001, 150_001)] == [0, 0, 1, 2]
    for cat, tiers in CATEGORY_DISCOUNT.items():
        assert tiers[0] <= tiers[1] <= tiers[2], cat  # bigger orders never discount less


def test_bottom_up_arithmetic(layer, book):
    one_ws = Program(workstations=1, private_offices=0, conference_rooms=0, huddle_rooms=0)
    est = bottom_up(
        one_ws, Inputs(area_sf=100, finish="basic", period="2026", buyer="public"), layer, book
    )
    # desk x2, screen x3, pedestal x1 at 100 with 1.05-1.15 uplift; task chair 100 x 1.20-1.40
    assert est.list_low == pytest.approx((6 * 100 * 1.05 + 100 * 1.20) * 1.10)
    assert est.list_high == pytest.approx((6 * 100 * 1.15 + 100 * 1.40) * 1.10)
    assert est.order_tier == 0
    d = {c: CATEGORY_DISCOUNT[c][0] for c in ("desk", "screen", "pedestal", "task_chair")}
    net_low = (
        2 * 105 * (1 - d["desk"] - DISCOUNT_SPREAD)
        + 3 * 105 * (1 - d["screen"] - DISCOUNT_SPREAD)
        + 105 * (1 - d["pedestal"] - DISCOUNT_SPREAD)
        + 120 * (1 - d["task_chair"] - DISCOUNT_SPREAD)
    ) * 1.10
    assert est.net_low == pytest.approx(net_low)
    assert est.low == pytest.approx(net_low * est.multiplier)
    assert est.psf_high == pytest.approx(est.high / 100)


def test_commercial_buyers_pay_more_than_public(layer, book):
    ws = Program(1, 0, 0, 0)
    pub = bottom_up(ws, Inputs(area_sf=100, buyer="public"), layer, book)
    com = bottom_up(ws, Inputs(area_sf=100, buyer="commercial"), layer, book)
    assert com.net_low == pytest.approx(pub.net_low / book.public_price_factor)


def test_premium_finish_uses_the_best_tier(layer, book):
    one_ws = Program(1, 0, 0, 0)
    basic = bottom_up(one_ws, Inputs(area_sf=100, finish="basic"), layer, book)
    premium = bottom_up(one_ws, Inputs(area_sf=100, finish="premium"), layer, book)
    assert premium.list_low == pytest.approx(basic.list_low * 3)


def test_seat_only_orders_are_workstations_only(book):
    program, area = program_for(None, 40, book)
    assert program == Program(40, 0, 0, 0)
    assert area == 40 * book.usf_per_person


def test_area_projects_are_sized_from_usable_area(book):
    from dataclasses import replace

    b = replace(book, gsf_to_usf={"academic": 0.5})
    assert usable_area(1_000, "GSF", "academic", b) == 500
    assert usable_area(1_000, "USF", "academic", b) == 1_000
    program, area = program_for(2_000, None, b, "GSF", "academic")
    assert area == 2_000  # $/sf stays on the stated area
    assert program.workstations + program.private_offices == 10  # 1,000 usable / 100 per person

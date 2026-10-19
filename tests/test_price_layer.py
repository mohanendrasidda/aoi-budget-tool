"""Synthetic price layer only: no AOI prices in tests (ADR 0004)."""

import csv

import pytest

from aoi_budget.estimator import Inputs
from aoi_budget.price_layer import (
    DISCOUNT_TIERS,
    bottom_up,
    counts,
    discount_for,
    load_price_layer,
    program_for,
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


def test_bigger_projects_get_deeper_discounts():
    small, large = discount_for(50_000), discount_for(5_000_000)
    assert small == DISCOUNT_TIERS[0][1:]
    assert large[0] > small[0] and large[1] > small[1]


def test_bottom_up_arithmetic(layer, book):
    one_ws = Program(workstations=1, private_offices=0, conference_rooms=0, huddle_rooms=0)
    est = bottom_up(one_ws, Inputs(area_sf=100, finish="basic", period="2026"), layer, book)
    # desk x2, screen x3, pedestal x1 at 100 with 1.05-1.15 uplift; task chair 100 x 1.20-1.40
    assert est.list_low == pytest.approx((6 * 100 * 1.05 + 100 * 1.20) * 1.10)
    assert est.list_high == pytest.approx((6 * 100 * 1.15 + 100 * 1.40) * 1.10)
    assert est.discount == DISCOUNT_TIERS[0][1:]
    assert est.low == pytest.approx(est.list_low * (1 - est.discount[1]) * est.multiplier)
    assert est.psf_high == pytest.approx(est.high / 100)
    assert {line.category for line in est.lines} == {"desk", "screen", "pedestal", "task_chair"}


def test_premium_finish_uses_the_best_tier(layer, book):
    one_ws = Program(1, 0, 0, 0)
    basic = bottom_up(one_ws, Inputs(area_sf=100, finish="basic"), layer, book)
    premium = bottom_up(one_ws, Inputs(area_sf=100, finish="premium"), layer, book)
    assert premium.list_low == pytest.approx(basic.list_low * 3)


def test_seat_only_orders_are_workstations_only(book):
    program, area = program_for(None, 40, book)
    assert program == Program(40, 0, 0, 0)
    assert area == 40 * book.usf_per_person

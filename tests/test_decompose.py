from math import log

import pytest

from aoi_budget.decompose import LineCost, decompose


def test_single_category_splits_exactly():
    est = [LineCost("chair", 12, 1000, 400)]  # 20% more chairs, list +0%, 60% off
    act = [LineCost("chair", 10, 1000, 500)]  # 50% off
    a = decompose(est, act)
    assert a.quantity == pytest.approx(log(1.2))
    assert a.unit_list == pytest.approx(0.0)
    assert a.discount == pytest.approx(log(0.4 / 0.5))
    assert a.quantity + a.unit_list + a.discount == pytest.approx(a.total_log_error)


def test_net_only_sources_report_list_and_discount_together():
    est = [LineCost("ws", 22, None, 4000)]
    act = [LineCost("ws", 22, None, 5000)]
    a = decompose(est, act)
    assert a.unit_list is None and a.discount is None
    assert a.quantity == 0
    assert a.unit_net == pytest.approx(log(0.8))


def test_parts_are_weighted_by_actual_cost_share():
    est = [LineCost("ws", 10, None, 100), LineCost("chair", 10, None, 10)]
    act = [LineCost("ws", 10, None, 100), LineCost("chair", 10, None, 20)]
    a = decompose(est, act)
    assert a.unit_net == pytest.approx((200 / 1200) * log(0.5))

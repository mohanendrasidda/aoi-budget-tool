from aoi_budget.estimator import Inputs
from aoi_budget.sensitivity import tornado


def test_tornado_is_sorted_widest_first(book):
    base, swings = tornado(Inputs(area_sf=1000, period="2026"), book)
    spreads = [s.spread for s in swings]
    assert spreads == sorted(spreads, reverse=True)
    assert base > 0


def test_swings_that_cannot_move_the_baseline_are_dropped(book):
    _, commercial = tornado(Inputs(area_sf=1000, period="2026", buyer="commercial"), book)
    _, public = tornado(Inputs(area_sf=1000, period="2026", buyer="public"), book)
    assert "Public discount gap" not in {s.name for s in commercial}
    assert "Public discount gap" in {s.name for s in public}


def test_finish_swing_matches_band_halves(book):
    _, swings = tornado(Inputs(area_sf=1000, period="2025-12"), book)
    finish = next(s for s in swings if s.name == "Finish level")
    # basic mid = 12.5/sf, premium mid = 17.5/sf, on 1000 sf
    assert (finish.low_total, finish.high_total) == (12_500, 17_500)

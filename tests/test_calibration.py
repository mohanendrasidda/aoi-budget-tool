import pytest

from aoi_budget.calibration import calibrate, conformal, interval_score, reference_class
from aoi_budget.evaluate import Project, Scored


def _s(pid, actual_psf, low, high, variant="adjusted"):
    p = Project(
        pid,
        pid,
        "2025",
        "office",
        "public",
        "contract",
        "furniture_only",
        1000.0,
        "USF",
        None,
        actual_psf * 1000,
    )
    return Scored(p, variant, 1000.0, actual_psf, low, high)


def test_interval_score_rewards_narrow_and_penalizes_misses():
    assert interval_score(10, 20, 15) == 10  # inside: just the width
    assert interval_score(10, 20, 25, alpha=0.2) == 10 + 10 * 5  # 5 above, x 2/alpha
    assert interval_score(10, 20, 8, alpha=0.2) == 10 + 10 * 2
    assert interval_score(14, 16, 15) < interval_score(10, 20, 15)


def test_reference_class_never_uses_the_project_itself(book):
    rows = [_s("a", 10, 0, 0), _s("b", 20, 0, 0), _s("c", 30, 0, 0)]
    ref = {s.project.id: s for s in reference_class(rows, book)}
    assert (ref["a"].low_psf, ref["a"].high_psf) == (20, 30)
    assert (ref["c"].low_psf, ref["c"].high_psf) == (10, 20)


def test_conformal_widens_by_the_other_projects_errors():
    rows = [_s("a", 10, 9, 11), _s("b", 20, 9, 11), _s("c", 5, 9, 11)]  # mid 10 for all
    conf = {s.project.id: s for s in conformal(rows, alpha=0.2)}
    # for "a", the other log errors are log(2) and log(0.5): range 10 x [0.5, 2]
    assert conf["a"].low_psf == pytest.approx(5)
    assert conf["a"].high_psf == pytest.approx(20)


def test_calibrate_reports_under_quoting_separately():
    rows = [_s("a", 25, 10, 20), _s("b", 15, 10, 20), _s("c", 5, 10, 20)]
    (c,) = calibrate(rows)
    assert c.coverage_pct == pytest.approx(100 / 3)
    assert c.under_pct == pytest.approx(100 / 3)

import pytest

from aoi_budget.evaluate import Project, evaluate, load_projects, report, summarize


def _project(pid, actual, **kw):
    base = dict(
        id=pid,
        name=pid,
        year="2025",
        segment="office",
        buyer="commercial",
        evidence="contract",
        scope="furniture_only",
        area_sf=1000.0,
        area_basis="USF",
        seats=None,
        actual_usd=actual,
    )
    return Project(**{**base, **kw})


def test_roles():
    assert _project("a", 1).role == "headline"
    assert _project("a", 1, scope="reuse_heavy").role == "floor"
    assert _project("a", 1, evidence="budget").role == "envelope"
    assert _project("a", 1, area_sf=None, seats=10).role == "per_seat"


def test_published_variant_scores_against_the_band(book):
    # Band is 10-20/sf at index 100; actual 15/sf sits in the middle.
    scored = evaluate([_project("mid", 15_000)], book)
    pub = next(s for s in scored if s.variant == "published")
    assert pub.inside and pub.error_pct == 0


def test_calibration_is_leave_one_out(book):
    # Both actuals are 2x the band midpoint (15/sf). Each project is calibrated on the other one.
    projects = [_project("a", 30_000), _project("b", 30_000)]
    cal = [s for s in evaluate(projects, book) if s.variant == "calibrated"]
    assert all(s.mid_psf == pytest.approx(30) for s in cal)


def test_single_headline_project_gets_no_calibration(book):
    cal = [s for s in evaluate([_project("only", 30_000)], book) if s.variant == "calibrated"]
    assert cal[0].mid_psf == pytest.approx(15)


def test_per_seat_area_comes_from_usable_sf_per_person(book):
    p = _project("seats", 15_000, area_sf=None, seats=10)
    pub = next(s for s in evaluate([p], book) if s.variant == "published")
    assert pub.area_sf == 1000 and pub.actual_psf == 15


def test_summary_counts_only_headline_projects(book):
    projects = [_project("h", 15_000), _project("f", 5_000, scope="reuse_heavy")]
    summary = {s.variant: s for s in summarize(evaluate(projects, book))}
    assert summary["published"].n == 1
    assert summary["published"].coverage_pct == 100


def test_public_projects_load_and_report_runs():
    projects = load_projects()
    assert {p.role for p in projects} >= {"headline", "floor", "envelope", "per_seat"}
    from aoi_budget.book import load_book

    assert "Headline accuracy" in report(evaluate(projects, load_book()))

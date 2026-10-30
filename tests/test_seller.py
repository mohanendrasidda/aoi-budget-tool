from aoi_budget.estimator import Inputs, estimate
from aoi_budget.seller import (
    biggest_unknown,
    client_summary,
    default_headcount,
    handoff_items,
    next_questions,
    quote_label,
    sanity_checks,
    space_program,
    talking_points,
    what_ifs,
)
from aoi_budget.sensitivity import Swing


def test_headcount_from_area():
    assert default_headcount(12_000, 200) == 60
    assert default_headcount(50, 200) == 1


def test_space_program_splits_offices_and_rooms():
    p = space_program(60, "Balanced")
    assert (p.workstations, p.private_offices) == (45, 15)
    assert (p.conference_rooms, p.huddle_rooms) == (4, 6)
    assert space_program(3, "Mostly open").conference_rooms == 1  # never zero rooms


def test_questions_follow_project_type_and_headcount():
    assert next_questions("New space", False, 60)[0].startswith("How many people")
    refresh = next_questions("Refresh", True, 60)
    assert not any(q.startswith("How many people") for q in refresh)
    assert any("reused" in q for q in refresh)


def test_summary_states_range_and_reuse(book):
    est = estimate(Inputs(area_sf=1000, period="2025-12", finish="standard"), book)
    text = client_summary("Test floor", est, 5, "standard", 25)
    assert "$12,500 to $17,500" in text
    assert "25% of furniture reused" in text and "Better finish" in text


def test_handoff_marks_notes_only_when_present():
    p = space_program(10, "Balanced")
    assert handoff_items(1000, 10, True, p, "basic", "")[-1] == (
        "Conversation notes attached",
        False,
    )
    assert handoff_items(1000, 10, True, p, "basic", "x")[-1][1] is True


def test_quote_label_maps_sources_to_plain_words():
    assert quote_label("assumption") == "Assumption"
    assert quote_label("seller input") == "From the client"
    assert quote_label("synthetic") == "Published"


def test_talking_points_use_only_the_estimates_own_numbers(book):
    est = estimate(Inputs(area_sf=1000, period="2025-12", reuse_pct=25, include_adders=True), book)
    points = talking_points(est, 10, "standard")
    # band 10-20, Better = middle half 12.5-17.5, x0.75 reuse x1.2 adders = 11.25-15.75 per sf,
    # said aloud to the nearest thousand
    assert points[0] == (
        "Roughly $11,000 to $16,000 for 1,000 sq ft and about 10 people.",
        "Published",
    )
    assert points[1][1] == "Assumption"
    reuse = [p for p in points if p[0].startswith("Reused furniture")][0]
    assert reuse == ("Reused furniture takes off about 25%.", "From the client")
    assert any(t.startswith("Freight, install, handling adds about 20%") for t, _ in points)
    assert not any(t.startswith("Price level") for t, _ in points)  # x1.0 adds nothing


def test_sanity_checks_flag_typos_only():
    p = space_program(60, "Balanced")
    assert sanity_checks(12_000, 60, True, p) == []
    assert "very tight" in sanity_checks(1_200, 60, True, p)[0]
    assert "very roomy" in sanity_checks(60_000, 60, True, p)[0]
    assert sanity_checks(1_200, 60, False, p) == []  # estimated headcount cannot be a typo
    many_offices = space_program(60, "Balanced").__class__(0, 70, 1, 1)
    assert "more offices than people" in sanity_checks(12_000, 60, True, many_offices)[0]


def test_what_ifs_only_offer_changes_that_move_the_price(book):
    base = Inputs(area_sf=1000, period="2025-12", finish="standard")
    alts = dict(what_ifs(base, book))
    assert set(alts) == {
        "Good finish instead",
        "Best finish instead",
        "With freight, install and handling",
        "Reusing about 25% of existing furniture",
    }
    now = estimate(base, book).mid
    assert all(a.mid != now for a in alts.values())
    assert alts["Good finish instead"].mid < now < alts["Best finish instead"].mid
    done = Inputs(area_sf=1000, period="2025-12", include_adders=True, reuse_pct=10)
    assert len(what_ifs(done, book)) == 2  # already included, so not offered again


def test_biggest_unknown_names_the_widest_swing():
    swings = [Swing("Finish level", "basic", "premium", 10_000, 30_000)]
    assert biggest_unknown(swings).startswith("Biggest unknown: finish level (basic vs premium")
    assert "$20,000" in biggest_unknown(swings)
    assert biggest_unknown([]) is None

from aoi_budget.estimator import Inputs, estimate
from aoi_budget.seller import (
    client_summary,
    default_headcount,
    handoff_items,
    next_questions,
    space_program,
)


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

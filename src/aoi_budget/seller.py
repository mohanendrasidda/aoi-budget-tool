"""Seller-facing helpers for the demo UI (#16): space program, next questions, client summary.

Plain functions so the app stays thin and every piece is testable without a browser. Nothing
here sets a price; prices come only from aoi_budget.estimator.
"""

from dataclasses import dataclass

from aoi_budget.estimator import Estimate

# Assumptions until partner data is approved; shown to the seller as assumptions.
PRIVATE_SHARE = {"Mostly open": 0.10, "Balanced": 0.25, "Private-heavy": 0.50}
PEOPLE_PER_CONFERENCE = 15
PEOPLE_PER_HUDDLE = 10
FINISH_LABEL = {"basic": "Good", "standard": "Better", "premium": "Best"}
PROJECT_TYPES = ("New space", "Refresh", "Expansion")


@dataclass(frozen=True)
class Program:
    workstations: int
    private_offices: int
    conference_rooms: int
    huddle_rooms: int


def default_headcount(area_sf: float, usf_per_person: float) -> int:
    return max(1, round(area_sf / usf_per_person))


def space_program(headcount: int, mix: str) -> Program:
    offices = round(headcount * PRIVATE_SHARE[mix])
    return Program(
        workstations=headcount - offices,
        private_offices=offices,
        conference_rooms=max(1, round(headcount / PEOPLE_PER_CONFERENCE)),
        huddle_rooms=max(1, round(headcount / PEOPLE_PER_HUDDLE)),
    )


def next_questions(project_type: str, headcount_given: bool, headcount: int) -> list[str]:
    q = []
    if not headcount_given:
        q.append(f"How many people will sit here? (estimated {headcount} from square footage)")
    q.append("Who needs a private office, and how many meeting rooms do they use today?")
    if project_type == "New space":
        q.append("Is any existing furniture worth reusing? It can lower the budget.")
    if project_type == "Refresh":
        q.append("Which pieces are being reused? Confirm their condition before counting on them.")
    q.append("Any preferred brands or product lines?")
    q.append("Move-in date and any phasing? Lead times can drive product choices.")
    return q


def client_summary(label: str, est: Estimate, headcount: int, finish: str, reuse_pct: float) -> str:
    reuse = f", with about {reuse_pct:g}% of furniture reused" if reuse_pct else ""
    return (
        f"Preliminary furniture budget for {label or 'this project'}\n"
        f"${est.low:,.0f} to ${est.high:,.0f} "
        f"(about ${est.psf_low:,.0f} to ${est.psf_high:,.0f} per sq ft)\n"
        f"{est.area_sf:,.0f} sq ft, about {headcount} people, "
        f"{FINISH_LABEL[finish]} finish level{reuse}.\n\n"
        "This is an early range based on published market benchmarks, before any product is "
        "selected. We'll narrow it once we confirm headcount, the mix of offices and open "
        "seating, and your product preferences."
    )


def handoff_items(
    area_sf: float, headcount: int, headcount_given: bool, program: Program, finish: str, notes: str
) -> list[tuple[str, bool]]:
    """(item, already done?) for the designer hand-off checklist."""
    return [
        (f"Square footage confirmed ({area_sf:,.0f} sq ft)", True),
        (f"Headcount confirmed ({headcount})", headcount_given),
        (
            f"Space program: {program.workstations} workstations, {program.private_offices} "
            f"offices, {program.conference_rooms} conference, {program.huddle_rooms} huddle",
            False,
        ),
        (f"Finish level agreed ({FINISH_LABEL[finish]})", False),
        ("Budget range shared with the client", False),
        ("Conversation notes attached", bool(notes.strip())),
    ]

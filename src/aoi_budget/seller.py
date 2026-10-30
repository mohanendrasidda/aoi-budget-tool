"""Seller-facing helpers for the demo UI (#16): space program, next questions, client summary.

Plain functions so the app stays thin and every piece is testable without a browser. Nothing
here sets a price; prices come only from aoi_budget.estimator.
"""

from dataclasses import dataclass, replace

from aoi_budget.book import Book
from aoi_budget.estimator import Estimate, Inputs, estimate
from aoi_budget.sensitivity import Swing

# Assumptions until partner data is approved; shown to the seller as assumptions.
PRIVATE_SHARE = {"Mostly open": 0.10, "Balanced": 0.25, "Private-heavy": 0.50}
PEOPLE_PER_CONFERENCE = 15
PEOPLE_PER_HUDDLE = 10
FINISH_LABEL = {"basic": "Good", "standard": "Better", "premium": "Best"}
FINISH_PLACEMENT = {"basic": "lower half", "standard": "middle half", "premium": "upper half"}
PROJECT_TYPES = ("New space", "Refresh", "Expansion")
# Assumption: usable sq ft per person outside this range is rare for an office, so it is more
# likely a typo than a real plan. Used only to warn, never to change a number.
TIGHT_SF_PER_PERSON = 75
ROOMY_SF_PER_PERSON = 500
WHAT_IF_REUSE_PCT = 25.0


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


def quote_label(source_id: str) -> str:
    """Plain answer to "can I say this to the client?" for one part of the estimate."""
    if source_id == "assumption":
        return "Assumption"
    if source_id == "seller input":
        return "From the client"
    return "Published"


def talking_points(est: Estimate, headcount: int, finish: str) -> list[tuple[str, str]]:
    """(sentence the seller can say, quote label), built only from the estimate's own factors."""
    points = [
        (
            f"Roughly ${round(est.low, -3):,.0f} to ${round(est.high, -3):,.0f} for "
            f"{est.area_sf:,.0f} sq ft and "
            f"about {headcount} people.",
            "Published",
        ),
        (
            f"{FINISH_LABEL[finish]} finish puts it in the {FINISH_PLACEMENT[finish]} of the "
            "published market range for office furniture.",
            "Assumption",
        ),
    ]
    for f in est.factors:
        pct = (f.multiplier - 1) * 100
        if abs(pct) < 0.5:
            continue
        verb = "adds" if pct > 0 else "takes off"
        points.append((f"{f.name} {verb} about {abs(pct):.0f}%.", quote_label(f.source_id)))
    return points


def sanity_checks(
    area_sf: float, headcount: int, headcount_given: bool, program: Program
) -> list[str]:
    """Warnings for inputs that look like typos. Warn only; the seller decides."""
    out = []
    if headcount_given:
        per = area_sf / headcount
        if per < TIGHT_SF_PER_PERSON:
            out.append(
                f"{area_sf:,.0f} sq ft for {headcount} people is about {per:.0f} sq ft each, "
                "which is very tight. Check the square footage and headcount."
            )
        elif per > ROOMY_SF_PER_PERSON:
            out.append(
                f"{area_sf:,.0f} sq ft for {headcount} people is about {per:,.0f} sq ft each, "
                "which is very roomy. Check the headcount, or whether part of the space stays "
                "unfurnished."
            )
    if program.private_offices > headcount:
        out.append(
            f"{program.private_offices} offices for {headcount} people is more offices than "
            "people. Check the office count."
        )
    return out


def what_ifs(inputs: Inputs, book: Book) -> list[tuple[str, Estimate]]:
    """One-change alternatives for common client questions. Only changes that move the price."""
    options = [
        (f"{FINISH_LABEL[f]} finish instead", replace(inputs, finish=f))
        for f in FINISH_LABEL
        if f != inputs.finish
    ]
    if not inputs.include_adders:
        options.append(("With freight, install and handling", replace(inputs, include_adders=True)))
    if not inputs.reuse_pct:
        options.append(
            (
                f"Reusing about {WHAT_IF_REUSE_PCT:g}% of existing furniture",
                replace(inputs, reuse_pct=WHAT_IF_REUSE_PCT),
            )
        )
    return [(label, estimate(i, book)) for label, i in options]


def biggest_unknown(swings: list[Swing]) -> str | None:
    """The one question that would narrow the range most (swings come widest first)."""
    if not swings:
        return None
    s = swings[0]
    return (
        f"Biggest unknown: {s.name.lower()} ({s.low_label} vs {s.high_label} moves the middle "
        f"of the range by ${s.spread:,.0f}). Settle this first."
    )

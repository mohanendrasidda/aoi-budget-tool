"""Evaluation harness (#15): score the estimator against public projects with known totals.

Run: uv run python -m aoi_budget.evaluate

Roles decide what a project can prove:
- headline: awarded contract, furniture only, area known. Coverage and error are computed here.
- floor: contract that reused furniture. The estimate should sit above it.
- envelope: program-statement budget. The estimate should sit at or below it.
- per_seat: itemized seats, no building area. Area is seats x usable sf per person.
A total marked certainty=upper_bound (e.g. a seat count that is only a minimum) is scored as an
envelope, whatever its evidence.

Variants: published (band only), adjusted (+ sourced factors), calibrated (adjusted, scaled
leave-one-out), informed (adjusted + the finish level recorded for the project; rule declared
in docs/error-analysis.md: competitive public procurement is scored at the basic finish).
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import median

from aoi_budget.book import DATA_DIR, Book, load_book
from aoi_budget.estimator import Inputs, estimate

VARIANTS = ("published", "adjusted", "informed", "calibrated", "bottom_up")


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    year: str
    segment: str
    buyer: str
    evidence: str
    scope: str
    area_sf: float | None
    area_basis: str
    seats: int | None
    actual_usd: float
    procurement: str = ""
    finish: str = "unknown"
    certainty: str = ""

    @property
    def role(self) -> str:
        if self.evidence == "budget":
            return "envelope"
        if self.scope == "reuse_heavy":
            return "floor"  # reuse makes the total a minimum, even if it is also capped
        if self.certainty == "upper_bound":
            return "envelope"
        if self.area_sf is None:
            return "per_seat"
        return "headline"


@dataclass(frozen=True)
class Scored:
    project: Project
    variant: str
    area_sf: float
    actual_psf: float
    low_psf: float
    high_psf: float

    @property
    def mid_psf(self) -> float:
        return (self.low_psf + self.high_psf) / 2

    @property
    def inside(self) -> bool:
        return self.low_psf <= self.actual_psf <= self.high_psf

    @property
    def error_pct(self) -> float:
        """Signed error of the midpoint: positive means the estimate is too high."""
        return (self.mid_psf - self.actual_psf) / self.actual_psf * 100

    @property
    def passes(self) -> bool:
        role = self.project.role
        if role == "floor":
            return self.low_psf >= self.actual_psf
        if role == "envelope":
            return self.mid_psf <= self.actual_psf
        return self.inside


def load_projects(data_dir: Path = DATA_DIR) -> list[Project]:
    with (data_dir / "eval_projects.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [
        Project(
            id=r["id"],
            name=r["name"],
            year=r["year"],
            segment=r["segment"],
            buyer=r["buyer"],
            evidence=r["evidence"],
            scope=r["scope"],
            area_sf=float(r["area_sf"]) if r["area_sf"] else None,
            area_basis=r["area_basis"] or "USF",
            seats=int(r["seats"]) if r["seats"] else None,
            actual_usd=float(r["actual_usd"]),
            procurement=r.get("procurement", ""),
            finish=r.get("finish") or "unknown",
            certainty=r.get("certainty", ""),
        )
        for r in rows
    ]


def _inputs(p: Project, book: Book, variant: str) -> Inputs:
    area = p.area_sf if p.area_sf is not None else p.seats * book.usf_per_person
    if variant == "published":
        return Inputs(area_sf=area, finish="unknown", period=p.year)
    finish = p.finish if variant == "informed" else "unknown"
    return Inputs(
        area_sf=area, area_basis=p.area_basis, finish=finish, buyer=p.buyer, period=p.year
    )


def _score(p: Project, book: Book, variant: str, scale: float = 1.0) -> Scored:
    inputs = _inputs(p, book, variant)
    est = estimate(inputs, book)
    return Scored(
        project=p,
        variant=variant,
        area_sf=inputs.area_sf,
        actual_psf=p.actual_usd / inputs.area_sf,
        low_psf=est.psf_low * scale,
        high_psf=est.psf_high * scale,
    )


def evaluate(projects: list[Project], book: Book) -> list[Scored]:
    """Score every project under every variant.

    The calibrated variant scales the adjusted band by the median actual/estimate ratio of the
    OTHER headline projects (leave-one-out), so no project is scored with its own answer.
    """
    out = []
    headline = [p for p in projects if p.role == "headline"]
    adjusted = {p.id: _score(p, book, "adjusted") for p in projects}
    for p in projects:
        out.append(_score(p, book, "published"))
        out.append(adjusted[p.id])
        out.append(_score(p, book, "informed"))
        others = [adjusted[h.id] for h in headline if h.id != p.id]
        scale = median(s.actual_psf / s.mid_psf for s in others) if others else 1.0
        out.append(_score(p, book, "calibrated", scale))
    return out


@dataclass(frozen=True)
class Summary:
    variant: str
    n: int
    coverage_pct: float
    median_abs_error_pct: float
    median_width_pct: float


def summarize(scored: list[Scored]) -> list[Summary]:
    out = []
    for v in VARIANTS:
        rows = [s for s in scored if s.variant == v and s.project.role == "headline"]
        if not rows:
            continue
        out.append(
            Summary(
                variant=v,
                n=len(rows),
                coverage_pct=100 * sum(s.inside for s in rows) / len(rows),
                median_abs_error_pct=median(abs(s.error_pct) for s in rows),
                median_width_pct=median((s.high_psf - s.low_psf) / s.mid_psf * 100 for s in rows),
            )
        )
    return out


def report(scored: list[Scored]) -> str:
    lines = [
        "## Headline accuracy (awarded contracts, furniture only)",
        "",
        "| Variant | n | Coverage | Median abs error | Median band width |",
        "|---|---|---|---|---|",
    ]
    for s in summarize(scored):
        lines.append(
            f"| {s.variant} | {s.n} | {s.coverage_pct:.0f}% | {s.median_abs_error_pct:.0f}% "
            f"| {s.median_width_pct:.0f}% |"
        )
    lines += [
        "",
        "## Every project ($/sf of the stated area; per-seat rows use seats x usable sf/person)",
        "",
        "| Project | Year | Role | Variant | Actual $/sf | Estimate $/sf | Error | Check |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for s in scored:
        p = s.project
        lines.append(
            f"| {p.name} | {p.year} | {p.role} | {s.variant} | {s.actual_psf:.2f} "
            f"| {s.low_psf:.2f}-{s.high_psf:.2f} | {s.error_pct:+.0f}% "
            f"| {'pass' if s.passes else 'FAIL'} |"
        )
    return "\n".join(lines)


def main() -> None:
    print(report(evaluate(load_projects(), load_book())))


if __name__ == "__main__":
    main()

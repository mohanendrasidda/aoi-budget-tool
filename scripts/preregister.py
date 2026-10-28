"""Freeze estimates for projects whose totals are not known yet (docs/accuracy-target.md, rule 3).

Run: uv run python scripts/preregister.py

Reads the declared inputs in data/public/prereg_inputs.csv and writes:
- data/public/preregistered_estimates.csv: benchmark (public-data) estimates, committed.
- data/raw/aoi-derived/preregistered_bottom_up.csv: partner price-book estimates, local only.
Prints the SHA-256 of each file. Record the hashes outside the repo, with a timestamp, before any
partner total is revealed. Estimates are 2026 dollars, furniture only (no add-ons, no tax).
"""

import csv
import hashlib
import subprocess
from pathlib import Path

from aoi_budget import __version__
from aoi_budget.book import DATA_DIR, load_book
from aoi_budget.estimator import Inputs, estimate
from aoi_budget.price_layer import ITEMS_PATH, bottom_up, load_price_layer, program_for
from aoi_budget.seller import Program, space_program

INPUTS = DATA_DIR / "prereg_inputs.csv"
PUBLIC_OUT = DATA_DIR / "preregistered_estimates.csv"
LOCAL_OUT = ITEMS_PATH.parent.parent / "preregistered_bottom_up.csv"


def _int(v: str) -> int | None:
    return int(v) if v else None


def _program(r: dict, book) -> Program | None:
    heads = _int(r["headcount"])
    if heads is None:
        return None  # program_for derives it from usable area
    p = space_program(heads, "Balanced")
    ws, po, conf = _int(r["workstations"]), _int(r["private_offices"]), _int(r["conference_rooms"])
    return Program(
        workstations=ws if ws is not None else p.workstations,
        private_offices=po if po is not None else (0 if ws is not None else p.private_offices),
        conference_rooms=conf if conf is not None else p.conference_rooms,
        huddle_rooms=p.huddle_rooms,
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    book, layer = load_book(), load_price_layer()
    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    rows = list(csv.DictReader(INPUTS.open(newline="", encoding="utf-8")))
    pub, loc = [], []
    for r in rows:
        inputs = Inputs(
            area_sf=float(r["area_sf"]),
            area_basis=r["area_basis"],
            finish="unknown",
            buyer=r["buyer"],
            period="2026",
            segment=r["segment"],
        )
        e = estimate(inputs, book)
        pub.append(
            {
                "id": r["id"],
                "method": f"benchmark adjusted, aoi_budget {__version__} @ {commit}",
                "low_usd": round(e.low),
                "high_usd": round(e.high),
                "mid_usd": round(e.mid),
            }
        )
        if layer:
            program = _program(r, book)
            if program is None:
                program, _ = program_for(inputs.area_sf, None, book, r["area_basis"], r["segment"])
            bu = bottom_up(program, inputs, layer, book)
            loc.append(
                {
                    "id": r["id"],
                    "method": f"bottom-up price layer @ {commit}",
                    "workstations": program.workstations,
                    "private_offices": program.private_offices,
                    "low_usd": round(bu.low),
                    "high_usd": round(bu.high),
                }
            )
    for path, data in ((PUBLIC_OUT, pub), (LOCAL_OUT, loc)):
        if not data:
            continue
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(data)
        print(f"{path.name}: {len(data)} rows, sha256 {sha256(path)}")


if __name__ == "__main__":
    main()

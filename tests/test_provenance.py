"""Every public data row traces to a URL and an ISO date (data-collection-policy.md)."""

import csv
from datetime import date
from pathlib import Path

import pytest

PUBLIC = Path(__file__).resolve().parents[1] / "data" / "public"
# Model outputs, not sourced facts; frozen by hash (docs/accuracy-target.md, rule 3).
OUTPUTS = {"preregistered_estimates.csv"}
FILES = sorted(p for p in PUBLIC.glob("*.csv") if p.name not in OUTPUTS)


def _rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_expected_files_present():
    names = {p.name for p in FILES}
    assert {"benchmarks.csv", "eval_projects.csv", "ppi_office_furniture.csv"} <= names


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_file_has_rows(path):
    assert _rows(path), f"{path.name} is empty"


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_every_row_has_source_url(path):
    missing = [
        i
        for i, r in enumerate(_rows(path), start=2)
        if not (r.get("source_url") or "").startswith("https://")
    ]
    assert not missing, f"{path.name}: rows without an https source_url (lines): {missing}"


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_every_row_has_iso_retrieved_at(path):
    bad = []
    for i, r in enumerate(_rows(path), start=2):
        try:
            date.fromisoformat(r.get("retrieved_at") or "")
        except ValueError:
            bad.append(i)
    assert not bad, f"{path.name}: rows without an ISO retrieved_at date (lines): {bad}"

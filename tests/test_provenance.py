"""Every public benchmark row traces to a URL and an ISO date (data-collection-policy.md)."""

import csv
from datetime import date
from pathlib import Path

BENCHMARKS = Path(__file__).resolve().parents[1] / "data" / "public" / "benchmarks.csv"


def _rows():
    with BENCHMARKS.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_benchmarks_file_has_rows():
    assert _rows(), "benchmarks.csv is empty"


def test_every_row_has_source_url():
    missing = [
        i
        for i, r in enumerate(_rows(), start=2)
        if not (r.get("source_url") or "").startswith("https://")
    ]
    assert not missing, f"rows without an https source_url (CSV line numbers): {missing}"


def test_every_row_has_iso_retrieved_at():
    bad = []
    for i, r in enumerate(_rows(), start=2):
        try:
            date.fromisoformat(r.get("retrieved_at") or "")
        except ValueError:
            bad.append(i)
    assert not bad, f"rows without an ISO retrieved_at date (CSV line numbers): {bad}"

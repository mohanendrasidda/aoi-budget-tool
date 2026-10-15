"""University of Nebraska Board of Regents agendas -> text, for evaluation projects.

Run: uv run python -m aoi_budget.collect.nu_regents

Lists the "with materials" agenda PDFs on the public index, downloads each politely, converts it
with `pdftotext -layout`, and deletes the PDF (URL + SHA-256 stay in the manifest, so any file
can be re-downloaded and checked). Already-converted agendas are skipped.
"""

import re
import subprocess
import sys
from urllib.parse import quote, unquote

from aoi_budget.collect.fetch import Blocked, Fetcher

INDEX_URL = "https://nebraska.edu/regents/agendas-minutes/"
ALLOWED_HOSTS = ("https://docs.nebraska.edu/", "https://cdn.nebraska.edu/")
SUBDIR = "nu-regents"


def normalize(url: str) -> str:
    return quote(unquote(url), safe=":/,")


def agenda_urls(index_html: str) -> list[str]:
    """Materials agendas only; skips notices, minutes and results-only agendas."""
    out = []
    for href in re.findall(r'href="([^"]+)"', index_html):
        url = normalize(href)
        name = unquote(url.rsplit("/", 1)[-1]).lower()
        if url.startswith(ALLOWED_HOSTS) and "materials" in name and url not in out:
            out.append(url)
    return out


def slug(url: str) -> str:
    name = unquote(url.rsplit("/", 1)[-1])
    name = re.sub(r"\.pdf$", "", name, flags=re.IGNORECASE)
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


TABLE_START = re.compile(r"Business and Finance Report\s*[\u2013-]\s*Bids and Contracts")
TABLE_END = re.compile(r"^\s*\*\s*Approved budget amount", re.MULTILINE)
# A row starts with "Type of Action" at the left margin followed by a campus code.
ROW_START = re.compile(
    r"^ {0,8}[A-Z][A-Za-z/&-]+(?: [A-Za-z/&-]+)?\s{2,}(?:UNL|UNO|UNMC|UNK|NCTA|UNCA|NU|UN|System)\b"
)
FURNITURE = re.compile(r"furniture|furnishings|FF&E|movable equipment", re.IGNORECASE)
MONEY = re.compile(r"\$\s?[\d,]+(?:\.\d{2})?")
SKIP = re.compile(r"Page \d+ of \d+|Type of Action|Budget Amount|Business and Finance Report")


def bids_rows(text: str) -> list[str]:
    """Rows of every Bids and Contracts table, each joined into one line of text."""
    rows: list[str] = []
    for start in TABLE_START.finditer(text):
        end = TABLE_END.search(text, start.end())
        block = text[start.end() : end.start() if end else start.end() + 20_000]
        current: list[str] = []
        for line in block.splitlines():
            if not line.strip() or SKIP.search(line):
                continue
            if ROW_START.match(line) and current:
                rows.append(" ".join(current))
                current = []
            current.append(" ".join(line.split()))
        if current:
            rows.append(" ".join(current))
    return rows


def furniture_rows(text: str) -> list[str]:
    return [r for r in bids_rows(text) if FURNITURE.search(r) and MONEY.search(r)]


def scan() -> None:
    """Print every furniture row found in the converted agendas, for manual review."""
    text_dir = Fetcher().safe_path(f"{SUBDIR}/text")
    for path in sorted(text_dir.glob("*.txt")):
        for row in furniture_rows(path.read_text("utf-8", "replace")):
            print(f"{path.stem} | {row}")


def main() -> None:
    if "--scan" in sys.argv:
        scan()
        return
    fetcher = Fetcher()
    index = fetcher.download(INDEX_URL, f"{SUBDIR}/index.html").read_text("utf-8", "replace")
    urls = agenda_urls(index)
    print(f"{len(urls)} materials agendas listed")
    for n, url in enumerate(urls, start=1):
        txt = fetcher.safe_path(f"{SUBDIR}/text/{slug(url)}.txt")
        if txt.exists():
            continue
        try:
            pdf = fetcher.download(url, f"{SUBDIR}/pdf/{slug(url)}.pdf")
        except Blocked as e:
            print(f"[{n}] blocked, skipped: {e}")
            continue
        except Exception as e:  # one bad file should not stop the run
            print(f"[{n}] failed: {url}: {e}", file=sys.stderr)
            continue
        txt.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], check=True, timeout=600)
        pdf.unlink()
        print(f"[{n}/{len(urls)}] {txt.name}")


if __name__ == "__main__":
    main()

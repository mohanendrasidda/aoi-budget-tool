"""Remove client names and contact details before any AI processing (#18).

Run (names file is written by a person, one name per line; it never enters the repo):
    uv run python -m aoi_budget.redact --terms data/raw/aoi-derived/redact.txt FILE...

Each input (.pdf, .xlsx, .txt) becomes a redacted .txt in data/raw/aoi-derived/redacted/,
named F<n>.<ext>.txt so original file names (which can contain a client name) are not copied.
Output reports counts only, never the matched text. A person spot-checks the result.
"""

import argparse
import re
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree

OUT_DIR = Path("data/raw/aoi-derived/redacted")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def load_terms(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    terms = {t.strip() for t in lines if t.strip() and not t.lstrip().startswith("#")}
    return sorted(terms, key=len, reverse=True)  # longest first: "Acme Corp" before "Acme"


def redact(text: str, terms: list[str]) -> tuple[str, dict[str, int]]:
    counts = {"name": 0, "email": 0, "phone": 0}
    text, counts["email"] = EMAIL.subn("[EMAIL]", text)
    text, counts["phone"] = PHONE.subn("[PHONE]", text)
    for term in terms:
        pattern = re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)", re.IGNORECASE)
        text, n = pattern.subn("[REDACTED]", text)
        counts["name"] += n
    return text, counts


def xlsx_text(path: Path) -> str:
    """Every sheet as tab-separated rows, using only the standard library."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ElementTree.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
        sheets = sorted(
            (n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n)),
            key=lambda n: int(re.search(r"(\d+)\.xml$", n).group(1)),
        )
        out = []
        for i, name in enumerate(sheets, start=1):
            out.append(f"=== sheet {i}")
            root = ElementTree.fromstring(z.read(name))
            for row in root.iter(f"{{{NS['m']}}}row"):
                cells = []
                for c in row.findall("m:c", NS):
                    v = c.find("m:v", NS)
                    inline = c.find("m:is", NS)
                    if c.get("t") == "s" and v is not None:
                        val = shared[int(v.text)]
                    elif inline is not None:
                        val = "".join(t.text or "" for t in inline.iter(f"{{{NS['m']}}}t"))
                    else:
                        val = v.text if v is not None else ""
                    cells.append(f"{c.get('r')}={val}")
                if any(x.split("=", 1)[1] for x in cells):
                    out.append("\t".join(cells))
        return "\n".join(out)


def to_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".xlsx":
        return xlsx_text(path)
    if suffix == ".pdf":
        result = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"], capture_output=True, check=True, timeout=600
        )
        return result.stdout.decode("utf-8", "replace")
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--terms", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    ap.add_argument("files", type=Path, nargs="+")
    args = ap.parse_args()
    terms = load_terms(args.terms)
    args.out.mkdir(parents=True, exist_ok=True)
    print(f"{len(terms)} names loaded")
    for n, path in enumerate(args.files, start=1):
        text, counts = redact(to_text(path), terms)
        dest = args.out / f"F{n}{path.suffix.lower()}.txt"
        dest.write_text(text, encoding="utf-8")
        print(
            f"F{n}{path.suffix.lower()}: {counts['name']} names, {counts['email']} emails, "
            f"{counts['phone']} phones redacted -> {dest}"
        )


if __name__ == "__main__":
    main()

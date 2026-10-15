"""Polite fetcher for public documents (rules in docs/data-collection-policy.md).

- Checks robots.txt for every host before the first request; a missing robots.txt (404) allows.
- Identifies itself, waits between requests, and caps file size.
- Writes only under data/raw-public/ and records URL, date, size and SHA-256 in a manifest.
- Downloaded files are untrusted: they are only hashed and passed to pdftotext, never executed.

It never retries around a block: a 401/403/429 or a robots.txt "no" stops that URL.
"""

import csv
import hashlib
import time
import urllib.error
import urllib.request
import urllib.robotparser
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

RAW_PUBLIC = Path(__file__).resolve().parents[3] / "data" / "raw-public"
USER_AGENT = "aoi-budget-tool-research/0.1 (ENGR 491 student project; github.com/mohanendrasidda)"
MANIFEST_FIELDS = ["url", "path", "retrieved_at", "bytes", "sha256"]


class Blocked(Exception):
    """The site said no (robots.txt or HTTP status). Do not work around it."""


@dataclass
class Fetcher:
    root: Path = RAW_PUBLIC
    delay_s: float = 5.0
    max_bytes: int = 80_000_000
    timeout_s: float = 120.0

    def __post_init__(self) -> None:
        self._robots: dict[str, urllib.robotparser.RobotFileParser] = {}
        self._last = 0.0

    def safe_path(self, relative: str) -> Path:
        """Resolve a path inside root; refuse anything that escapes it."""
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root.resolve()):
            raise ValueError(f"refusing to write outside {self.root}: {relative}")
        return path

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        if parts.scheme != "https":
            return False
        host = parts.netloc
        if host not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                body = self._get(f"https://{host}/robots.txt", max_bytes=1_000_000)
                rp.parse(body.decode("utf-8", "replace").splitlines())
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    rp.disallow_all = True
                else:  # 404 and other "no file" answers mean no rules
                    rp.allow_all = True
            self._robots[host] = rp
        return self._robots[host].can_fetch(USER_AGENT, url)

    def _get(self, url: str, max_bytes: int) -> bytes:
        wait = self.delay_s - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                data = resp.read(max_bytes + 1)
        finally:
            self._last = time.monotonic()
        if len(data) > max_bytes:
            raise ValueError(f"file larger than {max_bytes} bytes: {url}")
        return data

    def download(self, url: str, relative: str) -> Path:
        if not self.allowed(url):
            raise Blocked(f"robots.txt disallows {url}")
        try:
            data = self._get(url, self.max_bytes)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 429):
                raise Blocked(f"HTTP {e.code} for {url}") from e
            raise
        path = self.safe_path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self._record(url, path, data)
        return path

    def _record(self, url: str, path: Path, data: bytes) -> None:
        manifest = self.root / "MANIFEST.csv"
        new = not manifest.exists()
        with manifest.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
            if new:
                w.writeheader()
            w.writerow(
                {
                    "url": url,
                    "path": str(path.relative_to(self.root.resolve())),
                    "retrieved_at": date.today().isoformat(),
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )

# Data collection policy (public sources)

Every number in the tool must trace to a URL and a date. These rules apply to any download or scrape.

1. Public pages only. No logins, dealer portals, paywalls, or form-gated content.
2. Check robots.txt and the site's terms before each run; record the check in the run manifest.
3. Be slow and identifiable: >= 5 seconds between requests to a host, User-Agent
   "AOI-Budget-Tool-ENGR491/0.1 (+contact: <team email>)", cache so each file downloads once.
4. Prefer downloads and APIs over HTML scraping.
5. Originals stay out of git: raw files go in data/raw-public/ (gitignored). Commit only derived CSVs with
   columns source_url, retrieved_at (UTC ISO date), source_sha256.
6. Classification: Public. Provenance columns are mandatory; a test fails on any row missing them.
7. No personal data. Drop any name/contact fields at parse time.
8. AI-assisted extraction is verified by code: schema validation on every row, plus a random 5% compared
   against the PDF text.
9. Downloaded files are untrusted input: parse with a library, never execute, no secrets in the
   downloader's environment, writes only to data/raw-public/.
10. Retail sites (Wayfair, IKEA, Amazon, Office Depot, etc.) are out of scope (ADR 0003).

# 0003: v1 runs on public data; AOI data replaces assumptions when shared

- Status: proposed
- Date: 2026-10-06
- Deciders: team (proposed by Sidd)

## Context
AOI has not shared quotes yet. AOI is a MillerKnoll Certified Dealer. Herman Miller publishes GSA price
books (list prices + GSA discount) as public PDFs. Cushman & Wakefield's 2026 Americas Fit Out Cost Guide
publishes furniture $/sf by market tier. Retail sites (Wayfair, IKEA) are the wrong market and their
terms typically forbid scraping.

## Decision
- v0: square feet x published furniture $/sf band (C&W Tier 3 by default; Omaha/Lincoln not listed).
- v1: seats -> MillerKnoll packages at list price -> discount range -> install/freight % -> range and $/sf.
  Must land inside the v0 band for typical inputs (calibration test).
- All public data follows docs/data-collection-policy.md and carries provenance (URL, retrieved date, SHA-256).
- No retail scraping.
- When AOI shares data under written terms, it lives in data/raw/ (gitignored) and replaces the discount
  range and package prices; the pipeline does not change.

## Consequences
- Estimates are labeled "public-data estimate" in the UI until AOI data is in.
- Discount is the largest uncertainty; the UI shows it as a range, never a point.

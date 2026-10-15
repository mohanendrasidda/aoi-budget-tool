# Public data register and plan forward

What public data exists for the estimator, what we collected, what is public but could not be
downloaded automatically, where the security work will go, and the plan to a working, accurate
product. Research checked 2026-10-14. Collection rules: [data-collection-policy.md](data-collection-policy.md).

**Key rule:** "publicly visible" is not the same as "allowed to automate". We check robots.txt
**and** the site's terms of use, and we never get around a login, a bot check or a block. When a
source says no, we use the "Allowed route" instead.

Contents: [1. Collected](#1-collected-in-datapublic) ·
[2. Public but not auto-downloaded](#2-public-but-not-auto-downloaded) ·
[3. Backlog](#3-public-allowed-not-yet-collected-backlog) ·
[4. What the data tells us](#4-what-the-data-already-tells-us) ·
[5. Security notes (later)](#5-security-notes-implement-later) ·
[6. Plan forward](#6-plan-forward)

## 1. Collected (in `data/public/`)

Every value was read by a person or research agent and entered by hand with its URL and retrieval
date. The only scripted download is the FRED index (an official CSV endpoint).

| Source | What we took | File |
|---|---|---|
| [Cushman & Wakefield Fit Out Cost Guide, Americas 2026, pp. 42-43](https://digital.cushmanwakefield.com/fitoutcostguide-03-2026-amer-regional-en-content-pds-office/42-43/) | Furniture $/sf bands, Tier 1-3 (as of Dec 2025) | `benchmarks.csv` |
| [GSA Workspace Benchmark 2012 (Missouri copy)](https://distributedteams.mo.gov/wp-content/uploads/2020/10/Workplace-Utilization-and-Allocation-Benchmark-review.pdf) | 200 USF = 230 RSF per person; office and room sizes | `benchmarks.csv` |
| [Herman Miller GSA price books](https://www.hermanmiller.com/solutions/government/us-federal-government/gsa-price-books/) | Government discount % by product line (3 PDFs read by hand) | `benchmarks.csv` |
| [Steelcase NASPO Missouri schedule](https://steelcase.com/resources/documents/naspo-state-of-missouri-discount-schedule) | Category discounts by order size | `benchmarks.csv` |
| [Nebraska DAS contract 15378 OC](https://das.nebraska.gov/materiel/purchasing/contracts/pdfs/15378(oc)awd.pdf) | Same-manufacturer government vs commercial discounts | `benchmarks.csv` |
| [US Air Force Furniture Cost Estimating Guide](https://www.wbdg.org/FFC/AF/AFCFS/AF-Furniture-Cost-Estimating-Guide.pdf) | Freight 6%, install 13%, handling 5% | `benchmarks.csv` |
| [FRED PPI PCU337214337214](https://fred.stlouisfed.org/series/PCU337214337214) | Office furniture price index, 2018-2026 | `ppi_office_furniture.csv` |
| [Nebraska Dept. of Revenue rates](https://revenue.nebraska.gov/businesses/local-sales-and-use-tax-rates) | State 5.5%; Lincoln 7.25%; Omaha 7.0% (city rates to re-check) | `benchmarks.csv` |
| [NU Regents agendas](https://nebraska.edu/regents/agendas-minutes) | 5 projects: 1 furniture award + 4 budget lines | `eval_projects.csv` |
| [LebTown (Palmyra SD)](https://lebtown.com/2026/09/08/palmyra-area-school-district-one-step-closer-to-moving-to-new-admin-offices/), [Des Moines council](https://councildocs.dsm.city/communications/2025/25-265.pdf), [Manassas Park staff report](https://cms7files.revize.com/manassasparkva/Agenda%20Item%20-%20OCM_City%20Hall%20Furniture%20and%20IT%20Purchase.pdf) | 3 more evaluation projects | `eval_projects.csv` |

## 2. Public but not auto-downloaded

Every company and source the research could not (or may not) download automatically, grouped by
the reason.

### 2a. Terms of use forbid automated download

| Company / source | What is there | Detail | Allowed route |
|---|---|---|---|
| **Herman Miller** commercial price books (48 live codes, eff. Apr 6, 2026) | List prices by product line and material grade | robots.txt allows `/content/dam/.../pricing/`, but the [Terms of Use](https://www.hermanmiller.com/legal/terms-of-use/) ban "spiders, robots, data mining... to catalog, download" | Download by hand, one at a time; MillerKnoll written permission; or the dealer's own copies once partner data is approved |
| **Herman Miller** GSA price books (53 in the index) | GSA list + discount by line | Same Terms of Use; only 3 read by hand so far | Same as above |
| **Herman Miller specIT** (HM + Geiger, monthly, history to 2011) | Most structured list-price data | Windows installer, proprietary format; same Terms of Use | Dealer channel; parsing unverified |
| **Knoll** (24 commercial + 16 GSA lists) | Knoll list prices and GSA discounts | Terms of Use bar derivative works; PDF host also blocks crawlers (2b) | Dealer channel or written permission |

### 2b. robots.txt blocks crawlers

| Company / source | What is there | Detail | Allowed route |
|---|---|---|---|
| **Knoll** PDF host `library.hermanmiller.group` | All Knoll price-list PDFs; edition dates unread | `User-agent: * Disallow: /` | Dealer channel or written permission |
| **OMNIA Partners** (MillerKnoll, DIRTT and others) | Cooperative contract pricing | Disallows ClaudeBot, GPTBot, CCBot site-wide; allows user-initiated agents | A person browses by hand |
| **GSA eLibrary** (Steelcase, Haworth, HNI/Allsteel, Kimball, Teknion, Global, OFS, KI GSA price lists) | Federal price lists and discounts, SIN 33721 | `/ElibMain/` disallowed. The `gsaadvantage.gov/ref_text/` PDFs are allowed but none were opened | Browse eLibrary by hand, then fetch the ref_text PDF |
| **KI** (ki.com) | Price lists | Disallows `/*.aspx$` and the document library; also blocks scripts (2c) | NE DAS 6904 OF KI bid sheet (public) |
| **nebraska.edu** `/archive/` | Older Regents agendas | Disallowed on the main host | Use the `docs.nebraska.edu` copies (allowed) |

### 2c. Bot protection (scripts blocked)

| Company / source | What is there | Detail | Allowed route |
|---|---|---|---|
| **HON** (hon.com/price-lists) | Price list page | Incapsula blocks scripts | HON List Pricer on HNI's public CDN (May 2026, 620 pages) |
| **Allsteel** (allsteeloffice.com/price-lists) | Price lists, contents unverified | Incapsula | Public contract documents; never go around the block (for example via the CDN) without permission |
| **Gunlocke** (gunlocke.com/price-lists) | Price lists, contents unverified | Incapsula | Same as Allsteel |
| **KI** | Price lists | HTTP 403 to scripts | NE DAS KI bid sheet; a person checks in a browser |
| **citizenportal.ai** | Council vote summaries: La Porte TX, Dothan AL, Republic MO, Harrisville UT, Story County IA | Cloudflare 403 | Discovery only; find and cite each city's own record |
| **University of Illinois** capital projects furniture/AV process PDF | FF&E rules | HTTP 403 | Manual |

### 2d. Login required

| Company / source | What is there | Allowed route |
|---|---|---|
| **Steelcase** | No public price list (`/resources/price-lists/` 404) | NASPO / Sourcewell / GSA contract PDFs |
| **Teknion** | "Price & Product Guides" pricing module (login) | GSA eLibrary |
| **Global Furniture Group** | `/price-lists` page has a login form | GSA eLibrary |
| **OFS** (also First Office, Carolina) | Configurator with prices (login); `/price-lists` 404 | GSA eLibrary |
| **CBRE, JLL** US city cost tables | Furniture $/sf by city | Often behind a form; request by hand |
| **RSMeans / Gordian** | Cost data | Paid subscription |

### 2e. Gone (404) or unreachable

| Company / source | Detail | Allowed route |
|---|---|---|
| **Geiger** pricebooks | Old URLs 404; only a stale Jan 2020 lounge PDF remains | specIT via the dealer |
| **Herman Miller** codes EAG, GIS and `_10day` variants | 404 at the commercial path (10-day books live in their own folder) | Manual |
| **Haworth** Sourcewell discount document | 404; figures (41% / 57% / 74%) seen only in a search snippet | Find the current Sourcewell document |
| **Montana** NASPO furniture discount PDFs (Steelcase file) | 404 | Check the Montana index page by hand |
| **GSA 2012 benchmark** original on gsa.gov | 404 | Wayback Machine copy |
| **Nebraska DOR** Oct 2026 rate card PDF | Redirects and an expired certificate | Re-check by hand; confirm how freight is taxed |
| **geigerfurniture.com, millerknoll.com** robots.txt | Returned HTML 404s | Treat as unknown; manual only |
| **cbs-ergonomics.com** | Did not respond | Retry by hand |

### 2f. No public pricing found

| Company | Detail | Allowed route |
|---|---|---|
| **DIRTT** | Prices per project in its ICE software; robots allows all | Dealer quotes once partner data is approved |
| **Magis** | robots allows all; sitemap not yet searched | Search the sitemap by hand |
| **NaughtOne** | Resource portal has brochures and specs, no price list; crawl-delay 60 | Dealer channel |
| **HAY, Muuto** | No US contract price list found (only robots.txt checked) | Dealer channel |
| **BIRSCH, Trendway, Watson** | No price list found; Trendway and Watson `/price-lists` 404 | GSA eLibrary |
| **Commercial sales-practice disclosures** for MillerKnoll and Steelcase | GSA keeps them in the contract file | Not available; Neutral Posture's is public only because Nebraska attached it |

### 2g. Found but not opened yet (allowed; time ran out)

| Source | Why it matters |
|---|---|
| [NASPO MillerKnoll MA3967](https://www.naspovaluepoint.org/portfolio/office-furniture-and-related-services-2023-2028/millerknoll-inc/) price list | MillerKnoll cooperative pricing |
| MillerKnoll Sourcewell and OMNIA discount tables | Commercial-like discount ladder |
| Iowa, Kansas, Minnesota, Colorado, South Dakota MillerKnoll discount tables; [SD BOA furniture page](https://boa.sd.gov/central-services/procurement-management/procurement-management-systemOfficeFurniture.aspx) | Midwest cooperative discounts |
| LA County ISD Herman Miller discounts (search snippet only) | Another public discount ladder |
| UNL BRB Phase 3 equipment line | Cost table is an image, so text extraction failed; read by hand |
| City hall square footage for Manassas Park, La Porte, Dothan, Republic, Harrisville | Would turn totals into $/sf evaluation rows |
| Terms of use for Kimball, HON, AIS, Humanscale, Haworth, Friant, 9to5, Sitmatic, citizenportal.ai, withpavilion.com, businessrecord.com | Must be read before any repeat downloads |

## 3. Public, allowed, not yet collected (backlog)

| Priority | Source | Why it matters | How |
|---|---|---|---|
| 1 | NU Regents "Bids and Contracts" tables and quarterly capital reports, 2015-2026 | Could raise scorable projects from 2 to roughly 10-20 | Polite scripted parse (`pdftotext -layout` + regex) on `docs.nebraska.edu` |
| 2 | Lincoln/Lancaster County clerk, Lincoln Public Schools, Omaha Public Schools (BoardBook) packets | Local projects with totals and building size | Manual portal search |
| 3 | Kimball/National, HON pricer, AIS, Humanscale, Haworth Ancillary, Friant, 9to5, Sitmatic price books | List prices for the item-by-item estimator | Read each site's terms first; Humanscale crawl-delay 5 s |
| 4 | Section 2g items | Discounts and more evaluation rows | Manual |
| 5 | C&W methodology note (area basis, what "furniture" includes); AF guide Nebraska location factor | Explains the gap between public awards and the C&W band | Manual |

## 4. What the data already tells us

- Public awards run about $11-15/sf; the C&W Tier 3 band is $23-35/sf. Discount depth (public
  buyers pay roughly 25-40% of list), area basis (gross vs usable) and furniture reuse explain
  most of the gap. Run `uv run python -m aoi_budget.evaluate` for current scores.
- After escalation to today's prices, the one per-seat record (Manassas Park, 2021) sits **above**
  the C&W band while whole-building awards sit below it. More projects are needed before choosing
  between per-seat and per-sq-ft pricing.
- Discounts vary far more by product category (20-35 points) than by order size (1-5 points), so
  the estimator should key discount on category first.

## 5. Security notes (implement later)

Recorded here so nothing is lost. Product and accuracy come first; each item is built when its
feature is built, not before. Already in place: secret scanning (local + CI), branch ruleset,
CODEOWNERS, SHA-pinned Actions and hooks, Dependabot.

| Item | Where it goes | When |
|---|---|---|
| Collector rules: check robots.txt + terms before each host, rate limit and crawl-delay, identify the bot, never bypass a block | `src/aoi_budget/collect/` (new), rules 1-7 of the collection policy | With the NU Regents collector / #11 |
| Downloaded files are untrusted: parse with a library, never execute, size limits, write only to `data/raw-public/`, SHA-256 manifest | Same module + `data/raw-public/MANIFEST` | With #11 |
| Parsed rows pass schema validation; random 5% compared against the PDF text | `src/aoi_budget/parse/` + tests | With #13 |
| Seller-notes AI step: output must pass a pydantic schema; AI never sets a price; prompt-injection tests | `src/aoi_budget/intake.py` + `tests/test_intake_injection.py` | With #16 |
| API key for the AI step from environment only (`.env`, never committed) | `.env.example` + settings loader | With #16 |
| App: never render user text as HTML (`unsafe_allow_html` stays off); bound all numeric inputs | `app/streamlit_app.py` (bounds exist today) | Ongoing |
| Make `test` a required CI check | Branch ruleset + `scripts/ruleset-main.json` | Right after #8 merges |
| Partner data: approval recorded first; transcripts redacted before any processing | ADR 0004 (#9), redaction tool (#18) | After approval |

## 6. Plan forward

**Goal:** a working tool that gives an AOI seller a sourced budget range in minutes, with
measured accuracy. Dates: demo **Thu 2026-10-29**, code freeze **2026-11-30**, final presentation
week of **2026-12-07**.

### Accuracy targets (proposed)

Measured on headline projects (awarded, furniture-only contracts) with `aoi_budget.evaluate`:

| Metric | Today (public data) | Target for the final |
|---|---|---|
| Headline projects scored | 2 | 10 or more |
| Coverage (actual inside the range) | 50% adjusted | 80% or more |
| Median abs error of the midpoint | 26% adjusted | 20% or less |
| Median range width | 40% | 40% or less (a range that is too wide is not useful) |

### Steps

| Phase | When | Work | Issue | Owner |
|---|---|---|---|---|
| **1. Merge what is built** | Now | Merge #8 (stack), then the estimator + evaluation PR, then the prototype PR | #8, #10, #14, #15 | Sidd (review: Anas, Sam) |
| **2. More real projects** | Now to 10-21 | NU Regents collector (2015-2026) + Lincoln/LPS/OPS manual search; tag each row; target 10+ headline projects | new | Sidd + Claude |
| **3. Fix what the scores show** | 10-19 to 10-23 | Seat-based estimate next to the $/sf estimate (workstations, offices, meeting rooms x public unit costs) to settle the per-seat vs per-sq-ft gap; re-score | #14 | Sam (review), Claude |
| **4. Demo UI** | 10-20 to 10-27 | Move the prototype flow (space program, questions for the client, client summary, seller notes) onto the tested estimator; v0/v1 toggle | #16 | Harshi (pending access), Claude |
| **5. Demo** | 10-29 | Script: one scenario end to end, the accuracy tab, what partner data will change | #17 | Sidd |
| **6. Item-by-item estimator (v1)** | November | Price books collected by allowed routes only (section 2/3), parser + spot-check, discount by category; score v1 vs v0 | #11, #13 | Colby |
| **7. Partner data** | After approval | Hash-match, ingest, swap in real discounts and tiers, calibrate on real quotes; compare against a general chatbot estimate | #9, #12, #18-#21 | Team |
| **8. Freeze and present** | 11-30 / week of 12-07 | Final scores, docs, presentation | — | Team |

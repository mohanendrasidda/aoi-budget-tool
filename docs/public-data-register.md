# Public data register

What public data exists for the estimator, what we collected, and what is public but we did not
(or may not) collect automatically. Checked 2026-10-14 unless noted. Rules:
[data-collection-policy.md](data-collection-policy.md).

**Key rule:** "publicly visible" is not the same as "allowed to automate". We check robots.txt
**and** the site's terms of use, and we never get around a login, a bot check or a block. If a
source says no, we use the route in the "Allowed route" column instead.

## 1. Collected (in `data/public/`)

Every value was read by a person or research agent and entered by hand with its URL and retrieval
date. Nothing below was bulk-downloaded by a script except the FRED index (an official CSV
endpoint).

| Source | What we took | File |
|---|---|---|
| [Cushman & Wakefield Fit Out Cost Guide, Americas 2026, pp. 42-43](https://digital.cushmanwakefield.com/fitoutcostguide-03-2026-amer-regional-en-content-pds-office/42-43/) | Furniture $/sf bands, Tier 1-3 (as of Dec 2025) | `benchmarks.csv` |
| [GSA Workspace Benchmark 2012 (Missouri copy)](https://distributedteams.mo.gov/wp-content/uploads/2020/10/Workplace-Utilization-and-Allocation-Benchmark-review.pdf) | 200 USF = 230 RSF per person; office and room sizes | `benchmarks.csv` |
| [Herman Miller GSA price books](https://www.hermanmiller.com/solutions/government/us-federal-government/gsa-price-books/) | Government discount % by product line (read by hand) | `benchmarks.csv` |
| [Steelcase NASPO Missouri schedule](https://steelcase.com/resources/documents/naspo-state-of-missouri-discount-schedule) | Category discounts by order size | `benchmarks.csv` |
| [Nebraska DAS contract 15378 OC](https://das.nebraska.gov/materiel/purchasing/contracts/pdfs/15378(oc)awd.pdf) | Same-manufacturer government vs commercial discounts | `benchmarks.csv` |
| [US Air Force Furniture Cost Estimating Guide](https://www.wbdg.org/FFC/AF/AFCFS/AF-Furniture-Cost-Estimating-Guide.pdf) | Freight 6%, install 13%, handling 5% | `benchmarks.csv` |
| [FRED PPI PCU337214337214](https://fred.stlouisfed.org/series/PCU337214337214) | Office furniture price index, 2018-2026 | `ppi_office_furniture.csv` |
| [Nebraska Dept. of Revenue rates](https://revenue.nebraska.gov/businesses/local-sales-and-use-tax-rates) | State 5.5%; Lincoln 7.25%; Omaha 7.0% (city rates to re-check) | `benchmarks.csv` |
| [NU Regents agendas](https://nebraska.edu/regents/agendas-minutes) | 5 projects: 1 furniture award + 4 budget lines | `eval_projects.csv` |
| [LebTown (Palmyra SD)](https://lebtown.com/2026/09/08/palmyra-area-school-district-one-step-closer-to-moving-to-new-admin-offices/), [Des Moines council](https://councildocs.dsm.city/communications/2025/25-265.pdf), [Manassas Park staff report](https://cms7files.revize.com/manassasparkva/Agenda%20Item%20-%20OCM_City%20Hall%20Furniture%20and%20IT%20Purchase.pdf) | 3 more evaluation projects | `eval_projects.csv` |

## 2. Public, but not collected automatically

| Source | What is there | Why we did not automate it | Allowed route | Issue |
|---|---|---|---|---|
| [Herman Miller commercial price books](https://www.hermanmiller.com/content/dam/hermanmiller/documents/pricing/PB_AOS.pdf) (48 live, eff. Apr 6, 2026) | List prices by product line and material grade | robots.txt allows the path, but the [Terms of Use](https://www.hermanmiller.com/legal/terms-of-use/) ban "spiders, robots, data mining... to catalog, download" | Download by hand, one at a time; or ask MillerKnoll in writing; or the dealer's own copies once partner data is approved | #11, #13 |
| [Herman Miller specIT](https://www.hermanmiller.com/support/specit/) | HM + Geiger list prices, monthly, history to 2011 | Windows installer, proprietary format; same Terms of Use | Dealer channel; parsing unverified | #13 |
| [Knoll price lists](https://www.knoll.com/design-plan/resources/price-lists) (24 commercial, 16 GSA) | Knoll list prices and GSA discounts | PDF host `library.hermanmiller.group` has `Disallow: /` for all crawlers | Dealer channel or written permission | #13 |
| Geiger current pricebooks | List prices | Old URLs return 404; only a Jan 2020 lounge book is online (stale) | specIT via the dealer | #13 |
| [OMNIA Partners](https://www.omniapartners.com/robots.txt) (MillerKnoll, DIRTT) | Cooperative contract discounts | robots.txt blocks AI crawlers | A person browses it by hand | — |
| Allsteel, Gunlocke, KI websites | Price lists | Bot protection (Incapsula / 403 to scripts) | Use public contract copies instead, e.g. [NE DAS KI bid sheet](https://das.nebraska.gov/materiel/purchasing/6904OF/6904%20OF%20Krueger%20International%20Bid%20Sheet%20TO%20POST.pdf); never bypass the protection | — |
| Steelcase, Teknion, Global, OFS price lists | List prices | Login required | Public contract documents only | — |
| [GSA eLibrary](https://www.gsaelibrary.gsa.gov/) (Steelcase, Haworth, HNI GSA lists) | Federal price lists and discounts | `/ElibMain/` is disallowed in robots.txt | Browse by hand | — |
| citizenportal.ai | Summaries of city council furniture votes (La Porte TX, Dothan AL, Republic MO, Harrisville UT, Story County IA) | Cloudflare 403 to scripts | Use only to find the city's own record, then cite the city | — |
| [Haworth Sourcewell discounts](https://files.sourcewell.org/public/Shared%20Documents/Solicitations/091423-10745/091423-HAWRT/Additional%20Documents/90705%20SOURCEWELL%20ss%20Customer%20Discounts%20Only.pdf) | Category discounts | Link returns 404; figures seen only in a search snippet (unverified) | Find the current Sourcewell document | — |
| [GSA 2012 benchmark original](https://www.gsa.gov/) | Original of the 200 USF figure | gsa.gov file returns 404 | Wayback Machine copy | — |
| DIRTT, Magis | — | No public pricing exists (DIRTT prices per project in its ICE software) | Dealer quotes only, once partner data is approved | #19 |

## 3. Public, allowed, not yet collected (backlog)

| Priority | Source | Why it matters | How |
|---|---|---|---|
| 1 | NU Regents "Bids and Contracts" tables and quarterly capital reports, 2015-2026 | Could raise scorable projects from 2 to roughly 10-20 | Polite scripted parse (`pdftotext -layout` + regex); nebraska.edu disallows only `/archive/`, docs host has no robots.txt |
| 2 | Lincoln/Lancaster County clerk, Lincoln Public Schools, Omaha Public Schools board packets | Local projects with totals and building size | Manual portal search |
| 3 | Kimball/National, HON pricer, AIS, Humanscale, Haworth Ancillary, Friant, 9to5, Sitmatic price books | List prices for the item-by-item estimator | Read each site's terms first; Humanscale asks a 5 s crawl delay |
| 4 | NASPO MillerKnoll MA3967 price list | MillerKnoll cooperative pricing | Manual download (robots allows) |
| 5 | C&W methodology note (area basis, what "furniture" includes); AF guide Nebraska location factor | Explains the gap between public awards and the C&W band | Manual |

## What the data already tells us

- Public awards run about $11-15/sf; the C&W Tier 3 band is $23-35/sf. Discount depth (public
  buyers pay roughly 25-40% of list), area basis (gross vs usable) and furniture reuse explain
  most of the gap. Run `uv run python -m aoi_budget.evaluate` for the current scores.
- After escalation to today's prices, the one per-seat record (Manassas Park, 2021) sits **above**
  the C&W band, while whole-building awards sit below it. Per-seat and per-building evidence
  disagree; more projects are needed before choosing one.
- Discounts vary far more by product category (20-35 points) than by order size (1-5 points), so
  the estimator should key discount on category first.

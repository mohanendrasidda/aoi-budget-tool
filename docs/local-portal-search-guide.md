# Local portal search guide (manual, about 2 hours)

**Goal:** find Lincoln / Omaha / Nebraska public furniture purchases that state **both** a dollar
amount **and** a floor area (or a seat/workstation count). Each one becomes an evaluation project
in `data/public/eval_projects.csv`, which is how we measure the estimator's accuracy. Today only 2
projects count toward the headline score; the target is 10 or more.

**Why a person:** the best local sources (City of Lincoln / Lancaster County clerk, BoardBook
packets) block automated access with Cloudflare or session checks. A person using a normal
browser is fine. Do **not** use scripts, scrapers or browser automation on these sites.

## 1. What counts

| Keep | Skip |
|---|---|
| Awarded contract, PO or approved bid for furniture for a **named** building or floor | Annual supply contracts with no named project |
| Office, admin, academic or library space | Athletics, residence halls, lab or medical equipment buys |
| Amount + area (sf) in the same record, or area in a second public document | Amount only, with no area or seat count anywhere |
| Amount + number of workstations / seats | Retail purchases |

Budgets (program statements, "FF&E budget") are still useful, but mark them `budget`.

## 2. Where to look (in this order)

| # | Portal | How to search | Known leads to check first |
|---|---|---|---|
| 1 | City of Lincoln / Lancaster County clerk agendas: `app.lincoln.ne.gov/cnty/clerk/agenda/` | Browse by year; use the browser's find (Cmd+F) for "furniture" | Lancaster County Sheriff's Office furniture bid 19-167 (Office Interiors & Design); Haworth and Teknion county contracts (skip if annual supply) |
| 2 | Lincoln Public Schools board packets (district board page) | Search "furniture", "FF&E", "workstations" | District office or new school furniture awards |
| 3 | BoardBook (`meetings.boardbook.org`) for Nebraska districts | Open packets from the meeting page (direct PDF links fail) | "Lincoln Hall Phase III furniture" packet |
| 4 | City of Omaha, Douglas County, Omaha Public Schools, Millard, Elkhorn, Papillion-La Vista boards | Same search terms | New admin buildings or office moves |
| 5 | Southeast Community College, Metropolitan Community College board minutes | Same search terms | Campus office or classroom furniture awards |
| 6 | Nebraska DAS (`das.nebraska.gov/materiel/purchasing/`) intent-to-award pages | Search a building name | State office consolidation at 245 Fallbrook Blvd, Lincoln (the director's note PDF is a scanned image: read it by eye) |

**Search phrases that worked elsewhere:** `"furniture" "not to exceed"`, `"systems furniture"`,
`"workstations"`, `"Furniture & Equipment"`, `"FF&E budget"`.

**Finding the area when the record has none:** search `<building name> square feet` and prefer
the architect's or contractor's project page, an earlier construction agenda item, or a lease memo.

## 3. How to record a find

Add one row per project (or send the details in a comment on the PR/issue and we will add it):

| Column | Example / rule |
|---|---|
| `id` | short slug: `lps-district-office` |
| `name` | building / project name |
| `year` | year of the award |
| `state` | `NE` |
| `segment` | `office`, `academic` or `library` |
| `buyer` | `public` |
| `evidence` | `contract` (awarded) or `budget` |
| `scope` | `furniture_only`, `ffe_mixed` (includes AV/IT/equipment) or `reuse_heavy` (mostly reused furniture) |
| `area_sf` + `area_basis` | number + `GSF`, `NSF`, `RSF`, `USF` or `building_sf`; leave blank if only seats are known |
| `seats` | workstations or seats, if stated |
| `actual_usd` | the furniture amount, no `$` or commas |
| `source_url` | the exact document link (add the area link in `notes` if separate) |
| `retrieved_at` | today's date, `YYYY-MM-DD` |
| `notes` | anything that limits the comparison ("includes install", "partly reused", "area from news article") |

Then run `uv run python -m aoi_budget.evaluate` to see the new row scored.

## 4. Rules

- Public bodies and companies only. **Never record a person's name, email or phone.**
- Never guess a number. If a figure appears only in a search-result snippet, write "snippet only" in `notes`.
- If a site blocks you or asks for a login, stop and note it; do not try to get around it.
- Time box: about 2 hours. Even 3 to 5 good records is a big improvement.

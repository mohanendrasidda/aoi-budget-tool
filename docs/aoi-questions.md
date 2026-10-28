# Questions for the partner (draft for team review)

Status: **draft, not sent.** Teammates: please comment on the PR. Is each question clear? Should
any be dropped? Is anything missing? The email version at the bottom goes to the partner after
review.

Why we ask: the public data takes the estimate to about 15% median error on 4 projects, and the
best any estimate can do is about 9% (public bid tabs, `docs/accuracy-target.md`). Closing the gap
needs real outcomes, which only the partner has.

## The questions, by priority

| # | Question | What it fixes | Minimum useful answer |
|---|---|---|---|
| 1 | Final furniture totals for closed projects, ideally split into product, freight/delivery, installation and design fees | Accuracy can be measured for the first time | 3-5 projects (10-20 ideal) |
| 2 | For those projects: usable sq ft and counts of workstations, private offices and conference rooms (or a floor plan) | Area and seat inputs | Same projects as #1 |
| 3 | Year ordered, and commercial or public buyer | Price-year and buyer adjustment | One line per project |
| 4 | Totals for public case studies we already have inputs for (FNBO Tower, Methodist corporate office, Centris, SAC Federal Credit Union, Kiewit, Pillen Family Farms, Q2) | Scores our 15 estimates that were frozen before seeing any total | Totals alone |
| 5 | The typical open-plan workstation: product line, size, and what it includes (storage, overhead, power) | Biggest single unknown in the item-by-item estimate | One example |
| 6 | Rough share of furniture sales by brand: Herman Miller, Knoll, other MillerKnoll brands, DIRTT, outside brands; and for workstations specifically | Tells us if Knoll pricing changes the estimate enough to matter (it could move an all-Knoll estimate by up to 30 points) | Rough percentages |
| 7 | If Knoll is a large share: the Knoll price books for workstation and seating lines | Knoll list prices are not readable by our tools from public sources | Only if #6 says Knoll matters |
| 8 | Line-item order or quote exports (for example SIF or CET): manufacturer, item, quantity, list, discount, sell | Splits each miss into quantity vs price vs discount | 1-2 projects |
| 9 | Are DIRTT walls usually part of the furniture budget the client sees, or a separate line or contract? | Confirms ADR 0005 (walls shown separately) | Yes/no |
| 10 | For the senior living project in the shared folder: the final quote total | Compares a real quote with the AI-generated budget in the same file | One number |

## Email version (for review before sending)

> Subject: A few past projects to check the budget tool against
>
> Hi Penny,
>
> Thank you again for approving the use of the materials you shared. They have already helped:
> the price books let us build an item-by-item check behind the budget range.
>
> The part we can't do on our own is test the tool against what projects actually cost. We'd
> find a small set of closed projects very helpful. For each, whichever of these is easy to pull:
>
> 1. The final furniture total, ideally split into product, freight and delivery, installation,
>    and design fees.
> 2. The usable square footage and the counts of workstations, private offices and conference
>    rooms, or a floor plan we can count from.
> 3. The year the order was placed and whether the client was commercial or public.
> 4. If easy, the line-item order or quote export (for example SIF or CET).
>
> Three to five projects would let us measure accuracy for the first time; ten to twenty would be
> ideal. For FNBO Tower, Methodist corporate office, Centris, SAC Federal Credit Union, Kiewit,
> Pillen Family Farms and Q2, we already have square footage and headcounts from your website, so
> the totals alone would be enough. We recorded and locked our tool's estimates for these first,
> so the comparison is a fair test.
>
> A few smaller questions would also help:
>
> - Your typical open-plan workstation: product line, size, and what it usually includes. This
>   is the biggest single unknown in our numbers.
> - A rough split of furniture sales by brand (Herman Miller, Knoll, other MillerKnoll brands,
>   DIRTT, outside brands), and for workstations if it differs. If Knoll is a large share, the
>   Knoll price books for workstations and seating would help a lot.
> - Whether DIRTT walls are usually part of the furniture budget the client sees, or a separate
>   line.
> - For the senior living project in the folder, the final quote total, so we can compare it
>   with the AI-generated budget in the same file.
>
> Everything stays on one laptop, is used only for this project, and client names are removed
> before any processing. Nothing with your numbers goes into the shared code.
>
> If it is easier to walk through a couple of projects together, we can come to you at a time
> that works.
>
> Mohanendra Siddha
> ENGR 491, Team AOI

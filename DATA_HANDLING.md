# Data Handling

Four words people use interchangeably. They mean different things, and each one gets a different control.

| Term | Question it answers | Protects | Example in this project | Control |
|---|---|---|---|---|
| **Privacy** | Should we collect or use information about a *person* at all? | People (clients, AOI staff, us) | An end client's name or contact info on a real AOI quote | Don't collect it. Strip names before anything touches the repo. |
| **Confidentiality** | Who is allowed to *see* this information? | The information owner (AOI) | AOI's dealer discounts, margins, vendor pricing | Classify it (below), keep it in approved places only |
| **Security** | How do we stop the system and data from being *compromised*? | Systems + data | A leaked LLM API key, an injectable input field, a vulnerable dependency | Secret scanning, reviews, least privilege, dependency alerts |
| **Authorization** | Once we know *who* you are, what are you *allowed to do*? | Resources | Only the admin can change branch rules; only you can push to your branch | Repo roles, branch protection, app role checks |

Authentication is the fifth one people mix in: it answers *who are you* (login, 2FA, SSH key). Authorization comes after it and answers *what can you do*.

Short version: privacy is about **people**, confidentiality is about **who sees**, security is about **not getting broken into**, authorization is about **who can do what**.

## Classification

| Level | What it is | Allowed places | Never |
|---|---|---|---|
| **Public** | Course info, our own generic code, public furniture list prices | Anywhere | |
| **Team-internal** | Our designs, meeting notes, draft estimates, synthetic data | This repo, Teams | Public repos, personal social posts |
| **AOI-confidential** | Anything AOI shares: real quotes, discounts, margins, internal process docs, Landon's walkthrough numbers | `data/raw/` locally (gitignored); shared only as the team agrees with the repo admin. Repo only if AOI agrees in writing, and then only aggregated or anonymized | Commits (by default), Teams chat, personal LLM accounts, screenshots in public places |
| **Personal (PII)** | Names, emails, phone numbers, addresses of AOI's end clients | Nowhere. We don't need it. | Everywhere |

When unsure, treat it as the stricter level and ask in the Teams **#security** channel.

## AI tools

AI tools are data processors. Pasting something into a chat is sharing it with that vendor under that account's terms.

- **OK in any AI tool:** Public and Team-internal data, our own code.
- **AOI-confidential:** only after the team has confirmed with AOI (and Chad/Mark) which tools are acceptable. Until then, use synthetic data with the same shape.
- **PII:** never.
- Commercial or education accounts often have different retention and training terms than free personal accounts. Check before you paste.

## Synthetic data first

Until AOI shares data under clear terms, build and test against a synthetic dataset in `data/synthetic/` (committed). Real data goes in `data/raw/` (gitignored, never committed).

## If something leaks

Follow [SECURITY.md](SECURITY.md). Speed matters more than blame.

# AOI Budget Tool (ENGR 491 Applied AI, Fall 2026)

Pre-design budget-range tool for AOI furniture sellers. During the first client conversation, before a designer specs anything in CET/CAP/Core, a seller enters scope and square footage and gets back a budget range and a price per square foot.

**Private repository.** This repo may later contain information AOI considers confidential. Do not fork it, mirror it, make it public, or paste its contents into tools outside the approved list in [DATA_HANDLING.md](DATA_HANDLING.md).

## Team

| Name | GitHub | Role |
|---|---|---|
| Mohanendra (Sidd) Siddha | `@mohanendrasidda` | Repo admin |
| Mohammed Anas | `@TODO` | |
| Colby Jochum | `@TODO` | |
| Sam Sanketh | `@TODO` | |
| Harshi Vallabhaneni | `@TODO` | |

Partner contacts (AOI Lincoln): Penny Johnston, Curtis Yount. Instructors: Chad Michel, Mark Stone.

## Read before your first commit

1. [CONTRIBUTING.md](CONTRIBUTING.md): branch, commit, and PR rules
2. [DATA_HANDLING.md](DATA_HANDLING.md): what data can go where (including into AI tools)
3. [SECURITY.md](SECURITY.md): how to report a leaked secret or a vulnerability
4. [CLAUDE.md](CLAUDE.md): rules our AI coding agents follow in this repo

## First-time setup

```bash
git clone git@github.com:<owner>/aoi-budget-tool.git
cd aoi-budget-tool
./scripts/setup-dev.sh        # installs pre-commit hooks incl. secret scanning
cp .env.example .env          # fill in locally; .env is never committed
```

## Where things live

| What | Where |
|---|---|
| Code, tests, ADRs | this repo |
| Tasks | GitHub Issues |
| Decisions | `docs/decisions/` (ADRs) |
| Day-to-day chat | Microsoft Teams: "AOI Budget Tool" team |
| Secrets (API keys) | each person's local `.env` + GitHub Actions secrets. Never Teams, commits, or screenshots |

## Architecture decisions

Recorded as short ADRs in [docs/decisions/](docs/decisions/). Stack is **not decided yet** (see ADR 0001).

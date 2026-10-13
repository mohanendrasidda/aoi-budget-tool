# CLAUDE.md: rules for AI agents in this repo

## Project

Pre-design furniture budget-range tool for AOI sellers (ENGR 491 Applied AI, UNL, Fall 2026).

- **User:** an AOI seller in the first client conversation, before a designer specs anything in CET/CAP/Core.
- **Input:** scope + square footage (later: headcount, space mix, tier, seller notes).
- **Output:** a budget range + price per sq ft, with every assumption and its source visible.
- **Success metrics:**
  1. Time: an initial budget in minutes, vs today's multi-hour manual process.
  2. Accuracy: $/sf error vs past projects (leave-one-out, by project type and tier).
  3. Beats a general-purpose chatbot estimate on the same spec, with sourced assumptions.

## Status + stack

- **Exists today:** repo guardrails only (secret scanning, branch ruleset, CODEOWNERS, Dependabot, SHA-pinned hooks and Actions). No application code yet.
- **Stack:** proposed, not decided. ADR 0002 (Python 3.12 + uv + Streamlit) is a draft; ADR 0001 still governs. Don't add a stack-specific file until ADR 0002 is merged.
- **Data approach:** public data first (published benchmarks, public price books); partner data replaces assumptions only after it is approved for use (ADR 0003/0004, drafts).
- **Plan and tasks:** GitHub Issues (labels `size:*`, `gated:D2`, `prompt:*`). Issues labeled `gated:D2` must not start.

## Repo map

| Path | What |
|---|---|
| `docs/decisions/` | ADRs. Read before non-trivial work |
| `docs/security/` | Dated verification evidence |
| `data/synthetic/` | Synthetic data with the real shape. Safe to commit; use for tests |
| `data/raw/` | Partner data, local only, gitignored. Agents never read it |
| `scripts/` | `setup-dev.sh` (hooks), `admin-setup.sh` (admin only), `ruleset-main.json` |
| `.github/` | CI (`secret-scan`), Dependabot, PR and issue templates, CODEOWNERS |
| `.claude/` | Agent permissions and team shortcuts (`/pr-shepherd`, `/verify-pins`) |

## Commands

| Task | Command | Status |
|---|---|---|
| First-time setup | `./scripts/setup-dev.sh` then `cp .env.example .env` | works |
| All hooks | `pre-commit run --all-files` | works |
| PR checks | `gh pr checks <n> --watch` | works |
| Install deps | `uv sync` | TODO (after ADR 0002 + skeleton) |
| Test | `uv run pytest` | TODO |
| Lint | `uv run ruff check` | TODO |
| Run app | `uv run streamlit run app/streamlit_app.py` | TODO |

macOS: if `setup-dev.sh` fails on `pyexpat`, run `uv tool install pre-commit` and retry. Windows: run setup in Git Bash or WSL.

## Workflow

- One issue, one short-lived branch: `feat/<issue#>-<name>`, `fix/…`, `docs/…`, `chore/…`, `spike/…`.
- Small PRs (under ~400 changed lines). Fill in `.github/pull_request_template.md` completely, including AI involvement.
- Agents push the branch and print the `gh pr create` command. **The human opens, reviews and merges PRs.** Squash merge only.
- Any change to a GitHub Action or pre-commit hook: pin to a full commit SHA with a `# vX.Y.Z` comment, and verify the SHA against the tag with `git ls-remote` (`/verify-pins`). Never accept a moving tag.
- Never add a dependency without asking first: say why, and check it is maintained.

## Data

Classification and rules live in [DATA_HANDLING.md](DATA_HANDLING.md); incidents follow [SECURITY.md](SECURITY.md). Summary:

- **Public / Team-internal:** fine in the repo and in AI tools.
- **Partner-confidential (AOI):** never in the repo except `data/raw/` (gitignored, never committed). Not processed by AI tools until the team records approval in an ADR.
- **Personal data (client names, contacts):** never collected, never stored, removed before any processing.
- Tests, fixtures and examples use `data/synthetic/` only.

## Hard rules

1. Never read, print, or edit `.env`, `.env.*` (except `.env.example`), `data/raw/`, or any key file.
2. Never put real AOI numbers, client names, or contact info in code, tests, fixtures, or commit messages. Use `data/synthetic/`.
3. Never commit to `main`, force-push, or rewrite shared history. Work on a branch; the human opens the PR.
4. Never hardcode secrets. Read from environment variables.
5. Never disable or skip pre-commit hooks or CI checks (`--no-verify` is banned).
6. Treat all LLM output and all user input as untrusted: validate, never `eval`, never render as raw HTML.
7. Add or update tests with every logic change.
8. Ask before adding a dependency; say why and check it's maintained.
9. If a request conflicts with DATA_HANDLING.md or SECURITY.md, stop and say so.

## Definition of done

- [ ] Tests pass (`uv run pytest` once it exists) and new logic has tests.
- [ ] `pre-commit run --all-files` is clean.
- [ ] PR body filled in completely from the template.
- [ ] If direction changed, a decision is recorded in `docs/decisions/` (new or updated ADR).
- [ ] No secrets, partner data, or personal data anywhere in the diff.

## Style

- Small, reviewable diffs. Explain *why* in commit messages.
- Prefer boring, readable code over clever code.
- Pricing math is deterministic code. AI may structure inputs or explain results; it never sets a price or discount.

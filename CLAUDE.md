# CLAUDE.md: rules for AI agents in this repo

## Project

Pre-design furniture budget-range tool for AOI sellers (ENGR 491 Applied AI, UNL, Fall 2026). Inputs: scope + square footage. Output: budget range + price per sq ft. Stack not decided yet (see `docs/decisions/`).

## Project decisions

Read `docs/decisions/` before non-trivial work. Don't contradict an accepted ADR without flagging it.

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

## Style

- Small, reviewable diffs. Explain *why* in commit messages.
- Prefer boring, readable code over clever code.

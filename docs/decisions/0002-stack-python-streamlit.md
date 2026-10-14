# 0002: Stack for v0/v1 is Python 3.12 + uv + Streamlit

- Status: accepted
- Date: 2026-10-06 (accepted 2026-10-14)
- Deciders: team (proposed by Sidd)

## Context
v1 is mostly data work: download public price-book PDFs, parse them into rows, run a deterministic
estimator, show a demo UI to AOI in about three weeks. Five students, mixed OSes (macOS, possibly Windows).
Homebrew Python on some Macs can't load pyexpat; uv-managed Python works.

## Options considered
1. Python + uv + Streamlit: one language end to end, fastest demo UI, strong PDF/data libraries.
2. Next.js/TypeScript + Python backend: nicer UI, two languages, two dependency trees, slower to a demo.
3. Notebook only: fastest to start, not a product AOI can click.

## Decision
Python 3.12, managed by uv (lockfile `uv.lock` committed). Libraries now: pandas, pydantic, pyyaml, streamlit; dev: pytest, ruff.
httpx and pdfplumber are added with the price-book pipeline (#11, #13), not before: fewer
dependencies until they are needed. Pricing logic lives in `src/aoi_budget/` as plain functions with tests;
Streamlit is a thin UI layer in `app/`.

## Consequences
- Dependabot `uv` ecosystem gets enabled (updates pyproject.toml and uv.lock together); uv.lock pins exact versions (supply-chain control).
- Windows teammates use uv too; no Homebrew dependency.
- If AOI later wants a hosted app, Streamlit can be replaced without touching the pricing core.

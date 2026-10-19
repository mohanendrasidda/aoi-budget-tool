# ADR 0004: AOI data handling (D2 accepted)

- **Status:** accepted
- **Date:** 2026-10-19
- **Decider:** Sidd (repo admin), on AOI's approval

## Context

AOI shared price books, government-contract price books, past-project files and meeting
transcripts. The tool so far uses public data only (ADR 0003), and its accuracy is measured on
two public projects. AOI's own prices and outcomes are the best way to validate and calibrate it.
Until now, AOI material stayed unread (decision D2 pending).

## Decision

AOI approved processing of **all** shared AOI material with AI tools, under these conditions:

1. **Project scope only.** Used only to build and evaluate this ENGR 491 tool. Not reused for any
   other project, course, product or publication.
2. **No leaks.** AOI material and anything derived from it (extracted prices, discounts,
   calibration factors, per-project results) stays on the team member's machine:
   - originals in `data/raw/aoi/` (gitignored);
   - derived files in `data/raw/aoi-derived/` (gitignored);
   - code that touches AOI data on a `local/*` branch, blocked from pushing by a local pre-push
     hook. Only code and docs with **no AOI values** may move to a pushable branch.
3. **Personal data removed first.** Client names and contact details (transcripts, spec files)
   are removed before any AI processing, per DATA_HANDLING.md. AOI's approval covers AOI's
   information, not the clients' personal data.
4. **No model training.** The AI account used must not allow training on this data (consumer
   accounts: "Help improve Claude" off; or a Team, Education or API account).
5. **Nothing AOI-specific in repo history, issues, PRs, commit messages or shared notes:** no
   prices, discounts, margins, quote totals, client names or contacts. Counts, file types,
   brand names and pass/fail or error percentages are fine.
6. **Demo:** results shown to AOI may use AOI numbers in a live session; slides or recordings
   shared outside the team use public numbers or aggregate error figures only.

## Consequences

- Unblocks #19 (ingest AOI price data), #21 (AOI discount and tier data), #18 (transcript
  redaction, now required before transcripts are used) and #20 (ChatGPT baseline vs landed number).
- The public-data path stays as the default and as the fallback, so the app still runs for
  anyone without AOI files.
- When the project ends, AOI-derived files are deleted or returned as AOI prefers.

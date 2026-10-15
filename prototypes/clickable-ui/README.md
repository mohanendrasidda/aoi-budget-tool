# Clickable UI prototype (2026-10-13)

A single-file HTML mock of the seller flow: project, space, finish level, then a budget range,
a per-sq-ft range, questions to ask the client, and a client-ready summary. Used to agree on the
flow before building the Streamlit app (#16).

- **Open it:** double-click `index.html`, or `open prototypes/clickable-ui/index.html`. No build step.
- **Data:** public only. Furniture bands from the Cushman & Wakefield 2026 fit-out guide (Tier 3 is
  a labeled proxy for Lincoln/Omaha) and 200 usable sq ft per person from GSA 2012. The finish
  split and private-office shares are labeled assumptions. Same values as `data/public/benchmarks.csv`.
- **Not the estimator.** It prices by area only. The real, tested math lives in `src/aoi_budget/`;
  if the two disagree, the Python code wins.
- **Safety:** user input is written with `textContent`, never `innerHTML`. External request: Google
  Fonts only.

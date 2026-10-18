# Demo script: Thu 2026-10-29 (5 minutes)

**Goal:** show that a seller can get a sourced budget range in minutes, show how honest we are
about accuracy, and agree on what would make it accurate enough to use.

**Setup (before the meeting):** `uv run streamlit run app/streamlit_app.py`, browser at full
width, Estimate tab, default inputs. Have the notes example below ready to paste.

All numbers below are from public data and come straight from the app. Re-run the app the day
before and update them if the data changed.

## 0:00 Today vs the tool (30 s)

- Today, an early budget takes a seller several hours of manual work (4 to 8 hours is the figure
  we were given) before a designer has specified anything.
- The tool's job: a defensible range during the first conversation, with every assumption visible.

## 0:30 Worked example (90 s)

1. Default project: **12,000 sq ft usable, Lincoln / Omaha, New space, Better finish,
   commercial buyer, 2026, Lincoln sales tax.**
2. Point at the result: **$343,092 to $419,364** (about $28.59 to $34.95 per sq ft).
3. Paste the notes and click **Read notes into the form**:
   > Moving to a new office, 15,000 rentable sq ft, 70 people, private-heavy, 6 private
   > offices, 4 conference rooms. High-end finish.
4. Show the review table, then **Apply to form**. The range becomes **$414,586 to $497,531**.
5. Say: the notes only fill the form. They never set a price, and the seller checks every field
   before it is applied. Prices come only from the sourced calculation.
6. Optional: switch Project type to **Refresh** at 25% reuse to show the range drop.

## 2:00 Where every number comes from (60 s)

1. Open **Assumptions and sources**: the published $/sf band, finish placement, price-level
   index, and each adjustment with its source.
2. Toggle **Method** to **Published band only (v0)**: $319,900 to $391,015. Explain that v1 adds
   the sourced adjustments (buyer type, area basis, reuse, add-ons, tax).
3. **What moves it** tab: the biggest swings for this project are buyer pricing, freight and
   install, and finish level. Those are the questions worth asking first.

## 3:00 How accurate it is today (60 s)

- **How accurate** tab. Be direct: only **2** public furniture-only awards with a known area so
  far.
  - Published band alone: 0 of 2 inside the range, about 95% error.
  - Adjusted (v1): 1 of 2 inside, about 26% median error.
  - Calibrated: 2 of 2, but with n = 2 this proves the method works, not the accuracy.
- Our target before anyone relies on it: 10 or more projects, at least 80% inside the range,
  20% or less error.

## 4:00 What would help most (60 s)

Phrase these as what would help us, not as anything missing on AOI's side.

1. **Approval to use the materials already shared** (price books and past examples) in the
   tool, and any conditions on how.
2. **A few past projects** with the final furniture total and square footage, with client names
   removed. These become the accuracy test set.
3. **Typical discount and tier ranges** by manufacturer, so the buyer-pricing assumption reflects
   AOI instead of public contracts.
4. **The landed number for the chatbot example** from kickoff, so we can compare the tool with a
   general-purpose chatbot on the same spec.

## Backup answers

| Question | Answer |
|---|---|
| Why a range, not one number? | Before products are chosen, the honest answer is a range. It narrows as the questions get answered. |
| Where does the band come from? | A published 2026 fit-out cost guide by market tier; Lincoln / Omaha uses the Tier 3 figures as a stand-in. |
| Does the AI see our pricing? | No. Pricing is plain code. The optional AI step reads only the notes, is off by default, and nothing goes to an AI service until that is approved. |
| What if a seller's notes say something odd? | Anything outside the form's fields or ranges is ignored and listed, and nothing applies until the seller clicks Apply. |

"""Streamlit entry point. Run: uv run streamlit run app/streamlit_app.py

Seller flow (#16): project -> space -> finish -> range, questions to ask, client summary,
assumptions, designer hand-off. User text is only ever shown as plain text (st.code / st.text).
"""

import csv

import pandas as pd
import streamlit as st

import aoi_budget
from aoi_budget.book import DATA_DIR, load_book
from aoi_budget.estimator import Inputs, estimate
from aoi_budget.evaluate import evaluate, load_projects, summarize
from aoi_budget.seller import (
    FINISH_LABEL,
    PEOPLE_PER_CONFERENCE,
    PEOPLE_PER_HUDDLE,
    PRIVATE_SHARE,
    PROJECT_TYPES,
    Program,
    client_summary,
    default_headcount,
    handoff_items,
    next_questions,
    space_program,
)
from aoi_budget.sensitivity import tornado

st.set_page_config(page_title="AOI Budget Tool", layout="wide")
book = load_book()
MARKETS = {
    "Lincoln / Omaha (Tier 3 proxy)": "US Tier 3",
    "Tier 2 market": "US Tier 2",
    "Tier 1 market": "US Tier 1",
}
AREA_BASES = {"Usable (USF)": "USF", "Rentable (RSF)": "RSF", "Gross (GSF)": "GSF"}
FINISH_PLACEMENT = {"basic": "lower half", "standard": "middle half", "premium": "upper half"}


@st.cache_data
def _scores():
    scored = evaluate(load_projects(), load_book())
    return scored, summarize(scored)


def _csv(name: str) -> pd.DataFrame:
    with (DATA_DIR / name).open(newline="", encoding="utf-8") as f:
        return pd.DataFrame(list(csv.DictReader(f)))


st.title("AOI Budget Tool")
st.caption(
    f"v{aoi_budget.__version__} · Public-data estimate: every number comes from a published "
    "source or a labeled assumption. Partner pricing replaces these once approved."
)

tab_est, tab_sens, tab_acc, tab_src = st.tabs(
    ["Estimate", "What moves it", "How accurate", "Sources"]
)

with tab_est:
    left, right = st.columns([5, 6], gap="large")

    with left:
        st.subheader("1 · The project")
        label = st.text_input("Project label", value="Example: 2nd floor office", max_chars=80)
        market = st.selectbox("Market", list(MARKETS), key="market")
        ptype = st.radio("Project type", PROJECT_TYPES, horizontal=True, key="ptype")
        reuse = 0
        if ptype == "Refresh":
            reuse = st.slider("Share of furniture reused (%)", 0, 75, 25, step=5, key="reuse")

        st.subheader("2 · The space")
        c1, c2 = st.columns(2)
        area = c1.number_input(
            "Square feet", min_value=500, max_value=500_000, value=12_000, step=500, key="area"
        )
        basis = c2.selectbox("Measured as", list(AREA_BASES), key="basis")
        heads_in = c1.number_input(
            "Headcount (0 = estimate)", min_value=0, max_value=5_000, value=0, key="heads"
        )
        heads = int(heads_in) or default_headcount(area, book.usf_per_person)
        mix = c2.radio("Space mix", list(PRIVATE_SHARE), index=1, key="mix")
        suggested = space_program(heads, mix)
        st.caption("Space program (edit any count)")
        p = st.columns(4)
        k = f"{heads}-{mix}"  # fresh suggestion whenever headcount or mix changes
        program = Program(
            workstations=p[0].number_input(
                "Workstations", 0, 5_000, suggested.workstations, key=f"ws-{k}"
            ),
            private_offices=p[1].number_input(
                "Offices", 0, 5_000, suggested.private_offices, key=f"po-{k}"
            ),
            conference_rooms=p[2].number_input(
                "Conference", 0, 500, suggested.conference_rooms, key=f"cr-{k}"
            ),
            huddle_rooms=p[3].number_input("Huddle", 0, 500, suggested.huddle_rooms, key=f"hd-{k}"),
        )

        st.subheader("3 · Finish and pricing")
        finish = st.radio(
            "Finish level",
            list(FINISH_LABEL),
            index=1,
            format_func=FINISH_LABEL.get,
            horizontal=True,
            key="finish",
        )
        c3, c4 = st.columns(2)
        buyer = c3.radio("Buyer", ["commercial", "public"], horizontal=True, key="buyer")
        year = c4.selectbox("Purchase year", ["2026", "2027", "2028"], key="year")
        tax = c3.selectbox("Sales tax", ["exempt", *book.tax_pct], index=2, key="tax")
        adders = c4.checkbox("Include freight, install, handling", key="adders")

        st.subheader("Conversation notes")
        notes = st.text_area(
            "Notes (kept as plain text; not used for pricing)",
            placeholder="e.g. about 60 people, mostly open plan, 4 offices for leadership",
            max_chars=2_000,
            key="notes",
        )

    inputs = Inputs(
        area_sf=float(area),
        area_basis=AREA_BASES[basis],
        finish=finish,
        buyer=buyer,
        tier=MARKETS[market],
        period=year,
        include_adders=adders,
        tax_scope=None if tax == "exempt" else tax,
        reuse_pct=float(reuse),
    )
    est = estimate(inputs, book)

    with right:
        st.subheader("Preliminary furniture budget")
        m1, m2 = st.columns(2)
        m1.metric("Budget range", f"\\${est.low:,.0f} – \\${est.high:,.0f}")
        m2.metric("Per sq ft", f"\\${est.psf_low:,.2f} – \\${est.psf_high:,.2f}")
        st.caption(
            f"{area:,} sq ft · about {heads} people · {FINISH_LABEL[finish]} finish"
            + (f" · {reuse}% reused" if reuse else "")
        )

        _, summary = _scores()
        adj = next((s for s in summary if s.variant == "adjusted"), None)
        if adj:
            st.info(
                f"Checked against {adj.n} public furniture awards: the adjusted model's median "
                f"error is {adj.median_abs_error_pct:.0f}%. Few data points, so treat the range "
                "as a starting point. See *How accurate*."
            )

        st.markdown("**Published bands vs this estimate (\\$/sf, before adjustments)**")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Market band": tier,
                        "Low": lo,
                        "High": hi,
                        "Selected": "◀" if tier == MARKETS[market] else "",
                    }
                    for tier, (lo, hi) in sorted(book.bands.items())
                ]
            ),
            hide_index=True,
            width="stretch",
        )

        st.markdown("**Ask next to narrow the range**")
        for q in next_questions(ptype, heads_in > 0, heads):
            st.markdown(f"- {q}")

        st.markdown("**Client-ready summary** (copy button at top right)")
        st.code(client_summary(label, est, heads, finish, reuse), language=None, wrap_lines=True)

        with st.expander("Assumptions and sources"):
            band_lo, band_hi = book.bands[MARKETS[market]]
            rows = [
                {
                    "Assumption": "Furniture cost band",
                    "Value": f"${band_lo:.2f} – ${band_hi:.2f}/sf (Dec 2025)",
                    "Source": book.sources["band"],
                },
                {
                    "Assumption": "Finish placement",
                    "Value": f"{FINISH_PLACEMENT[finish]} of band",
                    "Source": "assumption",
                },
                *[
                    {
                        "Assumption": f.name,
                        "Value": f"x {f.multiplier:.3f} · {f.note}",
                        "Source": f.source_id,
                    }
                    for f in est.factors
                ],
                {
                    "Assumption": "Sq ft per person",
                    "Value": f"{book.usf_per_person:g} usable",
                    "Source": book.sources["usf_per_person"],
                },
                {
                    "Assumption": "Private office share",
                    "Value": f"{PRIVATE_SHARE[mix]:.0%} ({mix})",
                    "Source": "assumption",
                },
                {
                    "Assumption": "Meeting rooms",
                    "Value": f"1 conference / {PEOPLE_PER_CONFERENCE} people, "
                    f"1 huddle / {PEOPLE_PER_HUDDLE}",
                    "Source": "assumption",
                },
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

        with st.expander("Hand-off to design"):
            items = handoff_items(area, heads, heads_in > 0, program, finish, notes)
            for i, (item, done) in enumerate(items):
                st.checkbox(item, value=done, key=f"handoff-{i}-{done}")
            if notes.strip():
                st.text(notes)

with tab_sens:
    base_mid, swings = tornado(inputs, book)
    st.write(
        f"Baseline midpoint **\\${base_mid:,.0f}** for the project on the Estimate tab. Each bar "
        "changes one assumption and keeps the rest. The widest bars are the questions worth "
        "answering first."
    )
    df = pd.DataFrame(
        {
            "low side": [s.low_total - base_mid for s in swings],
            "high side": [s.high_total - base_mid for s in swings],
        },
        index=[f"{i}. {s.name}" for i, s in enumerate(swings, start=1)],
    )
    st.bar_chart(df, horizontal=True, stack=False)
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Assumption": s.name,
                    "Low": s.low_label,
                    "Low total": round(s.low_total),
                    "High": s.high_label,
                    "High total": round(s.high_total),
                    "Spread": round(s.spread),
                }
                for s in swings
            ]
        ),
        hide_index=True,
        width="stretch",
    )

with tab_acc:
    scored, summary = _scores()
    st.write(
        "Scored against public projects with a known furniture total. **Headline** = awarded, "
        "furniture-only contracts. With so few, these numbers show the method works; they do "
        "not prove accuracy yet."
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Variant": s.variant,
                    "n": s.n,
                    "Coverage %": round(s.coverage_pct),
                    "Median abs error %": round(s.median_abs_error_pct),
                    "Band width %": round(s.median_width_pct),
                }
                for s in summary
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    variant = st.radio(
        "Show variant",
        ["published", "adjusted", "calibrated"],
        index=1,
        horizontal=True,
        key="variant",
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Project": s.project.name,
                    "Year": s.project.year,
                    "Role": s.project.role,
                    "Actual $/sf": round(s.actual_psf, 2),
                    "Estimate $/sf": f"{s.low_psf:.2f} – {s.high_psf:.2f}",
                    "Error %": round(s.error_pct),
                    "Check": "pass" if s.passes else "FAIL",
                }
                for s in scored
                if s.variant == variant
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "Roles: headline = scored; floor = reused furniture, estimate should be above; "
        "envelope = budget, estimate should be at or below; per_seat = seats x usable sf/person."
    )

with tab_src:
    st.write("Every number the tool uses, with the page it came from.")
    link = {"source_url": st.column_config.LinkColumn("Source")}
    st.markdown("**Benchmarks and assumptions**")
    st.dataframe(
        _csv("benchmarks.csv")[["metric", "scope", "low", "high", "value", "unit", "source_url"]],
        column_config=link,
        hide_index=True,
        width="stretch",
    )
    st.markdown("**Evaluation projects**")
    st.dataframe(
        _csv("eval_projects.csv")[
            [
                "name",
                "year",
                "state",
                "evidence",
                "scope",
                "area_sf",
                "area_basis",
                "seats",
                "actual_usd",
                "source_url",
            ]
        ],
        column_config=link,
        hide_index=True,
        width="stretch",
    )

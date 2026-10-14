"""Streamlit entry point. Run: uv run streamlit run app/streamlit_app.py"""

import pandas as pd
import streamlit as st

import aoi_budget
from aoi_budget.book import load_book
from aoi_budget.estimator import FINISH_POSITION, Inputs, estimate
from aoi_budget.evaluate import evaluate, load_projects, summarize
from aoi_budget.sensitivity import tornado

st.set_page_config(page_title="AOI Budget Tool", layout="centered")
st.title("AOI Budget Tool")
st.caption(
    f"Public-data prototype, v{aoi_budget.__version__}. Every number comes from a published "
    "source; partner pricing will replace these assumptions once approved."
)

book = load_book()

with st.sidebar:
    st.header("Project")
    area = st.number_input("Area (sq ft)", min_value=100, max_value=2_000_000, value=20_000)
    basis = st.selectbox("Area measured as", ["USF", "RSF", "GSF"], help="Usable, rentable, gross")
    finish = st.selectbox("Finish level", [f for f in FINISH_POSITION if f != "unknown"], index=1)
    buyer = st.radio("Buyer", ["commercial", "public"], horizontal=True, key="buyer")
    tier = st.selectbox("Market band", sorted(book.bands), index=2)
    tax_scope = st.selectbox("Sales tax", ["exempt", *book.tax_pct], index=2)
    adders = st.checkbox("Include freight, install, handling", key="adders")
    period = st.selectbox("Purchase year", ["2026", "2027", "2028"])

inputs = Inputs(
    area_sf=float(area),
    area_basis=basis,
    finish=finish,
    buyer=buyer,
    tier=tier,
    period=period,
    include_adders=adders,
    tax_scope=None if tax_scope == "exempt" else tax_scope,
)
est = estimate(inputs, book)

tab_est, tab_sens, tab_acc = st.tabs(["Estimate", "What moves it", "How accurate"])

with tab_est:
    c1, c2 = st.columns(2)
    c1.metric("Budget range", f"${est.low:,.0f} - ${est.high:,.0f}")
    c2.metric("Per sq ft", f"${est.psf_low:,.2f} - ${est.psf_high:,.2f}")
    band_low, band_high = book.bands[tier]
    st.write(
        f"Starts from the published {tier} furniture band of ${band_low:.2f}-${band_high:.2f}/sf "
        f"(as of Dec 2025), narrowed to the {finish} part of the band, then:"
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Adjustment": f.name,
                    "x": round(f.multiplier, 3),
                    "Why": f.note,
                    "Source": f.source_id,
                }
                for f in est.factors
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "Lincoln/Omaha are not listed by the guide; Tier 3 is a labeled proxy. "
        "Sources: data/public/sources.yaml."
    )

with tab_sens:
    base_mid, swings = tornado(inputs, book)
    st.write(
        f"Baseline midpoint ${base_mid:,.0f}. Each bar changes one assumption and keeps the "
        "rest. The widest bars are the questions worth answering first."
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
    scored = evaluate(load_projects(), book)
    st.write(
        "Scored against public projects with a known total. Headline = awarded, furniture-only "
        "contracts. With n = 2 these numbers show the harness works; they do not prove accuracy."
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
                for s in summarize(scored)
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    variant = st.radio("Show variant", ["published", "adjusted", "calibrated"], horizontal=True)
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Project": s.project.name,
                    "Year": s.project.year,
                    "Role": s.project.role,
                    "Actual $/sf": round(s.actual_psf, 2),
                    "Estimate $/sf": f"{s.low_psf:.2f}-{s.high_psf:.2f}",
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
        "envelope = budget, estimate should be at or below; per_seat = seats x 200 usable sf."
    )

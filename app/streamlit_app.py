"""Streamlit entry point. Run: uv run streamlit run app/streamlit_app.py

Seller flow (#16): 1 scope -> 2 range (with typo checks) -> 3 what to say (talking points,
what-ifs, questions, client summary, designer hand-off). Expert view adds the method choice,
partner second opinion, assumptions table and the sensitivity / accuracy / sources tabs.
User text is only ever shown as plain text (st.code / st.text).
"""

import csv

import pandas as pd
import streamlit as st

import aoi_budget
from aoi_budget.book import DATA_DIR, load_book
from aoi_budget.calibration import noise_floor
from aoi_budget.calibration import run as calibration_run
from aoi_budget.estimator import Inputs, estimate
from aoi_budget.evaluate import evaluate, load_projects, summarize
from aoi_budget.intake import llm_enabled, read_notes
from aoi_budget.price_layer import bottom_up, load_price_layer
from aoi_budget.price_layer import score as score_bottom_up
from aoi_budget.seller import (
    FINISH_LABEL,
    FINISH_PLACEMENT,
    PEOPLE_PER_CONFERENCE,
    PEOPLE_PER_HUDDLE,
    PRIVATE_SHARE,
    PROJECT_TYPES,
    Program,
    biggest_unknown,
    client_summary,
    default_headcount,
    handoff_items,
    next_questions,
    sanity_checks,
    space_program,
    talking_points,
    what_ifs,
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
BADGE = {"Published": "green", "Assumption": "orange", "From the client": "blue"}
METHODS = {
    "Adjusted (v1)": "all sourced adjustments below",
    "Published band only (v0)": "band x finish x price level; ignores buyer, area basis, reuse, "
    "add-ons and tax",
}
# Widget defaults live in session state so "Apply to form" can change them (#16).
DEFAULTS = {
    "ptype": PROJECT_TYPES[0],
    "reuse": 25,
    "area": 12_000,
    "basis": "Usable (USF)",
    "heads": 0,
    "mix": "Balanced",
    "finish": "standard",
    "buyer": "commercial",
    "intake_v": 0,
    "walls": False,
}
for _k, _v in DEFAULTS.items():
    st.session_state.setdefault(_k, _v)
# ADR 0005: prefab interior walls (DIRTT) are quoted separately, never inside the furniture
# range. Public placeholder from DIRTT-published case studies, $ per sf of floor (wide on purpose).
WALLS_PSF = (19, 67)
BASIS_LABEL = {v: k for k, v in AREA_BASES.items()}
COUNT_FIELDS = ("private_offices", "conference_rooms", "huddle_rooms")
FIELD_LABEL = {
    "area_sf": "Square feet",
    "area_basis": "Measured as",
    "headcount": "Headcount",
    "mix": "Space mix",
    "private_offices": "Offices",
    "conference_rooms": "Conference",
    "huddle_rooms": "Huddle",
    "finish": "Finish level",
    "project_type": "Project type",
    "reuse_pct": "Reused (%)",
    "buyer": "Buyer",
}


@st.cache_resource
def _price_layer():
    """Partner price layer: present only on the approved laptop (ADR 0004), else None."""
    return load_price_layer()


@st.cache_data
def _scores():
    b = load_book()
    scored = evaluate(load_projects(), b)
    if _price_layer() is not None:
        scored += score_bottom_up(_price_layer(), b)
    return scored, summarize(scored)


@st.cache_data
def _calibration():
    return calibration_run(), noise_floor()


def _shown(field: str, value) -> str:
    if field == "area_basis":
        return BASIS_LABEL[value]
    if field == "finish":
        return FINISH_LABEL[value]
    return f"{value:,}" if isinstance(value, int) else str(value)


def _read_notes() -> None:
    use_model = st.session_state.get("use_model", False)
    st.session_state.proposal = read_notes(st.session_state.get("notes", ""), use_model)


def _apply_proposal() -> None:
    f = st.session_state.proposal.fields
    ss = st.session_state
    if "area_sf" in f:
        ss.area = f["area_sf"]
    if "area_basis" in f:
        ss.basis = BASIS_LABEL[f["area_basis"]]
    for field, key in (("headcount", "heads"), ("mix", "mix"), ("finish", "finish")):
        if field in f:
            ss[key] = f[field]
    if "buyer" in f:
        ss.buyer = f["buyer"]
    if "project_type" in f:
        ss.ptype = f["project_type"]
    if "reuse_pct" in f:
        ss.reuse = min(75, 5 * round(f["reuse_pct"] / 5))  # slider steps by 5
        ss.ptype = "Refresh"
    counts = {k: f[k] for k in COUNT_FIELDS if k in f}
    if counts:
        heads = ss.heads or default_headcount(ss.area, book.usf_per_person)
        ss.program_override = {"for": (heads, ss.mix), **counts}
    ss.intake_v += 1
    ss.proposal = None


def _csv(name: str) -> pd.DataFrame:
    with (DATA_DIR / name).open(newline="", encoding="utf-8") as f:
        return pd.DataFrame(list(csv.DictReader(f)))


st.title("AOI Budget Tool")
expert = st.toggle("Expert view (method, accuracy, sensitivity, sources)", key="expert")
st.caption(
    f"v{aoi_budget.__version__} · Public-data estimate: every number comes from a published "
    "source or a labeled assumption. Partner prices appear only on the approved laptop, in the "
    "item-by-item second opinion."
)

if expert:
    tab_est, tab_sens, tab_acc, tab_src = st.tabs(
        ["Estimate", "What moves it", "How accurate", "Sources"]
    )
else:  # seller view: one page, no tabs
    tab_est = st.container()

with tab_est:
    left, right = st.columns([5, 6], gap="large")

    with left:
        st.header("1 · Scope")
        st.subheader("The project")
        label = st.text_input("Project label", value="Example: 2nd floor office", max_chars=80)
        ptype = st.radio("Project type", PROJECT_TYPES, horizontal=True, key="ptype")
        reuse = 0
        if ptype == "Refresh":
            reuse = st.slider("Share of furniture reused (%)", 0, 75, step=5, key="reuse")

        st.subheader("The space")
        c1, c2 = st.columns(2)
        area = c1.number_input(
            "Square feet", min_value=500, max_value=500_000, step=500, key="area"
        )
        basis = c2.selectbox("Measured as", list(AREA_BASES), key="basis")
        heads_in = c1.number_input(
            "Headcount (0 = estimate)", min_value=0, max_value=5_000, key="heads"
        )
        heads = int(heads_in) or default_headcount(area, book.usf_per_person)
        mix = c2.radio("Space mix", list(PRIVATE_SHARE), key="mix")
        suggested = space_program(heads, mix)
        override = st.session_state.get("program_override") or {}
        if override.get("for") == (heads, mix):  # counts from the notes, until headcount/mix change
            offices = override.get("private_offices", suggested.private_offices)
            suggested = Program(
                workstations=max(0, heads - offices),
                private_offices=offices,
                conference_rooms=override.get("conference_rooms", suggested.conference_rooms),
                huddle_rooms=override.get("huddle_rooms", suggested.huddle_rooms),
            )
        st.caption("Space program (edit any count)")
        p = st.columns(4)
        # Fresh suggestion whenever headcount, mix or applied notes change.
        k = f"{heads}-{mix}-{st.session_state.intake_v}"
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

        st.subheader("Finish")
        finish = st.radio(
            "Finish level",
            list(FINISH_LABEL),
            format_func=FINISH_LABEL.get,
            horizontal=True,
            key="finish",
        )
        buyer = st.radio("Buyer", ["commercial", "public"], horizontal=True, key="buyer")
        # Defaults fit a typical Lincoln/Omaha office, so sellers rarely need to open this.
        more = st.container() if expert else st.expander("More pricing options")
        with more:
            market = st.selectbox("Market", list(MARKETS), key="market")
            c3, c4 = st.columns(2)
            year = c4.selectbox("Purchase year", ["2026", "2027", "2028"], key="year")
            tax = c3.selectbox("Sales tax", ["exempt", *book.tax_pct], index=2, key="tax")
            adders = c3.checkbox("Include freight, install, handling", key="adders")
            walls = st.checkbox("Show prefab walls (DIRTT) as a separate allowance", key="walls")
        if expert:
            method = st.radio("Method", list(METHODS), horizontal=True, key="method")
            st.caption(METHODS[method])
        else:
            method = next(iter(METHODS))

        st.subheader("Conversation notes")
        notes = st.text_area(
            "Notes (kept as plain text; not used for pricing)",
            placeholder="e.g. about 60 people, mostly open plan, 4 offices for leadership",
            max_chars=2_000,
            key="notes",
        )
        if llm_enabled():
            st.toggle(
                "Read with AI model (sends these notes to the model provider)", key="use_model"
            )
        st.button("Read notes into the form", on_click=_read_notes, disabled=not notes.strip())
        proposal = st.session_state.get("proposal")
        if proposal:
            if proposal.error:
                st.warning(f"Could not read the notes: {proposal.error}. Nothing was changed.")
            elif proposal.fields:
                st.caption(f"Found in the notes ({proposal.source}). Check before applying:")
                st.dataframe(
                    pd.DataFrame(
                        [
                            {"Field": FIELD_LABEL[k], "Value": _shown(k, v)}
                            for k, v in proposal.fields.items()
                        ]
                    ),
                    hide_index=True,
                    width="stretch",
                )
                st.button("Apply to form", on_click=_apply_proposal, type="primary")
            else:
                st.caption("No form fields found in the notes.")
            if proposal.dropped:
                st.caption("Ignored:")
                st.text("\n".join(proposal.dropped))

    adjusted_inputs = Inputs(
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
    if method.endswith("(v0)"):
        inputs = Inputs(area_sf=float(area), finish=finish, tier=MARKETS[market], period=year)
    else:
        inputs = adjusted_inputs
    est = estimate(inputs, book)

    with right:
        st.header("2 · Range")
        m1, m2 = st.columns(2)
        m1.metric("Budget range", f"\\${est.low:,.0f} – \\${est.high:,.0f}")
        m2.metric("Per sq ft", f"\\${est.psf_low:,.2f} – \\${est.psf_high:,.2f}")
        st.caption(
            f"{area:,} sq ft · about {heads} people · {FINISH_LABEL[finish]} finish"
            + (f" · {reuse}% reused" if reuse and inputs.reuse_pct else "")
            + f" · {method}"
        )
        for msg in sanity_checks(area, heads, heads_in > 0, program):
            st.warning(msg)

        _, summary = _scores()
        inf = next((s for s in summary if s.variant == "informed"), None)
        if inf:
            st.info(
                f"Checked against {inf.n} public furniture awards, with each project's finish "
                f"level set: median error {inf.median_abs_error_pct:.0f}%. Few data points, so "
                "treat the range as a starting point. See *How accurate*."
            )

        if walls:
            w_lo, w_hi = WALLS_PSF
            st.warning(
                f"**Prefab walls (DIRTT): separate line, not in the furniture budget.** "
                f"Rough public allowance \\${area * w_lo:,.0f} – \\${area * w_hi:,.0f} "
                f"(\\${w_lo}–\\${w_hi} per sq ft of floor). Walls are quoted per project from wall "
                "length, glass, doors and power; ask for a real quote."
            )

        st.header("3 · What to say")
        st.markdown("**Talking points** (the label says how firm each one is)")
        for text, firmness in talking_points(est, heads, finish):
            safe = text.replace("$", "\\$")  # a bare $ pair would render as LaTeX
            st.markdown(f"- {safe} :{BADGE[firmness]}-badge[{firmness}]")

        st.markdown("**Ask next to narrow the range**")
        top = biggest_unknown(tornado(inputs, book)[1])
        if top:
            top = top.replace("$", "\\$")
            st.markdown(f"- **{top}**")
        for q in next_questions(ptype, heads_in > 0, heads):
            st.markdown(f"- {q}")

        if not method.endswith("(v0)"):
            st.markdown("**Quick what-ifs** (one change each, everything else the same)")
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "If the client asks about…": what,
                            "Range": f"${alt.low:,.0f} – ${alt.high:,.0f}",
                            "vs now": f"{(alt.mid - est.mid) / est.mid:+.0%}",
                        }
                        for what, alt in what_ifs(inputs, book)
                    ]
                ),
                hide_index=True,
                width="stretch",
            )

        st.markdown("**Client-ready summary** (copy button at top right)")
        st.code(
            client_summary(label, est, heads, finish, inputs.reuse_pct),
            language=None,
            wrap_lines=True,
        )

        with st.expander("Hand-off to design"):
            items = handoff_items(area, heads, heads_in > 0, program, finish, notes)
            for i, (item, done) in enumerate(items):
                st.checkbox(item, value=done, key=f"handoff-{i}-{done}")
            if notes.strip():
                st.text(notes)

        if expert:
            with st.expander("Second opinion: item by item (partner price books)"):
                layer = _price_layer()
                if layer is None:
                    st.caption(
                        "Not loaded on this computer. Partner prices stay on one approved "
                        "laptop, so this panel shows numbers only there. The main range above "
                        "uses public data."
                    )
                else:
                    bu = bottom_up(program, adjusted_inputs, layer, book)
                    st.metric("Item-by-item range", f"\\${bu.low:,.0f} – \\${bu.high:,.0f}")
                    st.dataframe(
                        pd.DataFrame(
                            [
                                {"Item": ln.category, "Count": ln.count, "Priced from": ln.source}
                                for ln in bu.lines
                            ]
                        ),
                        hide_index=True,
                        width="stretch",
                    )
                    st.caption(
                        "Counts x list price x options x category discount. Kits per space type "
                        "are our assumption; discounts come from a public cooperative contract "
                        "and are not yet verified. Herman Miller lines only (no Knoll yet)."
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

if not expert:  # seller view ends here; the tabs below are for the team
    st.stop()

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
                    "Low total": f"${s.low_total:,.0f}",
                    "High": s.high_label,
                    "High total": f"${s.high_total:,.0f}",
                    "Spread": f"${s.spread:,.0f}",
                }
                for s in swings
            ]
        ),
        hide_index=True,
        width="stretch",
    )

with tab_acc:
    scored, summary = _scores()
    calib, floor = _calibration()
    st.write(
        "Scored against public projects with a known furniture total. **Headline** = awarded, "
        "furniture-only contracts. With so few, these numbers show the method works; they do "
        "not prove accuracy yet."
    )
    f1, f2, f3 = st.columns(3)
    f1.metric("Noise floor", f"{floor['loo_median_abs_dev_pct']:.1f}%")
    f2.metric("Winning bid vs typical bid", f"{floor['low_bid_vs_median_pct']:+.1f}%")
    f3.metric("Public bid tabs", f"{floor['tabs']} tabs / {floor['bids']} bids")
    st.caption(
        "Noise floor: how far honest bids on the same spec differ. No estimate can beat it on "
        "average, so a median error near 10% on 10+ projects is the stop line "
        "(docs/accuracy-target.md)."
    )
    st.markdown("**Range quality (headline projects)**")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Method": c.variant,
                    "n": c.n,
                    "Inside range %": round(c.coverage_pct),
                    "Median abs error %": round(c.median_abs_error_pct),
                    "Interval score (lower is better)": round(c.mean_rel_interval_score, 2),
                    "Under-quoted %": round(c.under_pct),
                }
                for c in calib
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "Interval score = range width plus a penalty for a miss, so vague and wrong both cost. "
        "Reference = the other projects' \\$/sf. Estimates for 15 partner case studies are "
        "frozen with a hash before their totals are known (data/public/"
        "preregistered_estimates.csv)."
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
        list(dict.fromkeys(s.variant for s in scored)),
        index=2,
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
    st.markdown("**Public bid tabulations (noise floor)**")
    st.dataframe(
        _csv("bid_tabs.csv")[
            [
                "tab_id",
                "public_body",
                "year",
                "state",
                "bidder",
                "total_usd",
                "compliant",
                "source_url",
            ]
        ],
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

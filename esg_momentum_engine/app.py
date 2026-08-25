from __future__ import annotations
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from scoring import (
    score_universe, DEFAULT_WEIGHTS, QUADRANT_META,
    POSITIVE_SIGNALS, benchmarks, shrinkage_report,
    SECTOR_RELATIVE, UNIVERSE_RELATIVE,
)

st.set_page_config(page_title="ESG Momentum Engine 2.0", page_icon="🚀", layout="wide")

NAVY = "#0f2038"
TEAL = "#16b8a6"
st.markdown(f"""
<style>
    .block-container {{ padding-top: 2rem; }}
    h1, h2, h3 {{ color: {NAVY}; }}
    .quad-badge {{ padding:2px 10px; border-radius:12px; color:white; font-weight:600; font-size:0.8rem; }}
    .metric-note {{ color:#64748b; font-size:0.85rem; }}
</style>
""", unsafe_allow_html=True)

# pillars
# colors
PILLAR_COLORS = {"E": "#16a34a", "S": "#3b82f6", "G": "#8b5cf6", "I": "#f59e0b"}

PILLAR_LABELS = {
    "E": "Environmental momentum",
    "S": "Social momentum",
    "G": "Governance momentum",
    "I": "Innovation / Digital momentum",
    "sentiment": "News sentiment",
    "say_do": "Say-Do Gap penalty",
}

SIGNAL_LABELS = {
    **PILLAR_LABELS,
    "esg_cagr": "ESG CAGR (5yr)",
    "hiring_growth": "Hiring growth",
    "ai_job_pct": "AI job posting %",
    "ai_patent_count": "AI patent activity",
    "ai_earnings_mentions": "AI earnings mentions",
    "sentiment_trend": "News sentiment",
    "controversy": "Controversy (risk)",
}


@st.cache_data
def _load(weights_tuple, esg_t, mom_t, mode):
    weights = dict(weights_tuple)
    companies, thresholds = score_universe(
        weights=weights,
        esg_threshold=esg_t if esg_t > 0 else None,
        momentum_threshold=mom_t if mom_t > 0 else None,
        mode=mode,
    )
    bench = benchmarks(companies)
    shrink = shrinkage_report(companies)
    df = pd.DataFrame([{
        "Company": c.company, "Ticker": c.ticker, "Country": c.country,
        "Sector": c.sector, "ESG Score": c.esg_score_today,
        "ESG CAGR %": round(c.esg_cagr_5yr * 100, 1),
        "Momentum": c.momentum_score, "Quadrant": c.quadrant,
        "Revenue $B": c.revenue_usd_b, "Hiring growth %": round(c.hires_growth * 100, 0),
        "AI job %": c.ai_job_pct, "AI patents": c.ai_patent_count,
        "AI earnings mentions": c.ai_earnings_mentions,
        "Sentiment": c.sentiment_score, "Sentiment trend": c.sentiment_trend,
        "Controversy flags": c.controversy_flags_12mo,
        "Source": c.data_source,
        "Stage": c.company_stage,
        "Say-Do Gap": c.say_do_gap,
        "Value Gap": c.value_gap,
        "Say-Do Confidence": c.say_do_confidence,
        "Claims Source": c.raw.get("claims_source", "hand-coded"),
        "Claim Articles": c.raw.get("claim_articles_12mo", ""),
        "Stated Commitments": c.raw.get("stated_commitments", ""),
        "Why these weights": c.why_weights(),
        **{f"_pillar_{k}": v for k, v in c.pillar_scores.items()},
        **{f"_w_{k}": v for k, v in c.pillar_weights.items()},
        **{f"_sig_{k}": v for k, v in c.signals_norm.items()},
    } for c in companies])
    return df, thresholds, bench, shrink


@st.cache_data
def _provenance():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "data", "provenance.csv")
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


st.sidebar.title("⚙️ Model controls")

st.sidebar.markdown("#### Benchmark")
mode = st.sidebar.radio(
    "Score each company against",
    [SECTOR_RELATIVE, UNIVERSE_RELATIVE],
    format_func=lambda m: ("Its own sector" if m == SECTOR_RELATIVE
                           else "The whole universe"),
    help="Comparing an oil producer with a software firm tells you nothing you "
         "did not already know. Sector-relative asks the only fair question: is "
         "this company improving faster than its peers? Flip it and watch the "
         "ranking move.",
)
st.sidebar.markdown("---")
st.sidebar.caption("Multipliers on the (sector, stage) weight table. 1.0 uses the "
                   "table as written; 0 switches an axis off. This is the "
                   "'challenge the framework' knob.")

weights = {}
for k in DEFAULT_WEIGHTS:
    label = SIGNAL_LABELS.get(k, k)
    weights[k] = st.sidebar.slider(label, 0.0, 3.0, float(DEFAULT_WEIGHTS[k]), 0.1)

st.sidebar.markdown("---")
manual_thresh = st.sidebar.checkbox("Set thresholds manually", value=False)
esg_t = st.sidebar.slider("ESG threshold", 30.0, 90.0, 56.0, 1.0) if manual_thresh else 0.0
mom_t = st.sidebar.slider("Momentum threshold", 0.0, 100.0, 55.0, 1.0) if manual_thresh else 0.0

df, thresholds, bench, shrink = _load(
    tuple(sorted(weights.items())), esg_t, mom_t, mode)

st.title("🚀 ESG Momentum Engine 2.0")
st.markdown("**From static scores to dynamic intelligence.** Traditional ESG asks "
            "*what is your score today?* — we ask *where are you going?* This engine "
            "blends alternative data (hiring, AI adoption, news, controversy) to find "
            "**Hidden Winners**: low ESG today, strong forward momentum.")

tab1, tab2, tab3, tab4 = st.tabs(["📊 The Matrix", "🔎 Company Drilldown",
                                 "🎯 My Portfolio", "🔍 Method & Limits"])

with tab1:
    esg_line = thresholds["esg_threshold"]
    mom_line = thresholds["momentum_threshold"]

    fig = go.Figure()

    x0, x1 = df["ESG Score"].min() - 3, df["ESG Score"].max() + 3
    y0, y1 = -2, 102
    quad_bg = [
        (x0, esg_line, mom_line, y1, "rgba(22,184,166,0.10)"),
        (esg_line, x1, mom_line, y1, "rgba(59,130,246,0.10)"),
        (x0, esg_line, y0, mom_line, "rgba(245,158,11,0.10)"),
        (esg_line, x1, y0, mom_line, "rgba(239,68,68,0.10)"),
    ]
    for qx0, qx1, qy0, qy1, color in quad_bg:
        fig.add_shape(type="rect", x0=qx0, x1=qx1, y0=qy0, y1=qy1,
                      fillcolor=color, line=dict(width=0), layer="below")

    labels = [
        (x0 + (esg_line - x0) / 2, y1 - 6, "HIDDEN WINNERS", "#0f766e"),
        (esg_line + (x1 - esg_line) / 2, y1 - 6, "FUTURE LEADERS", "#1e40af"),
        (x0 + (esg_line - x0) / 2, y0 + 6, "VALUE TRAPS", "#b45309"),
        (esg_line + (x1 - esg_line) / 2, y0 + 6, "OVERRATED LEADERS", "#b91c1c"),
    ]
    for lx, ly, txt, col in labels:
        fig.add_annotation(x=lx, y=ly, text=f"<b>{txt}</b>", showarrow=False,
                           font=dict(size=13, color=col), opacity=0.55)

    fig.add_vline(x=esg_line, line=dict(color="#94a3b8", dash="dash", width=1))
    fig.add_hline(y=mom_line, line=dict(color="#94a3b8", dash="dash", width=1))

    # benchmarks
    uni = bench["universe"]
    fig.add_hline(y=uni["momentum"], line=dict(color="#0f2038", dash="dot", width=1.5),
                  annotation_text="universe median momentum",
                  annotation_position="right",
                  annotation=dict(font=dict(size=10, color="#0f2038")))
    focus = st.selectbox("Overlay a sector benchmark", ["(none)"] +
                         sorted(df["Sector"].unique()), key="benchsector")
    if focus != "(none)" and focus in bench:
        b = bench[focus]
        fig.add_hline(y=b["momentum"], line=dict(color=TEAL, dash="dot", width=1.5),
                      annotation_text=f"{focus} median (n={b['n']})",
                      annotation_position="left",
                      annotation=dict(font=dict(size=10, color=TEAL)))

    for quad, meta in QUADRANT_META.items():
        sub = df[df["Quadrant"] == quad]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["ESG Score"], y=sub["Momentum"],
            mode="markers+text", name=quad,
            text=sub["Ticker"], textposition="top center",
            textfont=dict(size=9, color="#334155"),
            marker=dict(
                size=(sub["Revenue $B"] ** 0.5) * 4 + 9,
                color=meta["color"], line=dict(width=1.5, color="white"),
                opacity=0.85),
            customdata=sub[["Company", "Sector", "Country", "ESG CAGR %",
                            "Hiring growth %", "Controversy flags"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "%{customdata[2]} · %{customdata[1]}<br>"
                "ESG today: %{x} · Momentum: %{y}<br>"
                "ESG CAGR: %{customdata[3]}% · Hiring: %{customdata[4]}%<br>"
                "Controversy flags: %{customdata[5]}<extra>" + quad + "</extra>"),
        ))

    fig.update_layout(
        height=560, plot_bgcolor="white",
        xaxis=dict(title="ESG Score Today  →  (backward-looking)", range=[x0, x1],
                   showgrid=False, zeroline=False),
        yaxis=dict(title="Momentum 2.0 Score  →  (forward-looking)", range=[y0, y1],
                   showgrid=False, zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=40, r=20, t=40, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Split lines: ESG at {esg_line}, Momentum at {mom_line} "
               f"(median split unless set manually). Bubble size = revenue. "
               f"Data is illustrative/calibrated for demo — see README.")

    hw = df[df["Quadrant"] == "Hidden Winners"].sort_values("Momentum", ascending=False)
    if not hw.empty:
        top = hw.iloc[0]
        st.success(f"💡 **Top Hidden Winner: {top['Company']} ({top['Ticker']})** — "
                   f"ESG score only {top['ESG Score']} today, but a Momentum 2.0 score of "
                   f"{top['Momentum']}. The market is pricing what it *was*, not what it's "
                   f"*becoming*.")

    st.markdown("#### Full ranking")
    st.dataframe(
        df[["Company", "Ticker", "Country", "Sector", "ESG Score", "Momentum",
            "Quadrant", "ESG CAGR %", "Hiring growth %", "Controversy flags", "Source"]]
        .reset_index(drop=True),
        use_container_width=True, hide_index=True,
    )

with tab2:
    pick = st.selectbox("Choose a company", df["Company"].tolist())
    row = df[df["Company"] == pick].iloc[0]

    meta = QUADRANT_META[row["Quadrant"]]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ESG Score Today", row["ESG Score"])
    c2.metric("Momentum 2.0", row["Momentum"])
    c3.metric("ESG CAGR (5yr)", f"{row['ESG CAGR %']}%")
    c4.metric("Controversy flags", int(row["Controversy flags"]))
    st.markdown(f"<span class='quad-badge' style='background:{meta['color']}'>"
                f"{row['Quadrant']}</span> &nbsp; {meta['note']}", unsafe_allow_html=True)

    st.markdown("#### Four axes, scored separately")
    st.caption("E, S and G are real ESG pillars. Innovation is tracked as its own "
               "axis rather than being folded into Social — adopting AI is not a "
               "social outcome. Each bar is 0-100 within the chosen benchmark.")

    pillar_df = pd.DataFrame([
        {"Pillar": PILLAR_LABELS[k], "Score": row[f"_pillar_{k}"],
         "Weight": row[f"_w_{k}"], "key": k}
        for k in ("E", "S", "G", "I")])

    pbar = go.Figure(go.Bar(
        x=pillar_df["Score"], y=pillar_df["Pillar"], orientation="h",
        marker=dict(color=[PILLAR_COLORS[k] for k in pillar_df["key"]]),
        text=[f"{v:.0f}  (weight {w:.0%})"
              for v, w in zip(pillar_df["Score"], pillar_df["Weight"])],
        textposition="outside",
    ))
    pbar.add_vline(x=50, line=dict(color="#94a3b8", dash="dot", width=1))
    pbar.update_layout(height=250, plot_bgcolor="white",
                       xaxis=dict(range=[0, 118], title="Pillar momentum (50 = benchmark median)"),
                       margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(pbar, use_container_width=True)

    with st.expander(f"Why does {pick} get these weights?"):
        st.markdown(f"**Stage:** {row['Stage']}  ·  **Sector:** {row['Sector']}")
        st.markdown(f"_{row['Why these weights']}_")
        st.caption("Weights come from a (sector, stage) lookup table in weights.py, "
                   "not from a fitted model. Every cell is inspectable and arguable.")

    gap = row["Say-Do Gap"]
    conf = row["Say-Do Confidence"]
    st.markdown("#### Say-Do Gap")
    g1, g2 = st.columns([1, 3])
    g1.metric("Gap", f"{gap:.2f}", help="0 = claims backed by evidence. 1 = all talk.")
    n_claims = row["Claim Articles"]
    if row["Claims Source"] == "gdelt-news" and n_claims not in ("", None):
        g1.caption(f"{n_claims} pledge articles found in news")
    else:
        g1.caption("commitments hand-coded")
    verdict = ("Commitments are not matched by observed outcomes." if gap > 0.5
               else "Some gap between stated commitments and evidence." if gap > 0.2
               else "Claims are broadly consistent with observed outcomes.")
    g2.markdown(f"**{verdict}**")
    if conf == "unverified":
        g2.warning("Unverified — no independent evidence was fetched for this "
                   "company, so this compares disclosure against disclosure. "
                   "Run the pipeline with --live to bring in satellite emissions "
                   "and news-derived fines.", icon="⚠️")
    elif conf == "partial":
        g2.info("Partially verified — one external source contributed.", icon="ℹ️")
    else:
        g2.success("Verified against independent emissions and news evidence.", icon="✅")

    st.markdown("#### Legacy signal view")
    st.caption("The original seven signals, kept for comparison. "
               "Controversy is a risk — high is bad.")

    sig_rows = []
    for k in POSITIVE_SIGNALS + ["controversy"]:
        sig_rows.append({"Signal": SIGNAL_LABELS[k], "Normalized (0-1)": round(row[f"_sig_{k}"], 2)})
    sig_df = pd.DataFrame(sig_rows)

    bar = go.Figure(go.Bar(
        x=sig_df["Normalized (0-1)"], y=sig_df["Signal"], orientation="h",
        marker=dict(color=[TEAL if s != "Controversy (risk)" else "#ef4444"
                           for s in sig_df["Signal"]]),
        text=sig_df["Normalized (0-1)"], textposition="outside",
    ))
    bar.update_layout(height=320, plot_bgcolor="white",
                      xaxis=dict(range=[0, 1.1], title="Strength (0-1)"),
                      margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(bar, use_container_width=True)

    d1, d2, d3 = st.columns(3)
    d1.metric("AI job posting %", f"{int(row['AI job %'])}%")
    d1.metric("AI patents (12mo)", int(row["AI patents"]))
    d2.metric("AI earnings mentions", int(row["AI earnings mentions"]))
    d2.metric("Revenue", f"${row['Revenue $B']}B")
    d3.metric("News sentiment", f"{row['Sentiment']} ({row['Sentiment trend']})")
    d3.metric("Hiring growth", f"{int(row['Hiring growth %'])}%")

with tab3:
    st.markdown("#### 5-question risk & return profile")
    st.caption("Answer honestly. Your profile sets the tilt between undervalued "
               "momentum and compounding quality. Sector neutrality is not "
               "negotiable — see the note below the basket.")

    q1 = st.radio("1. Your investment horizon", ["< 1 year", "1\u20133 years", "3\u20135 years", "5+ years"], index=2)
    q2 = st.radio("2. If a holding dropped 20% in a month, you would", ["Sell immediately", "Trim the position", "Hold", "Buy more"], index=2)
    q3 = st.radio("3. What matters most to you", ["Protect capital", "Steady income", "Balanced growth", "Maximum growth"], index=2)
    q4 = st.radio("4. Appetite for early-stage / unproven names", ["None", "A little", "Moderate", "High"], index=2)
    q5 = st.radio("5. Target annual return", ["4\u20136% (safe)", "7\u201310%", "11\u201315%", "15%+ (aggressive)"], index=2)

    def idx(options, choice):
        return options.index(choice)

    score = (
        idx(["< 1 year", "1\u20133 years", "3\u20135 years", "5+ years"], q1) +
        idx(["Sell immediately", "Trim the position", "Hold", "Buy more"], q2) +
        idx(["Protect capital", "Steady income", "Balanced growth", "Maximum growth"], q3) +
        idx(["None", "A little", "Moderate", "High"], q4) +
        idx(["4\u20136% (safe)", "7\u201310%", "11\u201315%", "15%+ (aggressive)"], q5)
    )

    TOP_N_PER_SECTOR = 2

    if st.button("Build my basket", type="primary"):
        if score <= 4:
            profile, tilt = "Conservative", {"Future Leaders": 0.8, "Hidden Winners": 0.2}
        elif score <= 8:
            profile, tilt = "Balanced", {"Future Leaders": 0.55, "Hidden Winners": 0.45}
        elif score <= 12:
            profile, tilt = "Growth", {"Hidden Winners": 0.6, "Future Leaders": 0.4}
        else:
            profile, tilt = "Aggressive", {"Hidden Winners": 0.75, "Future Leaders": 0.25}

        st.markdown(f"### Your profile: **{profile}**  \u00b7  risk score {score}/15")

        # sectorneutral
        # Equal capital to every sector that has an improving name, then the top 2
        # by momentum inside each. A sector cannot dominate the basket by being large
        # or by scoring well in absolute terms, which is the point: you are never
        # betting on "energy is bad", only on the best improvers within energy.
        eligible = df[df["Quadrant"].isin(["Hidden Winners", "Future Leaders"])]

        if eligible.empty:
            st.warning("No companies sit in an improving quadrant at these weights. "
                       "Loosen the thresholds in the sidebar.")
        else:
            sectors = sorted(eligible["Sector"].unique())
            per_sector = 100.0 / len(sectors)

            basket_rows = []
            for sec in sectors:
                picks = (eligible[eligible["Sector"] == sec]
                         .sort_values("Momentum", ascending=False)
                         .head(TOP_N_PER_SECTOR))
                share = per_sector / len(picks)
                for rank, (_, p) in enumerate(picks.iterrows(), 1):
                    tilt_mult = tilt.get(p["Quadrant"], 0.5)
                    basket_rows.append({
                        "Sector": sec, "Rank in sector": rank,
                        "Company": p["Company"], "Ticker": p["Ticker"],
                        "Quadrant": p["Quadrant"],
                        "ESG Score": p["ESG Score"], "Momentum": p["Momentum"],
                        "Country": p["Country"],
                        "_w": share * (0.6 + 0.8 * tilt_mult),
                    })

            basket = pd.DataFrame(basket_rows)
            basket["Weight %"] = (basket["_w"] / basket["_w"].sum() * 100).round(2)
            basket = basket.drop(columns=["_w"])

            cA, cB = st.columns([3, 2])
            with cA:
                st.dataframe(
                    basket[["Sector", "Rank in sector", "Company", "Ticker",
                            "Quadrant", "Weight %", "ESG Score", "Momentum"]],
                    use_container_width=True, hide_index=True)
            with cB:
                sector_w = basket.groupby("Sector")["Weight %"].sum().reset_index()
                pie = go.Figure(go.Pie(
                    labels=sector_w["Sector"], values=sector_w["Weight %"], hole=0.45))
                pie.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0),
                                  showlegend=False,
                                  title=dict(text="Capital by sector", font=dict(size=13)))
                pie.update_traces(textinfo="label+percent", textfont_size=10)
                st.plotly_chart(pie, use_container_width=True)

            avg_esg = round((basket["ESG Score"] * basket["Weight %"] / 100).sum(), 1)
            avg_mom = round((basket["Momentum"] * basket["Weight %"] / 100).sum(), 1)
            spread = round(sector_w["Weight %"].max() - sector_w["Weight %"].min(), 1)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Holdings", len(basket))
            m2.metric("Sectors covered", len(sectors))
            m3.metric("Weighted ESG today", avg_esg)
            m4.metric("Weighted Momentum", avg_mom)

            st.info(f"**Sector-neutral by construction.** Every sector gets the same "
                    f"{per_sector:.1f}% of capital, then the top {TOP_N_PER_SECTOR} "
                    f"improvers inside it. Spread between the heaviest and lightest "
                    f"sector is {spread:.1f}pp \u2014 that residual is the risk tilt, "
                    f"not a sector bet. You are never asked to conclude 'don't invest "
                    f"in energy'; you are asked which energy names are actually improving.")
            st.caption("Only the two improving quadrants are eligible \u2014 never Value "
                       "Traps or Overrated Leaders.")


with tab4:
    st.markdown("### What this engine does not control for")
    st.caption("Every model has confounds. Ours are measured and printed here rather "
               "than left for someone else to find.")

    st.markdown("#### 1. Sector-relative scoring is weaker in thin sectors")
    st.markdown("A sector holding two companies cannot support a percentile. Each sector "
                "z-score is shrunk toward the universe score by n/(n+5), so a thin sector "
                "is mostly judged against everything. This table is the honest version of "
                "how much peer comparison each company actually received.")
    shrink_df = pd.DataFrame(shrink)
    shrink_df.columns = ["Sector", "Companies", "Sector weight", "Universe weight"]
    shrink_df["Sector weight"] = (shrink_df["Sector weight"] * 100).round(0).astype(int).astype(str) + "%"
    shrink_df["Universe weight"] = (shrink_df["Universe weight"] * 100).round(0).astype(int).astype(str) + "%"
    st.dataframe(shrink_df, use_container_width=True, hide_index=True)

    st.markdown("#### 2. Country is not controlled for — and it shows")
    cty = (df.groupby("Country")
             .agg(n=("Company", "size"),
                  med_mom=("Momentum", "median"),
                  med_esg=("ESG Score", "median"))
             .reset_index().sort_values("med_mom", ascending=False))
    uni_med = df["Momentum"].median()

    cfig = go.Figure(go.Bar(
        x=cty["med_mom"], y=cty["Country"], orientation="h",
        marker=dict(color=TEAL, line=dict(width=0)),
        text=[f"{v:.1f}" for v in cty["med_mom"]], textposition="outside",
        textfont=dict(color="#334155", size=11),
        customdata=cty[["n", "med_esg"]].values,
        hovertemplate="<b>%{y}</b><br>median momentum %{x:.1f}<br>"
                      "%{customdata[0]} companies · median ESG %{customdata[1]:.1f}"
                      "<extra></extra>",
    ))
    cfig.add_vline(x=uni_med, line=dict(color="#64748b", dash="dot", width=1.5),
                   annotation_text=f"universe median {uni_med:.1f}",
                   annotation_position="top",
                   annotation=dict(font=dict(size=10, color="#64748b")))
    cfig.update_layout(
        height=280, plot_bgcolor="white",
        xaxis=dict(title="Median Momentum 2.0 score", range=[0, 100],
                   showgrid=True, gridcolor="#eef2f7", zeroline=False),
        yaxis=dict(title="", autorange="reversed"),
        margin=dict(l=10, r=40, t=28, b=36), showlegend=False,
        title=dict(text="Median momentum by country of listing",
                   font=dict(size=13, color=NAVY), x=0, xanchor="left"),
    )
    st.plotly_chart(cfig, use_container_width=True)

    spread = cty["med_mom"].max() - cty["med_mom"].min()
    st.warning(
        f"**A {spread:.0f}-point median gap between the highest and lowest country — "
        f"wider than any sector gap in this universe.** Signals are normalised against "
        f"sector peers, never against country peers, so this is uncontrolled. Part of it "
        f"is real: the faster-growing markets here genuinely hold earlier-stage companies. "
        f"Part of it is a disclosure-regime artefact — a market that tightened its listing "
        f"rules recently starts from a lower base, so improvement looks steeper. "
        f"Country-relative normalisation uses the same machinery as the sector version, "
        f"but at these per-country counts it would shrink almost entirely back to the "
        f"universe. It needs a larger universe per country, and that is roadmap.",
        icon="⚠️")

    show = cty.copy()
    show.columns = ["Country", "Companies", "Median momentum", "Median ESG today"]
    st.dataframe(show.round(1), use_container_width=True, hide_index=True)

    st.markdown("#### 3. Which numbers are measured, and which are assumed")
    prov = _provenance()
    if prov is None:
        st.info("provenance.csv not found — run the pipeline to generate it.")
    else:
        real = int((prov["is_real"] == "yes").sum())
        total = len(prov)
        m1, m2, m3 = st.columns(3)
        m1.metric("Data cells", f"{total:,}")
        m2.metric("Measured", f"{real:,}")
        m3.metric("Calibrated", f"{total - real:,}")
        if real == 0:
            st.info("Every value in this demo is hand-calibrated to plausible magnitudes. "
                    "The live connectors — Yahoo/Sustainalytics, GDELT, Climate TRACE, "
                    "Wikirate, yfinance — are implemented; run "
                    "`python pipeline/build_master_data.py --live` to pull real values, "
                    "and this panel will show what came back.", icon="ℹ️")
        st.dataframe(prov["source"].value_counts().rename_axis("Source")
                     .reset_index(name="Cells"),
                     use_container_width=True, hide_index=True)

    st.markdown("#### 4. What we do not claim")
    st.markdown(
        "- **No predictive backtest.** Evidence that ESG improvers outperform comes from "
        "prior research, not from this engine. Building a backtest is the first roadmap item.\n"
        "- **Say-Do verification is only as good as its sources.** A company labelled "
        "*unverified* had no external evidence fetched; the score compares disclosure "
        "against disclosure and should not be read as a greenwashing finding.\n"
        "- **Governance coverage is uneven.** Insider and board filings are far richer for "
        "US-listed companies than ASEAN ones. We disclose the gap rather than imputing across it."
    )

"""Battery Dispatch Copilot (Team D01, Data2Decision M4).

Run from the repo root:  streamlit run app/app.py
Pages: Overview · Tomorrow's bid · Day replay · Scenario lab · Model lab · Risk and validation · Assistant.
The assistant runs locally on Ollama (default model qwen3:4b); if Ollama is not running it falls back to a built-in guide.
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import battery as bt

st.set_page_config(page_title="Battery Dispatch Copilot", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------------- design system
NAVY, BLUE, SKY, INK, MUTED, LINE = "#0f2c59", "#2563eb", "#93b4f5", "#0f172a", "#64748b", "#e2e8f0"
GREEN, RED, AMBER = "#059669", "#dc2626", "#d97706"
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, .stText, button, input, textarea, select {{ font-family: 'Inter', system-ui, sans-serif !important; }}
.block-container {{ padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1320px; }}
[data-testid="stSidebar"] {{ background: #0b1f3f; }}
[data-testid="stSidebar"] * {{ color: #e2e8f0 !important; }}
[data-testid="stSidebar"] .stRadio label p {{ font-size: 0.95rem; }}
h1, h2, h3 {{ color: {INK}; letter-spacing: -0.01em; }}
.eyebrow {{ color: {BLUE}; font-weight: 600; font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.2rem; }}
.title {{ font-size: 1.9rem; font-weight: 700; color: {INK}; margin: 0 0 0.3rem 0; }}
.lede {{ color: {MUTED}; font-size: 1.02rem; margin-bottom: 1.1rem; max-width: 900px; }}
.card {{ background: #ffffff; border: 1px solid {LINE}; border-radius: 14px; padding: 1rem 1.1rem; box-shadow: 0 1px 2px rgba(15,23,42,0.04); height: 100%; }}
.kpi-label {{ color: {MUTED}; font-size: 0.8rem; font-weight: 500; }}
.kpi-value {{ color: {INK}; font-size: 1.65rem; font-weight: 700; line-height: 1.25; }}
.kpi-sub {{ font-size: 0.82rem; font-weight: 500; }}
.pos {{ color: {GREEN}; }} .neg {{ color: {RED}; }} .neu {{ color: {MUTED}; }}
.step-num {{ display:inline-block; width:26px; height:26px; border-radius:50%; background:{NAVY}; color:#fff; text-align:center; line-height:26px; font-weight:600; font-size:0.85rem; margin-right:8px; }}
.step-title {{ font-weight: 600; color: {INK}; }}
.step-body {{ color: {MUTED}; font-size: 0.9rem; margin-top: 0.35rem; }}
.pill {{ display:inline-block; padding: 2px 10px; border-radius: 999px; background: #eef2ff; color: {NAVY}; font-size: 0.78rem; font-weight: 600; margin-right: 6px; }}
.section {{ font-size: 1.1rem; font-weight: 600; color: {INK}; margin: 1.2rem 0 0.5rem 0; }}
.note {{ color: {MUTED}; font-size: 0.85rem; }}
div[data-testid="stDataFrame"] {{ border: 1px solid {LINE}; border-radius: 10px; }}
</style>""", unsafe_allow_html=True)

pio.templates["copilot"] = go.layout.Template(layout=go.Layout(
    font=dict(family="Inter, system-ui, sans-serif", size=12, color=INK), paper_bgcolor="white", plot_bgcolor="white",
    colorway=[BLUE, NAVY, AMBER, GREEN, RED, MUTED], hovermode="x unified",
    xaxis=dict(showgrid=False, linecolor=LINE, ticks="outside", tickcolor=LINE),
    yaxis=dict(gridcolor="#f1f5f9", linecolor=LINE, zeroline=False),
    legend=dict(orientation="h", y=1.08, x=0, bgcolor="rgba(0,0,0,0)"), margin=dict(l=10, r=10, t=50, b=10),
    hoverlabel=dict(bgcolor="white", bordercolor=LINE, font=dict(family="Inter"))))
pio.templates.default = "copilot"


def card(label, value, sub=None, tone="neu"):
    s = f'<div class="kpi-sub {tone}">{sub}</div>' if sub else ""
    st.markdown(f'<div class="card"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div>{s}</div>', unsafe_allow_html=True)


def header(eyebrow, title, lede):
    st.markdown(f'<div class="eyebrow">{eyebrow}</div><div class="title">{title}</div><div class="lede">{lede}</div>', unsafe_allow_html=True)


def rupees(x): return f"₹{x:,.0f}"


# ---------------------------------------------------------------- data
@st.cache_data
def load():
    d = pd.read_csv(ROOT / "data/raw/iex_dam_15min.csv", usecols=["date", "block", "mcp_rs_mwh"])
    P = d.pivot(index="date", columns="block", values="mcp_rs_mwh"); P.index = pd.to_datetime(P.index); P = P.sort_index()
    fz = np.load(ROOT / "outputs/forecasts/lear_ens.npz"); cz = np.load(ROOT / "outputs/forecasts/chronos.npz")
    days = pd.to_datetime(fz["days"]).intersection(pd.to_datetime(cz["days"]))
    FL = pd.DataFrame(fz["ens"], index=pd.to_datetime(fz["days"])).loc[days].values
    cidx = {x: i for i, x in enumerate(pd.to_datetime(cz["days"]))}
    CQ = cz["quantiles"][[cidx[x] for x in days]]
    w = json.load(open(ROOT / "outputs/m3_metrics.json"))["upgrades"]["blend_weight_lear"]
    R = pd.read_csv(ROOT / "outputs/m4_daily_results.csv", index_col=0, parse_dates=True)
    M4 = json.load(open(ROOT / "outputs/m4_metrics.json")); M3 = json.load(open(ROOT / "outputs/m3_metrics.json"))
    bid_file = sorted((ROOT / "outputs").glob("bid_*.csv"))[-1]
    return P, days, FL, CQ, w, R, M4, M3, pd.read_csv(bid_file), bid_file.stem.replace("bid_", "")


P, DAYS, FL, CQ, W, R, M4, M3, BID, BID_DATE = load()
FORECASTS = {"Copilot blend": W * FL + (1 - W) * CQ[:, :, 4], "LEAR ensemble": FL, "Chronos (deep learning)": CQ[:, :, 4],
             "Tomorrow = today": P.shift(1).loc[DAYS].values}
ACT = P.loc[DAYS].values
X = np.arange(96) / 4
SLOTS = [f"{h // 4:02d}:{15 * (h % 4):02d}" for h in range(96)]

# ---------------------------------------------------------------- sidebar
st.sidebar.markdown('<div style="font-size:1.15rem;font-weight:700;margin:0.2rem 0 0.1rem 0;">Battery Dispatch Copilot</div>'
                    '<div style="font-size:0.8rem;opacity:0.75;margin-bottom:1rem;">IEX Day-Ahead Market · Team D01</div>', unsafe_allow_html=True)
PAGE = st.sidebar.radio("Navigate", ["Overview", "Tomorrow's bid", "Day replay", "Scenario lab", "Model lab", "Risk and validation", "Assistant"],
                        label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.markdown('<div style="font-weight:600;margin-bottom:0.3rem;">Battery</div>', unsafe_allow_html=True)
MW = st.sidebar.slider("Power, MW", 5, 50, 10, 5)
HRS = st.sidebar.select_slider("Duration, hours", [1, 2, 3, 4], value=2)
RTE = st.sidebar.slider("Round-trip efficiency", 0.80, 0.95, 0.88, 0.01)
WEAR = st.sidebar.slider("Wear cost, ₹ per MWh sold", 0, 2000, 1000, 100)
FEE = st.sidebar.slider("Exchange fee, ₹ per MWh each way", 0, 50, 0, 5)
ROUNDS = st.sidebar.radio("Max buy–sell rounds per day", [1, 2], index=1, horizontal=True)
MWH = MW * HRS
st.sidebar.caption(f"{MW} MW / {MWH} MWh. Every change re-optimises the plan instantly.")


def plan(prices):
    return bt.solve_custom(np.asarray(prices, float), mw=MW, mwh=MWH, rte=RTE, deg=WEAR, cycles=ROUNDS, fee=FEE)


def pnl(c, d, actual):
    return bt.settle_custom(c, d, np.asarray(actual, float), WEAR, FEE)


def plan_figure(title, forecast, c, d, soc, actual=None, low=None, high=None, naive=None, height=520):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.62, 0.38], vertical_spacing=0.05, specs=[[{}], [{"secondary_y": True}]])
    if low is not None:
        fig.add_trace(go.Scatter(x=X, y=high, line=dict(width=0), showlegend=False, hoverinfo="skip"), 1, 1)
        fig.add_trace(go.Scatter(x=X, y=low, fill="tonexty", fillcolor="rgba(37,99,235,0.12)", line=dict(width=0), name="likely range (10–90%)", hoverinfo="skip"), 1, 1)
    if naive is not None:
        fig.add_trace(go.Scatter(x=X, y=naive, name="tomorrow = today", line=dict(color="#94a3b8", width=1.2)), 1, 1)
    if actual is not None:
        fig.add_trace(go.Scatter(x=X, y=actual, name="actual price", line=dict(color=INK, width=2)), 1, 1)
    fig.add_trace(go.Scatter(x=X, y=forecast, name="copilot forecast", line=dict(color=BLUE, width=2.6)), 1, 1)
    fig.add_trace(go.Bar(x=X, y=c * 4, name="buy, MW", marker_color=GREEN, width=0.22), 2, 1)
    fig.add_trace(go.Bar(x=X, y=-d * 4, name="sell, MW", marker_color=RED, width=0.22), 2, 1)
    fig.add_trace(go.Scatter(x=X, y=soc, name="stored, MWh", line=dict(color=NAVY, width=1.8, dash="dot")), 2, 1, secondary_y=True)
    fig.update_layout(title=dict(text=title, font=dict(size=15), y=0.98), height=height, barmode="relative", margin=dict(l=10, r=10, t=95, b=10), legend=dict(y=1.09))
    fig.update_yaxes(title_text="₹ per MWh", row=1, col=1); fig.update_yaxes(title_text="MW", row=2, col=1)
    fig.update_yaxes(title_text="MWh", row=2, col=1, secondary_y=True, showgrid=False)
    fig.update_xaxes(tickvals=list(range(0, 25, 3)), ticktext=[f"{h:02d}:00" for h in range(0, 25, 3)], row=2, col=1)
    return fig


@st.cache_data(show_spinner=False)
def year_run(name, mw, mwh, rte, wear, rounds, fee, period="test"):
    F = FORECASTS[name]; idx = np.where(DAYS >= pd.Timestamp("2025-11-22"))[0] if period == "test" else np.where(DAYS < pd.Timestamp("2025-11-22"))[0]
    out = []
    for i in idx:
        c, d, _ = bt.solve_custom(F[i], mw=mw, mwh=mwh, rte=rte, deg=wear, cycles=rounds, fee=fee)
        out.append(bt.settle_custom(c, d, ACT[i], wear, fee))
    return pd.Series(out, index=DAYS[idx])


@st.cache_data(show_spinner=False)
def perfect_run(mw, mwh, rte, wear, rounds, fee, period="test"):
    idx = np.where(DAYS >= pd.Timestamp("2025-11-22"))[0] if period == "test" else np.where(DAYS < pd.Timestamp("2025-11-22"))[0]
    out = []
    for i in idx:
        c, d, _ = bt.solve_custom(ACT[i], mw=mw, mwh=mwh, rte=rte, deg=wear, cycles=rounds, fee=fee)
        out.append(bt.settle_custom(c, d, ACT[i], wear, fee))
    return pd.Series(out, index=DAYS[idx])


TEST = R[R.index >= "2025-11-22"]
T4 = M4["test"]; G2 = M4["tests"]["test"]["blend_vs_today_2"]

# ================================================================= OVERVIEW
if PAGE == "Overview":
    header("Overview", "Plan tomorrow's battery trades in one click",
           "The copilot forecasts tomorrow's price for every 15-minute slot on the Indian Energy Exchange, then finds the most profitable "
           "buy and sell plan for the battery and writes the bid. Results below are from a full year it never saw during development.")
    c1, c2, c3, c4 = st.columns(4)
    with c1: card("Profit per day, test year", rupees(T4["blend_2"]), f"+{rupees(G2['gain'])} vs tomorrow = today", "pos")
    with c2: card("Profit per year", f"₹{T4['blend_2'] * 365 / 1e7:.2f} crore", "10 MW / 20 MWh battery", "neu")
    with c3: card("Share of the best possible", f"{M4['share_test']['blend']:.1%}", "perfect knowledge of tomorrow = 100%", "neu")
    with c4: card("Months ahead of the simple plan", f"{M4['months_positive']} of {M4['months_total']}", f"chance it is luck < {max(G2['p'], 0.001):.1%}", "pos")
    st.markdown('<div class="section">How it works</div>', unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    steps = [("Forecast", "A blend of LEAR, the standard research model for electricity prices, and Chronos, a deep-learning foundation model, "
              "predicts all 96 prices for tomorrow with a likely range."),
             ("Optimise", "A linear program finds the exact profit-maximising plan within the battery's power, storage, efficiency and wear limits, in about a millisecond."),
             ("Bid", "The plan becomes 96 buy or sell orders with price limits from the forecast range, ready to submit to the exchange.")]
    for col, (i, (t, b)) in zip([s1, s2, s3], enumerate(steps, 1)):
        with col: st.markdown(f'<div class="card"><span class="step-num">{i}</span><span class="step-title">{t}</span><div class="step-body">{b}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section">Two years out of sample</div>', unsafe_allow_html=True)
    fig = go.Figure()
    for col, lbl, colr in [("blend_2", "Copilot", BLUE), ("today_sun_2", "Tomorrow = today, with Sunday fix", "#94a3b8"), ("fixed", "Fixed timetable from the canvas", RED)]:
        fig.add_trace(go.Scatter(x=R.index, y=(R[col] - R.today_2).cumsum() / 1e5, name=lbl, line=dict(color=colr, width=2.2)))
    fig.add_vrect(x0=pd.Timestamp("2025-11-22"), x1=R.index.max(), fillcolor="#eef2ff", opacity=0.5, layer="below", line_width=0, annotation_text="test year", annotation_position="top left")
    fig.update_layout(height=360, yaxis_title="₹ lakh, cumulative vs tomorrow = today", yaxis_range=[-60, 35])
    st.plotly_chart(fig, use_container_width=True)
    i1, i2, i3 = st.columns(3)
    with i1: card("Biggest lever", "Second daily round", "Worth up to ₹56k a day on winter double-peak days", "neu")
    with i2: card("Hardest day", "Sunday", f"Copilot gains {rupees(M4['segments']['Sun']['gain'])} a day here", "pos")
    with i3: card("Weak spot to fix", "Thursday", f"Trails the simple plan by {rupees(-M4['segments']['Thu']['gain'])} a day", "neg")

# ================================================================= TOMORROW
elif PAGE == "Tomorrow's bid":
    header("Tomorrow's bid", f"Bid for {pd.Timestamp(BID_DATE):%A %d %B %Y}",
           "The live forecast for the first delivery day after our data, the optimal plan for your battery settings, and exchange-ready orders.")
    fc = BID.forecast_rs_mwh.values; lo, hi = BID.low_rs_mwh.values, BID.high_rs_mwh.values
    c, d, soc = plan(fc)
    c1, c2, c3, c4 = st.columns(4)
    with c1: card("Expected profit", rupees(pnl(c, d, fc)), "at forecast prices")
    with c2: card("Energy bought", f"{c.sum():.1f} MWh", f"{(c > 1e-6).sum()} slots")
    with c3: card("Energy sold", f"{d.sum():.1f} MWh", f"{(d > 1e-6).sum()} slots")
    with c4: card("Rounds used", f"{d.sum() / np.sqrt(RTE) / (0.9 * MWH):.2f}", f"limit {ROUNDS}")
    st.plotly_chart(plan_figure("Forecast with likely range, and the battery plan", fc, c, d, soc, low=lo, high=hi, naive=P.iloc[-1].values), use_container_width=True)
    st.markdown('<div class="section">Exchange orders</div>', unsafe_allow_html=True)
    guard = st.toggle("Add price limits from the forecast range (recommended)", value=True,
                      help="Buy orders cap the price at the high end of the likely range; sell orders set a floor at the low end. "
                           "This protects the trader if the clearing price lands far from the forecast.")
    orders = []
    for k in range(96):
        if c[k] > 1e-6: orders.append({"slot": SLOTS[k], "block": k + 1, "side": "BUY", "MW": round(c[k] * 4, 2), "price limit ₹/MWh": round(hi[k]) if guard else "market"})
        if d[k] > 1e-6: orders.append({"slot": SLOTS[k], "block": k + 1, "side": "SELL", "MW": round(d[k] * 4, 2), "price limit ₹/MWh": round(lo[k]) if guard else "market"})
    od = pd.DataFrame(orders)
    a, b = st.columns([3, 1.1])
    with a: st.dataframe(od, hide_index=True, use_container_width=True, height=300)
    with b:
        st.download_button("Download orders (CSV)", od.to_csv(index=False), file_name=f"orders_{BID_DATE}.csv", mime="text/csv", use_container_width=True)
        full = pd.DataFrame({"block": range(1, 97), "slot": SLOTS, "forecast": fc.round(0), "low": lo.round(0), "high": hi.round(0),
                             "buy_MW": (c * 4).round(2), "sell_MW": (d * 4).round(2), "stored_MWh": soc.round(2)})
        st.download_button("Download full 96-slot plan (CSV)", full.to_csv(index=False), file_name=f"plan_{BID_DATE}.csv", mime="text/csv", use_container_width=True)
        st.markdown(f'<div class="note">{len(od)} orders. Format simplified from the IEX day-ahead bid: one order per active 15-minute block.</div>', unsafe_allow_html=True)

# ================================================================= REPLAY
elif PAGE == "Day replay":
    header("Day replay", "How would the copilot have traded on any day?",
           "Pick any of the 730 validation and test days. The plan is built from the forecast, then paid at the real prices.")
    a, b = st.columns([2, 1])
    with a: day = st.select_slider("Delivery day", options=list(DAYS), value=pd.Timestamp(M4["example_day"]["date"]), format_func=lambda x: x.strftime("%a %d %b %Y"))
    with b: model = st.selectbox("Forecast used for the plan", list(FORECASTS), index=0)
    i = list(DAYS).index(day); F = FORECASTS[model][i]; actual = ACT[i]; naive = FORECASTS["Tomorrow = today"][i]
    c, d, soc = plan(F); cn, dn, _ = plan(naive); cp, dp, _ = plan(actual)
    ours, base, best = pnl(c, d, actual), pnl(cn, dn, actual), pnl(cp, dp, actual)
    k1, k2, k3, k4 = st.columns(4)
    with k1: card(model, rupees(ours), f"{ours - base:+,.0f} vs tomorrow = today", "pos" if ours >= base else "neg")
    with k2: card("Tomorrow = today", rupees(base))
    with k3: card("Perfect knowledge", rupees(best), "the ceiling")
    with k4: card("Share of the best possible", f"{ours / best:.1%}" if best > 0 else "–")
    st.plotly_chart(plan_figure(f"{day:%A %d %b %Y}", F, c, d, soc, actual=actual, low=CQ[i, :, 0], high=CQ[i, :, 8], naive=naive), use_container_width=True)

# ================================================================= SCENARIO LAB
elif PAGE == "Scenario lab":
    header("Scenario lab", "What is a battery worth under different designs?",
           "Run the copilot on the full test year for up to three battery designs and compare. Each run solves 365 daily plans.")
    cols = st.columns(3); configs = []
    defaults = [(10, 2, 0.88, 1000, 2), (10, 4, 0.88, 1000, 2), (20, 2, 0.90, 700, 2)]
    for j, col in enumerate(cols):
        with col:
            st.markdown(f'<span class="pill">Design {"ABC"[j]}</span>', unsafe_allow_html=True)
            mw = st.number_input("Power, MW", 5, 100, defaults[j][0], 5, key=f"mw{j}")
            hrs = st.selectbox("Duration, hours", [1, 2, 3, 4], index=[1, 2, 3, 4].index(defaults[j][1]), key=f"h{j}")
            rte = st.number_input("Round-trip efficiency", 0.80, 0.95, defaults[j][2], 0.01, key=f"r{j}")
            wear = st.number_input("Wear, ₹/MWh", 0, 3000, defaults[j][3], 100, key=f"w{j}")
            configs.append((mw, mw * hrs, rte, wear))
    if st.button("Run the test year for all three designs", type="primary"):
        rows = []
        with st.spinner("Solving 2,190 daily plans…"):
            for j, (mw, mwh, rte, wear) in enumerate(configs):
                s = year_run("Copilot blend", mw, mwh, rte, wear, 2, 0); p = perfect_run(mw, mwh, rte, wear, 2, 0)
                rows.append({"design": f"Design {'ABC'[j]}: {mw} MW / {mwh} MWh", "profit ₹/day": s.mean(), "₹ crore/year": s.mean() * 365 / 1e7,
                             "per MWh of storage, ₹/day": s.mean() / mwh, "share of best": s.sum() / p.sum(), "worst 5% day, ₹": s.quantile(0.05)})
        res = pd.DataFrame(rows).set_index("design")
        st.dataframe(res.style.format({"profit ₹/day": "₹{:,.0f}", "₹ crore/year": "{:.2f}", "per MWh of storage, ₹/day": "₹{:,.0f}", "share of best": "{:.1%}", "worst 5% day, ₹": "₹{:,.0f}"}),
                     use_container_width=True)
        fig = go.Figure(go.Bar(x=res.index, y=res["₹ crore/year"], marker_color=[BLUE, NAVY, AMBER], text=[f"₹{v:.2f} cr" for v in res["₹ crore/year"]], textposition="outside"))
        fig.update_layout(height=320, yaxis_title="₹ crore per year", showlegend=False); st.plotly_chart(fig, use_container_width=True)
        st.markdown('<div class="note">Profit after wear, before fixed costs, at actual test-year prices. Price-taker assumption holds up to about 300 MW (3% of the thinnest block).</div>', unsafe_allow_html=True)

# ================================================================= MODEL LAB
elif PAGE == "Model lab":
    header("Model lab", "Which forecaster makes the most money?",
           "Every forecaster's plan is settled at real prices with your battery settings. Price accuracy and profit are not the same thing.")
    period = st.radio("Period", ["test", "validation"], horizontal=True)
    per = "test" if period == "test" else "validate"
    with st.spinner("Running the year for four forecasters…"):
        runs = {m: year_run(m, MW, MWH, RTE, WEAR, ROUNDS, FEE, per) for m in FORECASTS}
        perf = perfect_run(MW, MWH, RTE, WEAR, ROUNDS, FEE, per)
    idx = runs["Copilot blend"].index; pos = [list(DAYS).index(x) for x in idx]; cap = ACT[pos] >= 10000
    rows = []
    for m, s in runs.items():
        err = np.abs(FORECASTS[m][pos] - ACT[pos])[~cap].mean()
        rows.append({"forecaster": m, "profit ₹/day": s.mean(), "vs tomorrow = today": s.mean() - runs["Tomorrow = today"].mean(), "share of best": s.sum() / perf.sum(), "price error ₹/MWh": err})
    tab = pd.DataFrame(rows).set_index("forecaster")
    a, b = st.columns([1.15, 1])
    with a:
        st.dataframe(tab.style.format({"profit ₹/day": "₹{:,.0f}", "vs tomorrow = today": "{:+,.0f}", "share of best": "{:.1%}", "price error ₹/MWh": "{:,.0f}"}), use_container_width=True)
        st.markdown('<div class="note">Price error is the average miss on blocks below the ₹10,000 cap. Chronos misses prices about as much as copying yesterday, '
                    'yet earns more: it gets the shape of the day right, and the shape is what a battery trades on.</div>', unsafe_allow_html=True)
    with b:
        fig = go.Figure()
        for m, colr in zip(tab.index, [BLUE, NAVY, AMBER, "#94a3b8"]):
            fig.add_trace(go.Scatter(x=[tab.loc[m, "price error ₹/MWh"]], y=[tab.loc[m, "profit ₹/day"]], mode="markers+text", text=[m], textposition="top center",
                                     marker=dict(size=16, color=colr), name=m, showlegend=False))
        fig.update_layout(height=330, xaxis_title="price error, ₹/MWh (lower is better)", yaxis_title="profit, ₹/day", hovermode="closest", title="Accuracy vs money")
        st.plotly_chart(fig, use_container_width=True)
    fig = go.Figure()
    for m, colr in zip(FORECASTS, [BLUE, NAVY, AMBER, "#94a3b8"]):
        if m == "Tomorrow = today": continue
        fig.add_trace(go.Scatter(x=idx, y=(runs[m] - runs["Tomorrow = today"]).cumsum() / 1e5, name=m, line=dict(color=colr, width=2)))
    fig.update_layout(height=330, yaxis_title="₹ lakh, cumulative vs tomorrow = today", title="Extra profit over the period")
    st.plotly_chart(fig, use_container_width=True)

# ================================================================= RISK
elif PAGE == "Risk and validation":
    header("Risk and validation", "Is the gain real, steady and safe?",
           "Statistics on days the models never saw: confidence ranges that resample whole weeks, Diebold–Mariano tests, monthly results, bad days and stress tests.")
    tv = M4["tests"]["validate"]["blend_vs_today_2"]
    c1, c2, c3, c4 = st.columns(4)
    with c1: card("Extra profit, test year", f"+{rupees(G2['gain'])}/day", f"95% range {G2['ci'][0]:,} to {G2['ci'][1]:,}", "pos")
    with c2: card("Extra profit, validation year", f"+{rupees(tv['gain'])}/day", f"95% range {tv['ci'][0]:,} to {tv['ci'][1]:,}", "pos")
    with c3: card("Worst 5% of days", rupees(M4["risk"]["blend_2"]["worst 5% of days, ₹"]), f"simple plan {rupees(M4['risk']['today_2']['worst 5% of days, ₹'])}")
    with c4: card("Losing days", f"{M4['risk']['blend_2']['losing days']}", f"fixed timetable: {M4['risk']['fixed']['losing days']}", "pos")
    m = R.copy(); m["gain"] = m.blend_2 - m.today_2; mon = m.groupby(m.index.to_period("M")).gain.mean()
    a, b = st.columns(2)
    with a:
        fig = go.Figure(go.Bar(x=[p.strftime("%b %y") for p in mon.index], y=mon.values, marker_color=[GREEN if v > 0 else RED for v in mon.values]))
        fig.update_layout(height=330, title="Extra profit per day, each month", yaxis_title="₹/day"); st.plotly_chart(fig, use_container_width=True)
    with b:
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=TEST.today_2 / 1000, name="Tomorrow = today", marker_color="#94a3b8", opacity=0.6, xbins=dict(size=5)))
        fig.add_trace(go.Histogram(x=TEST.blend_2 / 1000, name="Copilot", marker_color=BLUE, opacity=0.6, xbins=dict(size=5)))
        fig.update_layout(height=330, barmode="overlay", title="Daily profit, test year", xaxis_title="₹ thousand per day", yaxis_title="days", hovermode="closest")
        st.plotly_chart(fig, use_container_width=True)
    tdf = pd.DataFrame({k.replace("blend_vs_", "vs "): {"extra ₹/day": v["gain"], "95% range": f"{v['ci'][0]:,} to {v['ci'][1]:,}", "chance it is luck": f"{v['p']:.4f}",
                        "days better": f"{v['share_days_better']:.0%}"} for k, v in M4["tests"]["test"].items()}).T
    tdf.index = ["vs tomorrow = today (2 rounds)", "vs tomorrow = today (1 round)", "vs tomorrow = today + Sunday fix", "vs fixed timetable"]
    st.markdown('<div class="section">Significance tests, test year</div>', unsafe_allow_html=True); st.dataframe(tdf, use_container_width=True)
    st.markdown('<div class="section">Stress tests, test year</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(M4["sensitivity"]).set_index("setting").style.format({"assistant ₹/day": "₹{:,.0f}", "tomorrow = today ₹/day": "₹{:,.0f}", "extra ₹/day": "{:+,.0f}", "share of best": "{:.1%}"}),
                 use_container_width=True)

# ================================================================= ASSISTANT
elif PAGE == "Assistant":
    header("Assistant", "Ask the copilot",
           "Ask about the results, the method, the risks or how to use the app. Answers are grounded in the project's own numbers.")
    import os, re
    t_, s_, rk = M4["test"], M4["share_test"], M4["risk"]["blend_2"]; up = M3.get("upgrades", {})
    FACTS = "\n".join([
        f"- Test year (22 Nov 2025 to 21 Nov 2026), 10 MW / 20 MWh battery, wear Rs 1,000/MWh: copilot earns Rs {t_['blend_2']:,.0f}/day (Rs {t_['blend_2'] * 365 / 1e7:.2f} crore/year), {s_['blend']:.1%} of perfect foresight.",
        f"- Baselines per day: fixed timetable Rs {t_['fixed']:,.0f}; tomorrow = today (2 rounds) Rs {t_['today_2']:,.0f}; perfect knowledge Rs {t_['perfect_2']:,.0f}.",
        f"- Gain vs tomorrow = today: Rs {G2['gain']:,}/day test (95% range {G2['ci'][0]:,} to {G2['ci'][1]:,}, Diebold-Mariano p = {G2['p']:.4f}); validation year Rs {M4['tests']['validate']['blend_vs_today_2']['gain']:,}/day. Ahead in {M4['months_positive']} of {M4['months_total']} months.",
        f"- Gain vs fixed timetable: Rs {M4['tests']['test']['blend_vs_fixed_1']['gain']:,}/day.",
        f"- Risk: worst 5% of test days Rs {rk['worst 5% of days, ₹']:,}; worst month Rs {rk['worst month avg, ₹/day']:,}/day; {rk['losing days']} losing days.",
        f"- By weekday: Sunday +Rs {M4['segments']['Sun']['gain']:,}/day (best), Thursday {M4['segments']['Thu']['gain']:,}/day (weak spot). Second round used on {M4['share_days_two_rounds']:.0%} of days.",
        "- Stress tests (all still ahead of tomorrow = today): " + "; ".join(f"{r['setting']}: +Rs {r['extra ₹/day']:,}/day" for r in M4["sensitivity"]) + ".",
        f"- Method: forecast = {W:.0%} LEAR ensemble (Lago et al. 2021 research model) + {1 - W:.0%} Chronos-Bolt (Amazon deep-learning foundation model, used as it comes); "
        "plan = linear program (power, storage 2-20 MWh, 88% round trip, up to 2 rounds/day); bid = 96 orders with price limits from the forecast range.",
        f"- Chronos price error is about the same as copying yesterday (Rs {up.get('mae', {}).get('chr', 649)} vs {up.get('mae', {}).get('lag1', 633)} per MWh) but it earns more because it gets the daily shape right.",
        "- Weather forecasts did not help; the weekly calendar explains far more. Prices are capped at Rs 10,000/MWh.",
        f"- Tomorrow's bid ({BID_DATE}): forecast-based plan in the Tomorrow's bid page. Current app settings: {MW} MW, {MWH} MWh, efficiency {RTE}, wear Rs {WEAR}, fee Rs {FEE}, max rounds {ROUNDS}.",
    ])
    SYSTEM = ("You are the assistant inside the Battery Dispatch Copilot, a tool for the trading head of a battery on the Indian Energy Exchange "
              "Day-Ahead Market. Pages: Overview, Tomorrow's bid, Day replay, Scenario lab, Model lab, Risk and validation. "
              "Answer in plain, simple English in 2 to 5 short sentences. Use only the facts below for numbers; if they do not answer the question, say so "
              "and point to the right page.\nFACTS:\n" + FACTS)
    OLLAMA_URL, OLLAMA_MODEL = os.environ.get("OLLAMA_HOST", "http://localhost:11434"), os.environ.get("OLLAMA_MODEL", "qwen3:4b")

    def ollama_ready():
        try:
            import requests
            tags = requests.get(f"{OLLAMA_URL}/api/tags", timeout=1.5).json().get("models", [])
            return any(m.get("name", "").startswith(OLLAMA_MODEL) for m in tags)
        except Exception:
            return False

    def guide_answer(q):
        ql = q.lower(); t = M4["test"]; s = M4["share_test"]
        rules = [
            (["how", "work", "method", "model"], f"Three steps. 1) Forecast: a blend of LEAR (a research model for electricity prices) and Chronos (a deep-learning "
             f"foundation model), {W:.0%} / {1 - W:.0%}. 2) Optimise: a linear program finds the most profitable buy and sell plan within the battery limits. "
             "3) Bid: the plan becomes exchange orders. See Overview and Model lab."),
            (["profit", "earn", "money", "revenue", "much"], f"On the test year the copilot earns ₹{t['blend_2']:,.0f} a day (about ₹{t['blend_2'] * 365 / 1e7:.2f} crore a year), "
             f"{s['blend']:.1%} of what perfect knowledge of tomorrow would earn, and ₹{G2['gain']:,.0f} a day more than assuming tomorrow = today."),
            (["real", "luck", "significant", "test", "valid"], f"Yes. The gain over tomorrow = today has a 95% range of ₹{G2['ci'][0]:,} to ₹{G2['ci'][1]:,} a day on the test year, "
             f"the Diebold–Mariano chance it is luck is {G2['p']:.4f}, and it is ahead in {M4['months_positive']} of {M4['months_total']} months. See Risk and validation."),
            (["risk", "bad", "worst", "loss", "lose"], f"On the worst 5% of test days it still earns ₹{M4['risk']['blend_2']['worst 5% of days, ₹']:,}, its worst month averages "
             f"₹{M4['risk']['blend_2']['worst month avg, ₹/day']:,} a day, and it had {M4['risk']['blend_2']['losing days']} losing days."),
            (["sunday", "weekday", "thursday"], f"Sundays gain most (+₹{M4['segments']['Sun']['gain']:,} a day) because copying Saturday is a poor guess. Thursdays are the weak "
             f"spot (₹{-M4['segments']['Thu']['gain']:,} a day behind)."),
            (["second", "round", "cycle", "two"], f"The copilot runs a second round on {M4['share_days_two_rounds']:.0%} of days, only when its forecast says it pays for the wear. "
             "It matters most in winter, when there is a morning peak as well as an evening one."),
            (["chronos", "deep", "ai", "lear", "blend"], "Chronos is Amazon's pretrained transformer for time series, used as it comes. LEAR is the standard research model "
             "(Lago et al., 2021). Chronos misses prices about as much as copying yesterday but earns more, because it gets the daily shape right. The blend earns most. See Model lab."),
            (["bid", "order", "tomorrow", "download"], "Open Tomorrow's bid: it shows the forecast with a likely range, the plan, and exchange orders with price limits. "
             "Use the download buttons for the orders or the full 96-slot plan."),
            (["size", "design", "scenario", "mw", "hour"], "Open Scenario lab to compare up to three battery designs over the full test year, or change the sliders on the left to re-plan any page."),
            (["weather"], "Weather forecasts did not help: day-to-day changes in sun and temperature barely move prices, and LEAR earned the same with or without them."),
        ]
        best = max(rules, key=lambda r: sum(w in ql for w in r[0]))
        return best[1] if any(w in ql for w in best[0]) else ("I can explain the results, the method, the risk, the bid or the battery designs. "
                                                              "Try: 'How much does it earn?', 'Is the gain real?', 'Why blend two models?'")

    live = ollama_ready()
    st.markdown(f'<span class="pill">{"Local AI · Ollama " + OLLAMA_MODEL if live else "Guide mode"}</span>'
                f'<span class="note">{"Runs on this machine; no data leaves the laptop." if live else "Start Ollama (ollama serve) to switch on the local AI model. Guide mode answers from the project results."}</span>',
                unsafe_allow_html=True)
    if "chat" not in st.session_state: st.session_state.chat = []
    sugg = st.columns(4)
    for col, q in zip(sugg, ["How much does it earn?", "Is the gain real or luck?", "Why blend two models?", "What are the risks?"]):
        if col.button(q, use_container_width=True): st.session_state.pending = q
    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    q = st.chat_input("Ask about results, method, risk or the bid") or st.session_state.pop("pending", None)
    if q:
        st.session_state.chat.append({"role": "user", "content": q})
        with st.chat_message("user"): st.markdown(q)
        with st.chat_message("assistant"):
            if live:
                import requests
                msgs = [{"role": "system", "content": SYSTEM}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat[-8:]]

                def stream_text():
                    buf = []
                    with requests.post(f"{OLLAMA_URL}/api/chat", json={"model": OLLAMA_MODEL, "messages": msgs, "stream": True, "think": True,
                                                                       "options": {"temperature": 0.2, "num_ctx": 8192, "num_predict": 1500}}, stream=True, timeout=120) as r:
                        r.raise_for_status()
                        for line in r.iter_lines():
                            if not line: continue
                            chunk = json.loads(line)
                            piece = chunk.get("message", {}).get("content", "")   # reasoning arrives separately in message.thinking and is not shown
                            if piece: yield piece
                            if chunk.get("done"): break
                try:
                    with st.spinner("Thinking on the local model…"):
                        first = stream_text()
                    answer = st.write_stream(first)
                    answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.S).strip() or guide_answer(q)
                except Exception:
                    answer = "The local AI model did not respond. " + guide_answer(q); st.markdown(answer)
            else:
                answer = guide_answer(q); st.markdown(answer)
        st.session_state.chat.append({"role": "assistant", "content": answer})

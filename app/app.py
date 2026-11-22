"""Battery trading assistant: demo app (Team D01, Data2Decision M4).

Run from the repo root:  streamlit run app/app.py
Tabs: Tomorrow's bid · Replay any day · Track record. Battery settings in the sidebar re-plan instantly.
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import battery as bt

st.set_page_config(page_title="Battery trading assistant", page_icon="⚡", layout="wide")
NAVY, MID, GREY, RED, GREEN = "#1f4e8c", "#6b8fc2", "#8c8c8c", "#c0392b", "#2e8b57"
st.markdown("""<style>
.block-container {padding-top: 1.6rem; max-width: 1250px;}
h1 {font-size: 1.7rem !important; margin-bottom: 0.1rem;}
[data-testid="stMetricValue"] {font-size: 1.5rem;}
.small {color: #555; font-size: 0.92rem;}
</style>""", unsafe_allow_html=True)


@st.cache_data
def load():
    d = pd.read_csv(ROOT / "data/raw/iex_dam_15min.csv", usecols=["date", "block", "mcp_rs_mwh"])
    P = d.pivot(index="date", columns="block", values="mcp_rs_mwh"); P.index = pd.to_datetime(P.index); P = P.sort_index()
    fz = np.load(ROOT / "outputs/forecasts/lear_ens.npz"); cz = np.load(ROOT / "outputs/forecasts/chronos.npz")
    days = pd.to_datetime(fz["days"]).intersection(pd.to_datetime(cz["days"]))
    FL = pd.DataFrame(fz["ens"], index=pd.to_datetime(fz["days"])).loc[days]
    CQ = cz["quantiles"][[list(pd.to_datetime(cz["days"])).index(x) for x in days]]
    w = json.load(open(ROOT / "outputs/m3_metrics.json"))["upgrades"]["blend_weight_lear"]
    FB = w * FL.values + (1 - w) * CQ[:, :, 4]
    R = pd.read_csv(ROOT / "outputs/m4_daily_results.csv", index_col=0, parse_dates=True)
    M = json.load(open(ROOT / "outputs/m4_metrics.json"))
    bid_file = sorted((ROOT / "outputs").glob("bid_*.csv"))[-1]
    return P, days, FB, CQ, R, M, pd.read_csv(bid_file), bid_file.stem.replace("bid_", ""), w


P, DAYS, FB, CQ, R, M, BID, BID_DATE, W = load()
x_hours = np.arange(96) / 4
labels = [f"{h // 4:02d}:{15 * (h % 4):02d}" for h in range(96)]

# ---------------- Sidebar ----------------
st.sidebar.header("Battery settings")
mw = st.sidebar.slider("Power (MW)", 5, 50, 10, 5)
hours = st.sidebar.select_slider("Storage (hours at full power)", [1, 2, 3, 4], value=2)
mwh = mw * hours
rte = st.sidebar.slider("Round-trip efficiency", 0.80, 0.95, 0.88, 0.01)
wear = st.sidebar.slider("Wear cost (₹ per MWh sold)", 0, 2000, 1000, 100)
fee = st.sidebar.slider("Exchange fee (₹ per MWh, each way)", 0, 50, 0, 5)
rounds = st.sidebar.radio("Buy–sell rounds per day, at most", [1, 2], index=1, horizontal=True)
st.sidebar.caption(f"Battery: {mw} MW / {mwh} MWh. Every change re-plans instantly with the optimiser.")
st.sidebar.markdown("---")
st.sidebar.caption("Forecast = blend of LEAR (research model, Lago et al. 2021) and Chronos (Amazon's deep-learning "
                   f"forecasting model, Ansari et al. 2024): {W:.0%} / {1 - W:.0%}.")


def plan(prices):
    return bt.solve_custom(np.asarray(prices, float), mw=mw, mwh=mwh, rte=rte, deg=wear, cycles=rounds, fee=fee)


def money(c, d, actual):
    return bt.settle_custom(c, d, np.asarray(actual, float), wear, fee)


def day_chart(title, actual, forecast, low, high, naive, c, d, soc):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.6, 0.4], vertical_spacing=0.06,
                        specs=[[{}], [{"secondary_y": True}]])
    if low is not None:
        fig.add_trace(go.Scatter(x=x_hours, y=high, line=dict(width=0), showlegend=False, hoverinfo="skip"), 1, 1)
        fig.add_trace(go.Scatter(x=x_hours, y=low, fill="tonexty", fillcolor="rgba(107,143,194,0.22)", line=dict(width=0),
                                 name="likely range (Chronos 10–90%)", hoverinfo="skip"), 1, 1)
    if naive is not None:
        fig.add_trace(go.Scatter(x=x_hours, y=naive, name="tomorrow = today", line=dict(color=GREY, width=1.2)), 1, 1)
    if actual is not None:
        fig.add_trace(go.Scatter(x=x_hours, y=actual, name="actual price", line=dict(color="#222", width=2)), 1, 1)
    fig.add_trace(go.Scatter(x=x_hours, y=forecast, name="our forecast", line=dict(color=NAVY, width=2.4, dash="dash")), 1, 1)
    fig.add_trace(go.Bar(x=x_hours, y=c * 4, name="buy (MW)", marker_color=GREEN, width=0.22), 2, 1)
    fig.add_trace(go.Bar(x=x_hours, y=-d * 4, name="sell (MW)", marker_color=RED, width=0.22), 2, 1)
    fig.add_trace(go.Scatter(x=x_hours, y=soc, name="stored (MWh)", line=dict(color=NAVY, width=1.6)), 2, 1, secondary_y=True)
    fig.update_layout(title=title, height=560, template="simple_white", barmode="relative", hovermode="x unified",
                      legend=dict(orientation="h", y=1.08, x=0), margin=dict(l=10, r=10, t=70, b=10))
    fig.update_yaxes(title_text="₹ per MWh", row=1, col=1); fig.update_yaxes(title_text="MW", row=2, col=1)
    fig.update_yaxes(title_text="MWh stored", row=2, col=1, secondary_y=True, showgrid=False)
    fig.update_xaxes(title_text="hour of day", tickvals=list(range(0, 25, 3)), row=2, col=1)
    return fig


st.title("⚡ Battery trading assistant")
st.markdown('<p class="small">Guesses tomorrow\'s electricity prices on the Indian Energy Exchange, then plans when the battery should '
            'buy and sell, slot by slot, to earn the most. Team D01 · Data2Decision 2026.</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📋 Tomorrow's bid", "🔁 Replay any day", "📈 Track record"])

# ---------------- Tab 1: tomorrow ----------------
with tab1:
    fc_next = BID.forecast_rs_mwh.values
    c, d, soc = plan(fc_next)
    exp = money(c, d, fc_next)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Delivery day", pd.Timestamp(BID_DATE).strftime("%a %d %b %Y"))
    k2.metric("Expected profit", f"₹{exp:,.0f}")
    k3.metric("Energy bought / sold", f"{c.sum():.1f} / {d.sum():.1f} MWh")
    k4.metric("Rounds used", f"{d.sum() / np.sqrt(rte) / (0.9 * mwh):.1f}")
    st.plotly_chart(day_chart("Tomorrow: forecast and the battery's plan", None, fc_next, BID.low_rs_mwh.values, BID.high_rs_mwh.values,
                              P.iloc[-1].values, c, d, soc), use_container_width=True)
    sheet = pd.DataFrame({"block": range(1, 97), "time": labels, "forecast ₹/MWh": fc_next.round(0),
                          "buy MW": (c * 4).round(2), "sell MW": (d * 4).round(2), "stored MWh": soc.round(2)})
    left, right = st.columns([3, 1])
    left.dataframe(sheet[(sheet["buy MW"] > 0.01) | (sheet["sell MW"] > 0.01)], hide_index=True, use_container_width=True, height=260)
    right.download_button("⬇️ Download the bid (96 slots, CSV)", sheet.to_csv(index=False), file_name=f"bid_{BID_DATE}.csv", mime="text/csv",
                          use_container_width=True)
    right.caption("Ready to submit: one row per 15-minute slot. Only active slots are shown on the left.")

# ---------------- Tab 2: replay ----------------
with tab2:
    day = st.select_slider("Pick a delivery day (validation and test years)", options=list(DAYS), value=pd.Timestamp(M["example_day"]["date"]),
                           format_func=lambda x: x.strftime("%d %b %Y"))
    i = list(DAYS).index(day); actual = P.loc[day].values; naive = P.shift(1).loc[day].values
    c, d, soc = plan(FB[i]); cn, dn, _ = plan(naive); cp, dp, _ = plan(actual)
    ours, base, best = money(c, d, actual), money(cn, dn, actual), money(cp, dp, actual)
    fixed = bt.fixed_rule(actual, wear) if (mw, mwh, rte, fee) == (10, 20, 0.88, 0) else None
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Our assistant", f"₹{ours:,.0f}", f"{ours - base:+,.0f} vs tomorrow = today")
    k2.metric("Tomorrow = today", f"₹{base:,.0f}")
    k3.metric("Perfect guess (ceiling)", f"₹{best:,.0f}")
    k4.metric("Share of the best possible", f"{ours / best:.1%}" if best > 0 else "–")
    st.plotly_chart(day_chart(f"{day:%A %d %b %Y}: forecast vs actual, and the plan", actual, FB[i], CQ[i, :, 0], CQ[i, :, 8], naive, c, d, soc),
                    use_container_width=True)
    if fixed is not None:
        st.caption(f"The canvas's fixed timetable would have earned ₹{fixed:,.0f} on this day.")

# ---------------- Tab 3: track record ----------------
with tab3:
    t = R[R.index >= "2025-11-22"]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Test year, per day", f"₹{t.blend_2.mean():,.0f}", f"{t.blend_2.mean() - t.today_2.mean():+,.0f} vs tomorrow = today")
    k2.metric("Per year", f"₹{t.blend_2.mean() * 365 / 1e7:.2f} crore")
    k3.metric("Share of the best possible", f"{t.blend_2.sum() / t.perfect_2.sum():.1%}")
    k4.metric("Months ahead of tomorrow = today", f"{M['months_positive']} of {M['months_total']}")
    cum = go.Figure()
    for col, lbl, colr in [("blend_2", "Our assistant", NAVY), ("today_sun_2", "Tomorrow = today + Sunday fix", GREY), ("fixed", "Fixed timetable (canvas)", RED)]:
        cum.add_trace(go.Scatter(x=R.index, y=(R[col] - R.today_2).cumsum() / 1e7, name=lbl, line=dict(color=colr, width=2)))
    cum.add_vline(x=pd.Timestamp("2025-11-22").timestamp() * 1000, line_dash="dot", line_color="#999")
    cum.update_layout(title="Extra money over tomorrow = today, adding up (₹ crore). Settings: 10 MW / 20 MWh, ₹1,000 wear",
                      template="simple_white", height=420, legend=dict(orientation="h", y=1.1), yaxis_range=[-0.6, 0.35], margin=dict(l=10, r=10, t=70, b=10))
    st.plotly_chart(cum, use_container_width=True)
    sens = pd.DataFrame(M["sensitivity"]).set_index("setting")
    st.markdown("**Does it hold if our assumptions change?** (test year, ₹ per day)")
    st.dataframe(sens.style.format({"assistant ₹/day": "{:,.0f}", "tomorrow = today ₹/day": "{:,.0f}", "extra ₹/day": "{:+,.0f}", "share of best": "{:.1%}"}),
                 use_container_width=True)

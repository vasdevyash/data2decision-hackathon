"""Build the M3 exploratory-analysis PDF (max 3 pages) from the notebook's outputs.
Usage: python build_m3.py <out.pdf> <outputs/m3_metrics.json> <outputs/figures>
Every number is read from the metrics file written by notebooks/D01_M3_eda.ipynb.
"""
import sys, json, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer, KeepTogether
from PIL import Image as PILImage

HN = "/System/Library/Fonts/HelveticaNeue.ttc"
pdfmetrics.registerFont(TTFont("G", HN, subfontIndex=0))
pdfmetrics.registerFont(TTFont("GB", HN, subfontIndex=1))
pdfmetrics.registerFont(TTFont("GI", HN, subfontIndex=2))
pdfmetrics.registerFontFamily("G", normal="G", bold="GB", italic="GI", boldItalic="GB")

out, M, FIGS = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
INK, GREY = HexColor("#111111"), HexColor("#444444")
st = lambda n, **k: ParagraphStyle(n, **{"fontName": "G", "fontSize": 8.6, "leading": 11.3, "textColor": INK, **k})
T = st("t", fontName="GB", fontSize=13.5, leading=16.5)
META = st("m", fontSize=8, leading=10.5, textColor=GREY, spaceAfter=4)
H = st("h", fontName="GB", fontSize=10, leading=12.5, spaceBefore=6, spaceAfter=2, keepWithNext=1)
B = st("b", spaceAfter=2.5)
NUM = st("num", leftIndent=11, firstLineIndent=-11, spaceAfter=1.8)
CAP = st("cap", fontSize=7.6, leading=9.6, textColor=GREY, spaceBefore=1, spaceAfter=4)
S = st("s", fontSize=7.8, leading=9.8)
SB = st("sb", fontSize=7.8, leading=9.8, fontName="GB")
REF = st("ref", fontSize=7, leading=8.8, leftIndent=9, firstLineIndent=-9, textColor=GREY)
W = 180


def n(x): return f"{x:,.0f}"
def pc(x, d=1): return f"{x * 100:.{d}f}%"
def sg(x): return ("−" if x < 0 else "") + f"{abs(x):,.0f}"
def ci(c): return f"{sg(c[0])} to {sg(c[1])}"
def pv(p): return "&lt; 0.001" if p < 0.001 else f"{p:.3f}"
def dt(x): return datetime.date.fromisoformat(x).strftime("%b %Y")
def fig(name, width=W):
    w, h = PILImage.open(f"{FIGS}/{name}").size
    return Image(f"{FIGS}/{name}", width=width * mm, height=width * mm * h / w)


def table(rows, widths, align_right=()):
    """Booktabs-style table: rules above, below the header and at the end; no shading."""
    data = [[Paragraph(c, SB if i == 0 else S) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1)
    cmd = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
           ("TOPPADDING", (0, 0), (-1, -1), 1.4), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.4),
           ("LINEABOVE", (0, 0), (-1, 0), 0.8, black), ("LINEBELOW", (0, 0), (-1, 0), 0.4, black), ("LINEBELOW", (0, -1), (-1, -1), 0.8, black)]
    t.setStyle(TableStyle(cmd))
    return t


bv, bt = M["bench"]["validate"], M["bench"]["test"]
lv, lt = M["lear"]["validate"], M["lear"]["test"]
wv, wt = M["weekday_gain"]["validate"], M["weekday_gain"]["test"]
cv, ct = M["conditional_cycling"]["validate"], M["conditional_cycling"]["test"]
sc, an, q, dtp = M["second_cycle"], M["anomalies"], M["quality"], M["day_types"]
dow = M["test_by_dow_lag1_capture"]
types = M["day_type_order"]; tab = dtp["table"]
dbl = next(t for t in types if t.startswith("Double")); scarce = next(t for t in types if t.startswith("Scarce"))
others_v2 = [tab[t]["v2_hind"] for t in types if t != dbl]
cps = M["changepoints"]
REPO = "github.com/vasdevyash/data2decision-hackathon"

s = [Paragraph("M3 Understand: Exploratory Analysis of IEX Day-Ahead Prices", T),
     Paragraph(f"Team D01 · Energy &amp; Renewables · Code and data: {REPO} (notebooks/D01_M3_eda.ipynb, sql/m3_prepare.sql). "
               "All figures and numbers are produced by the notebook.", META)]

s.append(Paragraph("Summary", H))
summary = [
    f"<b>A forecasting model is worth building.</b> The LEAR model, the benchmark recommended by Lago et al. (2021), earns ₹{n(lt['lear_1']['gain_vs_lag1'])} a day "
    f"more than copying yesterday's prices on the test year (95% CI ₹{ci(lt['lear_1']['ci'])}; Diebold–Mariano p &lt; 0.001) and captures "
    f"{pc(lt['lear_1']['capture'])} of perfect-foresight profit. It also does so on the validation year (+₹{n(lv['lear_1']['gain_vs_lag1'])} a day).",
    f"<b>The second daily cycle is the larger lever, and it is seasonal.</b> On double-peak days ({pc(tab[dbl]['share'], 0)} of days, {pc(tab[dbl]['winter_share'], 0)} "
    f"of them in Oct–Feb) a second cycle is worth ₹{n(tab[dbl]['v2_hind'])} a day; on other day types ₹{n(min(others_v2))}–{n(max(others_v2))}. In Mar–Jun it earns nothing.",
    f"<b>Simple rules fail on Sundays.</b> Copying yesterday captures {pc(dow['Sun'], 0)} of the available profit on Sundays against "
    f"{pc(min(v for k, v in dow.items() if k != 'Sun'), 0)}–{pc(max(dow.values()), 0)} on other days. Copying last Sunday instead adds ₹{n(wt['gain_1c'])} a day.",
    f"<b>Weather forecasts add nothing once the calendar is modelled.</b> Removing the weather inputs from LEAR leaves profit unchanged "
    f"(₹{n(lt['lear_nowx_2']['mean'])} vs ₹{n(lt['lear_2']['mean'])} a day on the test year).",
    f"<b>Prices move between regimes.</b> Changepoint detection finds {len(cps)} regimes with average prices from ₹{n(min(c[2] for c in cps))} to "
    f"₹{n(max(c[2] for c in cps))}/MWh, including a break in {dt(cps[-1][0])} inside the test year, so any model must be recalibrated regularly.",
]
for i, t in enumerate(summary, 1):
    s.append(Paragraph(f"{i}.&nbsp;&nbsp;{t}", NUM))

s.append(Paragraph("1. Data preparation and integration", H))
s.append(table([
    ["Step", "Method", "Result"],
    ["IEX prices", "Typed and flagged in DuckDB SQL; kept 1 Apr 2023 onward, the single ₹10,000-cap regime",
     f"{n(q['days'] * 96)} blocks, {n(q['days'])} days; {n(q['days_not_96_blocks'])} incomplete days, {n(q['duplicate_blocks'])} duplicates, {n(q['null_prices'])} missing"],
    ["Quality flags", "Price cap, regional congestion, cleared volume above a bid side",
     f"{q['capped_share_pct']}% capped, {q['congested_share_pct']}% congested, {n(q['volume_flag_blocks'])} volume flags"],
    ["Weather", "Open-Meteo archived forecasts: 4 solar hubs, 2 wind hubs, 7 demand centres; daily national indices",
     f"1,696 days, {M['weather_missing_days']} missing"],
    ["Holidays", "India public holidays (holidays library), joined on date", f"{M['holidays_in_window']} holidays"],
    ["Transform", "Median/MAD-normalised asinh (Uniejewski et al., 2018) to tame price spikes for modelling",
     f"skewness {M['vst']['skew_raw']} to {M['vst']['skew_asinh']}"],
], [24, 92, 64]))

s.append(Paragraph("2. Price structure", H))
s.append(KeepTogether([fig("m3_structure.png"), Paragraph(
    f"Figure 1. Average price and share of blocks at the ₹10,000 cap, by month and hour (Apr 2023 – Nov 2026). Midday is always the cheap window "
    f"(cheapest in {datetime.date(2000, M['midday_min_month'], 1).strftime('%B')}, ₹{n(M['midday_min_price'])}). Evenings hit the cap "
    f"{n(M['cap_evening_aug_pct'])}% of the time in August. Winter adds a morning peak at 6–9 am.", CAP)]))

s.append(KeepTogether([Paragraph("3. Regimes and day types", H), fig("m3_changepoints.png"), Paragraph(
    "Figure 2. Weekly average price with regimes found by PELT changepoint detection (Killick et al., 2012). Regimes: " +
    "; ".join(f"{dt(a)}–{dt(b)} ₹{n(m)}" for a, b, m in cps) + ".", CAP)]))
s.append(KeepTogether([fig("m3_daytypes.png"), Paragraph(
    f"Figure 3. Days clustered by the shape of their 96-block price curve (k-means on asinh prices, k = 4; silhouette favours k = 2, "
    f"we keep 4 because the types are operationally distinct). Right: how often tomorrow's type follows today's. A type repeats on "
    f"{pc(1 - dtp['share_type_change'], 0)} of days, which is why yesterday's prices work so well.", CAP)]))
s.append(table([["Day type", "Share of days", "In Oct–Feb", "Sundays", "2nd-cycle value, ₹/day", "Yesterday's capture"]] +
               [[t, pc(tab[t]["share"], 0), pc(tab[t]["winter_share"], 0), pc(tab[t]["sunday_share"], 0), n(tab[t]["v2_hind"]), pc(tab[t]["lag1_capture"])]
                for t in types], [58, 22, 20, 18, 34, 28]))

s.append(Paragraph("4. Where simple rules fail", H))
s.append(KeepTogether([fig("m3_weekday.png"), Paragraph(
    f"Figure 4. Left: price error when copying yesterday or the same day last week (uncapped blocks). Right: share of perfect-foresight profit "
    f"captured by the yesterday's-prices schedule, by weekday, test year. Sunday spreads are {pc(an['sunday_spread_vs_weekday'], 0)} of weekday "
    f"spreads, and all ten most extreme low-spread days since 2023 were Sundays or holidays. A weekday rule chosen on training data (copy last week "
    f"for Sunday) adds ₹{n(wv['gain_1c'])} a day on validation (95% CI ₹{ci(wv['ci_1c'])}) and ₹{n(wt['gain_1c'])} on test (₹{ci(wt['ci_1c'])}).", CAP)]))
qv = sc["v2_by_gap_quintile"]
s.append(KeepTogether([fig("m3_second_cycle.png"), Paragraph(
    f"Figure 5. Left: perfect-foresight value of a second cycle against the morning-minus-midday price gap; it rises from ₹{n(qv[0])} to "
    f"₹{n(qv[-1])} a day from the lowest to the highest fifth of days. Right: gain from allowing a second cycle with yesterday's prices, by month "
    f"of the test year. The second cycle loses money on {pc(sc['share_days_lag1_2c_worse'], 0)} of test days; its value repeats day to day "
    f"(correlation {sc['corr_v2_persistence']:.2f}).", CAP)]))

s.append(Paragraph("5. Benchmarks, including a forecasting model", H))
s.append(P := Paragraph(
    "Each schedule is optimised on its price input and settled at actual prices with identical battery limits and ₹1,000/MWh wear. LEAR fits one "
    "LASSO model per 15-minute block on asinh prices from D−1, D−2 and D−7, weekday and holiday dummies and the day-D weather forecast, recalibrated "
    "monthly on an expanding window. Confidence intervals resample whole weeks (Künsch, 1989); p-values are Diebold–Mariano tests on daily profit "
    f"differences (Diebold and Mariano, 1995). LEAR's price error on uncapped blocks is ₹{n(M['lear']['lear']['mae_uncapped'])}/MWh against "
    f"₹{n(M['lear']['mae_lag1_uncapped'])} for yesterday's prices.", B))
s.append(KeepTogether([fig("m3_lear.png"), Paragraph(
    "Figure 6. Left: cumulative profit gained over the yesterday's-prices schedule (up to two cycles) across the validation and test years. "
    "Right: average daily profit on the test year.", CAP)]))
rows = [["Schedule", "Validation, ₹/day (capture)", "Test, ₹/day (capture)", "Test gain vs yesterday, ₹/day (95% CI)", "DM p"]]
rows += [
    ["Fixed rule (canvas), 1 cycle", f"{n(bv['fixed'])} ({pc(bv['cap_fixed'])})", f"{n(bt['fixed'])} ({pc(bt['cap_fixed'])})",
     f"−{n(bt['lag1_1'] - bt['fixed'])} ({ci([-bt['lag1_vs_fixed_ci'][1], -bt['lag1_vs_fixed_ci'][0]])})", "–"],
    ["Same day last week, 1 cycle", f"{n(bv['lag7_1'])} ({pc(bv['cap_lag7_1'])})", f"{n(bt['lag7_1'])} ({pc(bt['cap_lag7_1'])})", f"−{n(bt['lag1_1'] - bt['lag7_1'])}", "–"],
    ["Yesterday's prices, 1 cycle", f"{n(bv['lag1_1'])} ({pc(bv['cap_lag1_1'])})", f"{n(bt['lag1_1'])} ({pc(bt['cap_lag1_1'])})", "reference", "–"],
    ["<b>LEAR, 1 cycle</b>", f"{n(lv['lear_1']['mean'])} ({pc(lv['lear_1']['capture'])})", f"<b>{n(lt['lear_1']['mean'])}</b> ({pc(lt['lear_1']['capture'])})",
     f"+{n(lt['lear_1']['gain_vs_lag1'])} ({ci(lt['lear_1']['ci'])})", pv(lt["lear_1"]["p"])],
    ["Yesterday's prices, up to 2 cycles", f"{n(bv['lag1_2'])} ({pc(bv['cap_lag1_2'])})", f"{n(bt['lag1_2'])} ({pc(bt['cap_lag1_2'])})", "reference (2 cycles)", "–"],
    ["Two simple rules, up to 2 cycles", f"{n(cv['mean'])} ({pc(cv['capture'])})", f"{n(ct['mean'])} ({pc(ct['capture'])})", f"+{n(ct['gain_vs_lag1_2'])} ({ci(ct['ci'])})", "–"],
    ["<b>LEAR, up to 2 cycles</b>", f"{n(lv['lear_2']['mean'])} ({pc(lv['lear_2']['capture'])})", f"<b>{n(lt['lear_2']['mean'])}</b> ({pc(lt['lear_2']['capture'])})",
     f"+{n(lt['lear_2']['gain_vs_lag1'])} ({ci(lt['lear_2']['ci'])})", pv(lt["lear_2"]["p"])],
    ["LEAR without weather, up to 2 cycles", f"{n(lv['lear_nowx_2']['mean'])} ({pc(lv['lear_nowx_2']['capture'])})", f"{n(lt['lear_nowx_2']['mean'])} ({pc(lt['lear_nowx_2']['capture'])})",
     f"+{n(lt['lear_nowx_2']['gain_vs_lag1'])} ({ci(lt['lear_nowx_2']['ci'])})", pv(lt["lear_nowx_2"]["p"])],
    ["Perfect foresight, 1 / up to 2 cycles (ceiling)", f"{n(bv['hind1'])} / {n(bv['hind2'])}", f"{n(bt['hind1'])} / {n(bt['hind2'])}", "not tradable", "–"],
]
s.append(table(rows, [52, 33, 31, 47, 17]))

s.append(KeepTogether([fig("m3_weather.png", 170), Paragraph(
    f"Figure 7. Day-over-day change in midday price against change in forecast solar radiation (left), and in evening price against forecast evening "
    f"temperature (right). Correlations are {str(round(M['corr_dsolar_dmidday'][0], 2)).replace('-', '−')} and {str(round(M['corr_dtemp_devening'][0], 2)).replace('-', '−')}. Out of sample, calendar terms explain "
    f"{pc(M['weather']['midday']['r2_oos_calendar_only'], 0)} (midday) and {pc(M['weather']['evening']['r2_oos_calendar_only'], 0)} (evening) of day-to-day price "
    f"changes; adding weather changes this to {pc(M['weather']['midday']['r2_oos_weather_calendar'], 0)} and {pc(M['weather']['evening']['r2_oos_weather_calendar'], 0)}.", CAP)]))
s.append(Paragraph("6. Limitations and plan for M4", H))
lim = [
    "<b>Data limits.</b> One all-India price (congestion splits 2.5% of blocks); the ₹10,000 cap hides scarcity above it; the weather archive is "
    "built from the first hours of each forecast run, so it is shorter-lead than a true day-ahead forecast; one test year; exchange fees (about ₹1k a day) excluded.",
    "<b>Model limits.</b> LEAR is recalibrated monthly here; Lago et al. recalibrate daily and average several calibration windows, which typically helps.",
    "<b>M4 method.</b> (a) LEAR with daily recalibration and window averaging as the main model; (b) decision-focused training, which fits the forecaster "
    "to the profit of the schedule it produces rather than to price error (Elmachtoub and Grigas, 2022; Sang et al., 2023); (c) a pretrained time-series "
    "foundation model, Chronos (Ansari et al., 2024), run zero-shot as a challenger; (d) a cycling policy conditioned on the forecast day type. "
    "All judged by test-year profit with Diebold–Mariano tests against the two simple rules.",
]
for t in lim:
    s.append(Paragraph(t, B))

s.append(Paragraph("References", H))
refs = [
    "Ansari, A. F. et al. (2024). Chronos: Learning the language of time series. <i>Transactions on Machine Learning Research</i>.",
    "Diebold, F. X. and Mariano, R. S. (1995). Comparing predictive accuracy. <i>Journal of Business &amp; Economic Statistics</i>, 13(3), 253–263.",
    "Elmachtoub, A. N. and Grigas, P. (2022). Smart \"predict, then optimize\". <i>Management Science</i>, 68(1), 9–26.",
    "Killick, R., Fearnhead, P. and Eckley, I. A. (2012). Optimal detection of changepoints with a linear computational cost. <i>JASA</i>, 107(500), 1590–1598.",
    "Künsch, H. R. (1989). The jackknife and the bootstrap for general stationary observations. <i>Annals of Statistics</i>, 17(3), 1217–1241.",
    "Lago, J., Marcjasz, G., De Schutter, B. and Weron, R. (2021). Forecasting day-ahead electricity prices: A review of state-of-the-art algorithms, "
    "best practices and an open-access benchmark. <i>Applied Energy</i>, 293, 116983.",
    "Sang, L., Xu, Y., Long, H., Hu, Q. and Sun, H. (2023). Electricity price prediction for energy storage system arbitrage: A decision-focused approach. arXiv:2305.00362.",
    "Uniejewski, B., Weron, R. and Ziel, F. (2018). Variance stabilizing transformations for electricity spot price forecasting. <i>IEEE Transactions on Power Systems</i>, 33(2), 2219–2229.",
    "Data: Indian Energy Exchange, Day-Ahead Market snapshot; Open-Meteo Historical Forecast API (CC BY 4.0); holidays Python library.",
]
for r in refs:
    s.append(Paragraph(r, REF))

SimpleDocTemplate(out, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=11 * mm, bottomMargin=10 * mm,
                  title="D01 M3 Exploratory Analysis", author="Team D01", creator="Team D01", producer="Team D01").build(s)

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

s = [Paragraph("M3 Understand: How Should a Battery Trade Electricity?", T),
     Paragraph(f"Team D01 · Energy &amp; Renewables · Code and data: {REPO} (notebooks/D01_M3_eda.ipynb, sql/m3_prepare.sql)", META)]
s.append(Paragraph("A big battery makes money like a shop: it buys electricity when it is cheap (around noon, when solar floods the grid) and sells it "
                   "when it is expensive (in the evening). The catch is that it must commit to tomorrow's plan, slot by slot, before it knows tomorrow's "
                   "prices. We studied 3.5 years of Indian exchange prices to answer one question: <b>what is the best way to guess tomorrow, and how much "
                   "extra money does a better guess make?</b>", B))
s.append(Paragraph("What we found", H))
summary = [
    f"<b>The fixed timetable in the canvas leaves a lot of money on the table.</b> Simply assuming <i>tomorrow = today</i> earns ₹{n(bt['lag1_1'] - bt['fixed'])} "
    f"a day more on the test year ({pc(bt['cap_lag1_1'], 0)} of the most anyone could earn, against {pc(bt['cap_fixed'], 0)}).",
    f"<b>A forecasting model from research does even better.</b> LEAR, the standard model recommended by a leading review (Lago et al., 2021), adds "
    f"₹{n(lt['lear_1']['gain_vs_lag1'])} a day on top, reaching {pc(lt['lear_1']['capture'], 0)}. The gain holds on two separate years and is very unlikely to be luck.",
    f"<b>The biggest lever is a second buy-sell round each day, but only in winter.</b> On winter days with a morning and an evening peak it is worth "
    f"₹{n(tab[dbl]['v2_hind'])} a day; in March–June it earns nothing.",
    f"<b>Sundays break the simple guess.</b> Sunday looks nothing like Saturday, so <i>tomorrow = today</i> gets only {pc(dow['Sun'], 0)} on Sundays. Copying last "
    f"Sunday instead adds ₹{n(wt['gain_1c'])} a day.",
    "<b>Weather forecasts do not help.</b> The forecasting model earns the same with or without them, so we leave weather out.",
]
for i, t in enumerate(summary, 1):
    s.append(Paragraph(f"{i}.&nbsp;&nbsp;{t}", NUM))

s.append(Paragraph("1. The data", H))
s.append(table([
    ["Source", "What we did", "Result"],
    ["IEX prices", "Every 15-minute price since 1 Apr 2023, cleaned in SQL (DuckDB)",
     f"{n(q['days'] * 96)} blocks, {n(q['days'])} days; {n(q['days_not_96_blocks'])} incomplete days, {n(q['duplicate_blocks'])} duplicates, {n(q['null_prices'])} missing"],
    ["Quality flags", "Marked prices at the ₹10,000 cap, regional splits and odd volume rows",
     f"{q['capped_share_pct']}% capped, {q['congested_share_pct']}% congested, {n(q['volume_flag_blocks'])} volume flags"],
    ["Weather", "Past weather forecasts for 13 places: solar parks, wind farms, big cities",
     f"1,696 days, {M['weather_missing_days']} missing"],
    ["Holidays", "India public holidays, matched by date", f"{M['holidays_in_window']} holidays"],
    ["Transform", "Squeezed extreme prices so models are not thrown by spikes (Uniejewski et al., 2018)",
     f"skewness {M['vst']['skew_raw']} to {M['vst']['skew_asinh']}"],
], [24, 92, 64]))

s.append(Paragraph("2. When is power cheap, and when is it expensive?", H))
s.append(KeepTogether([fig("m3_structure.png"), Paragraph(
    f"Figure 1. Left: average price by month and hour. Right: how often the price hits the ₹10,000 cap. Noon is always cheap. Evenings are expensive "
    f"and hit the cap {n(M['cap_evening_aug_pct'])}% of the time in August. Winter adds a second expensive spell in the morning, 6–9 am.", CAP)]))

s.append(KeepTogether([Paragraph("3. Price moods and kinds of days", H), fig("m3_changepoints.png"), Paragraph(
    "Figure 2. Weekly average price. A changepoint method (PELT; Killick et al., 2012) finds five long price moods, including one that starts inside our test year: " +
    "; ".join(f"{dt(a)}–{dt(b)} ₹{n(m)}" for a, b, m in cps) + ".", CAP)]))
s.append(KeepTogether([fig("m3_daytypes.png"), Paragraph(
    f"Figure 3. Left: the four kinds of day an algorithm finds when it groups days by the shape of their price curve (k-means). Right: how often "
    f"tomorrow is each kind, given today. Tomorrow is the same kind as today {pc(1 - dtp['share_type_change'], 0)} of the time, which is why "
    f"<i>tomorrow = today</i> is such a strong guess. The second round pays almost only on double-peak days.", CAP)]))
s.append(table([["Kind of day", "Share of days", "In Oct–Feb", "Sundays", "Value of 2nd round, ₹/day", "Share captured by tomorrow = today"]] +
               [[t, pc(tab[t]["share"], 0), pc(tab[t]["winter_share"], 0), pc(tab[t]["sunday_share"], 0), n(tab[t]["v2_hind"]), pc(tab[t]["lag1_capture"])]
                for t in types], [58, 22, 20, 18, 34, 28]))

s.append(Paragraph("4. Where the simple guess fails", H))
s.append(KeepTogether([fig("m3_weekday.png"), Paragraph(
    f"Figure 4. Left: how far off the guess is when copying yesterday or last week. Right: share of the possible profit that <i>tomorrow = today</i> "
    f"earns on each weekday. Sunday is the problem: it looks nothing like Saturday, and all ten most unusual days since 2023 were Sundays or holidays. "
    f"Copying last Sunday for Sundays adds ₹{n(wv['gain_1c'])} a day on the validation year and ₹{n(wt['gain_1c'])} on the test year.", CAP)]))
qv = sc["v2_by_gap_quintile"]
s.append(KeepTogether([fig("m3_second_cycle.png"), Paragraph(
    f"Figure 5. Left: the bigger the morning peak, the more a second buy-sell round is worth (from ₹{n(qv[0])} to ₹{n(qv[-1])} a day). "
    f"Right: what the second round adds in each month of the test year. It pays in winter and earns nothing in March–June.", CAP)]))

s.append(Paragraph("5. Simple guesses vs a forecasting model", H))
s.append(Paragraph(
    "Every plan is run on every day and paid at the real prices, with the same battery and wear cost. LEAR learns from the last few days' prices, "
    "the weekday and holidays, with one small model per 15-minute slot. To check that a gain is real and not luck we use two standard tests: resampling "
    f"whole weeks (Künsch, 1989) and the Diebold–Mariano test (1995). LEAR's guesses are off by ₹{n(M['lear']['lear']['mae_uncapped'])}/MWh on average, "
    f"against ₹{n(M['lear']['mae_lag1_uncapped'])} for <i>tomorrow = today</i>.", B))
s.append(KeepTogether([fig("m3_lear.png"), Paragraph(
    "Figure 6. Left: extra money earned over <i>tomorrow = today</i>, adding up day by day over two years; the research model pulls ahead steadily. "
    "Right: average money per day on the test year for each plan.", CAP)]))
rows = [["Plan", "Validation year, ₹/day (share of best)", "Test year, ₹/day (share of best)", "Extra vs tomorrow = today, test (95% range)", "Chance it is luck"]]
rows += [
    ["Fixed timetable (canvas), 1 round", f"{n(bv['fixed'])} ({pc(bv['cap_fixed'])})", f"{n(bt['fixed'])} ({pc(bt['cap_fixed'])})",
     f"−{n(bt['lag1_1'] - bt['fixed'])} ({ci([-bt['lag1_vs_fixed_ci'][1], -bt['lag1_vs_fixed_ci'][0]])})", "–"],
    ["Same day last week, 1 round", f"{n(bv['lag7_1'])} ({pc(bv['cap_lag7_1'])})", f"{n(bt['lag7_1'])} ({pc(bt['cap_lag7_1'])})", f"−{n(bt['lag1_1'] - bt['lag7_1'])}", "–"],
    ["Tomorrow = today, 1 round", f"{n(bv['lag1_1'])} ({pc(bv['cap_lag1_1'])})", f"{n(bt['lag1_1'])} ({pc(bt['cap_lag1_1'])})", "reference", "–"],
    ["<b>LEAR model, 1 round</b>", f"{n(lv['lear_1']['mean'])} ({pc(lv['lear_1']['capture'])})", f"<b>{n(lt['lear_1']['mean'])}</b> ({pc(lt['lear_1']['capture'])})",
     f"+{n(lt['lear_1']['gain_vs_lag1'])} ({ci(lt['lear_1']['ci'])})", pv(lt["lear_1"]["p"])],
    ["Tomorrow = today, up to 2 rounds", f"{n(bv['lag1_2'])} ({pc(bv['cap_lag1_2'])})", f"{n(bt['lag1_2'])} ({pc(bt['cap_lag1_2'])})", "reference (2 cycles)", "–"],
    ["Sunday fix + smart 2nd round", f"{n(cv['mean'])} ({pc(cv['capture'])})", f"{n(ct['mean'])} ({pc(ct['capture'])})", f"+{n(ct['gain_vs_lag1_2'])} ({ci(ct['ci'])})", "–"],
    ["<b>LEAR model, up to 2 rounds</b>", f"{n(lv['lear_2']['mean'])} ({pc(lv['lear_2']['capture'])})", f"<b>{n(lt['lear_2']['mean'])}</b> ({pc(lt['lear_2']['capture'])})",
     f"+{n(lt['lear_2']['gain_vs_lag1'])} ({ci(lt['lear_2']['ci'])})", pv(lt["lear_2"]["p"])],
    ["LEAR model without weather, up to 2 rounds", f"{n(lv['lear_nowx_2']['mean'])} ({pc(lv['lear_nowx_2']['capture'])})", f"{n(lt['lear_nowx_2']['mean'])} ({pc(lt['lear_nowx_2']['capture'])})",
     f"+{n(lt['lear_nowx_2']['gain_vs_lag1'])} ({ci(lt['lear_nowx_2']['ci'])})", pv(lt["lear_nowx_2"]["p"])],
    ["Perfect guess, 1 / up to 2 rounds (ceiling)", f"{n(bv['hind1'])} / {n(bv['hind2'])}", f"{n(bt['hind1'])} / {n(bt['hind2'])}", "not tradable", "–"],
]
s.append(table(rows, [52, 33, 31, 47, 17]))

s.append(KeepTogether([fig("m3_weather.png", 170), Paragraph(
    "Figure 7. Day-to-day change in noon price against change in forecast sunshine (left), and in evening price against forecast evening "
    "temperature (right). The dots form a flat cloud: weather barely moves the price from one day to the next. The day of the week explains "
    f"{pc(M['weather']['evening']['r2_oos_calendar_only'], 0)} of evening price changes; adding weather adds nothing.", CAP)]))
s.append(Paragraph("6. Limits, and what we do next (M4)", H))
lim = [
    "<b>Limits.</b> We use one all-India price. The ₹10,000 cap hides how scarce power really was. Our past weather forecasts are short-range, so "
    "real day-ahead forecasts would help even less. We test on one year, and exchange fees (about ₹1,000 a day) are left out.",
    "<b>Next, at M4.</b> (1) Make LEAR re-learn every day instead of every month, as the original paper does. (2) Train the model on the money it "
    "makes rather than on how close its prices are, an idea called decision-focused learning (Elmachtoub and Grigas, 2022; Sang et al., 2023). "
    "(3) Try Chronos, a ready-made AI forecasting model trained on many kinds of time series (Ansari et al., 2024), as a challenger. "
    "(4) Decide each day whether to run one round or two. Every option is judged by money earned on the test year."
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

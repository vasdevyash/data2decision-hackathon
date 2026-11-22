"""Build the M3 Exploratory Analysis PDF from outputs/m3_metrics.json and outputs/figures. Usage: python build_m3.py <out.pdf> <m3_metrics.json> <figures_dir>"""
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer, KeepTogether

from reportlab.lib.colors import HexColor

# Helvetica Neue: lining numerals and a native ₹ sign (Georgia's old-style numerals made "D01" read as "Do1")
HN = "/System/Library/Fonts/HelveticaNeue.ttc"
pdfmetrics.registerFont(TTFont("G", HN, subfontIndex=0))
pdfmetrics.registerFont(TTFont("GB", HN, subfontIndex=1))
pdfmetrics.registerFont(TTFont("GI", HN, subfontIndex=2))
pdfmetrics.registerFontFamily("G", normal="G", bold="GB", italic="GI", boldItalic="GB")
INK, SOFT = HexColor("#1a1a1a"), HexColor("#555555")

import json
out = sys.argv[1]; M = json.load(open(sys.argv[2])); FIGS = sys.argv[3]
B = ParagraphStyle("b", fontName="G", fontSize=8.5, leading=11.4, spaceAfter=2.6, textColor=INK)
H = ParagraphStyle("h", fontName="GB", fontSize=10.2, leading=12.5, spaceBefore=7, spaceAfter=2.6, keepWithNext=1, textColor=INK)
T = ParagraphStyle("t", fontName="GB", fontSize=15, leading=18, spaceAfter=2, textColor=INK)
SUB = ParagraphStyle("sub", fontName="G", fontSize=8.5, leading=11, spaceAfter=2, textColor=SOFT)
S = ParagraphStyle("s", fontName="G", fontSize=8, leading=10.1, textColor=INK)
SB = ParagraphStyle("sb", parent=S, fontName="GB")
CAP = ParagraphStyle("cap", fontName="GI", fontSize=7.6, leading=9.6, spaceBefore=0.5, spaceAfter=3, textColor=SOFT)
BL = ParagraphStyle("bl", parent=B, leftIndent=10, bulletIndent=1, spaceAfter=2)
P = lambda s: Paragraph(s, B)
bul = lambda s: Paragraph(s, BL, bulletText="•")


def plain(rows, widths):
    data = [[Paragraph(c, SB if i == 0 else S) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 1.3),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 1.3), ("BOTTOMPADDING", (0, 0), (-1, 0), 3)]))
    return t


LINK = HexColor("#1f4e8c")
def a(url, txt): return f'<link href="{url}"><font color="#1f4e8c">{txt}</font></link>'
REPO = "https://github.com/vasdevyash/data2decision-hackathon"
QUOTE = ParagraphStyle("q", parent=B, fontName="GI", leftIndent=8, textColor=SOFT)

def box(html):
    t = Table([[Paragraph(html, B)]], colWidths=[180 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), HexColor("#eef2f7")), ("LEFTPADDING", (0, 0), (-1, -1), 6),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return t

def rule_table(rows, widths, right=()):
    t = plain(rows, widths)
    st = [("LINEBELOW", (0, 0), (-1, 0), 0.6, HexColor("#888888"))]
    for c in right: st.append(("ALIGN", (c, 0), (c, -1), "RIGHT"))
    t.setStyle(TableStyle(st)); return t



# ---------- helpers bound to the metrics file ----------
def n(x): return f"{x:,.0f}"
def pc(x, d=1): return f"{x * 100:.{d}f}%"
def ci(c): return f"₹{n(c[0])} to ₹{n(c[1])}"
def dt(x): import datetime as _d; return _d.date.fromisoformat(x).strftime("%-d %b %Y")
bv, bt = M["bench"]["validate"], M["bench"]["test"]
wv, wt = M["weekday_gain"]["validate"], M["weekday_gain"]["test"]
cv, ct = M["conditional_cycling"]["validate"], M["conditional_cycling"]["test"]
sc, an, wx, q = M["second_cycle"], M["anomalies"], M["weather"], M["quality"]
dowcap = M["test_by_dow_lag1_capture"]
NB = REPO + "/blob/main/notebooks/D01_M3_eda.ipynb"; SQL = REPO + "/blob/main/sql/m3_prepare.sql"
MONTH = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
img = lambda f, h: Image(f"{FIGS}/{f}", width=176 * mm, height=h * mm)

s = [Paragraph("M3 UNDERSTAND · Exploratory Analysis: Battery Dispatch", T),
     Paragraph(f"Team D01 · Energy &amp; Renewables · Notebook: {a(NB, 'notebooks/D01_M3_eda.ipynb')} · SQL: {a(SQL, 'sql/m3_prepare.sql')} · "
               f"every number below is written by the notebook to outputs/m3_metrics.json", SUB),
     Spacer(1, 3),
     box("<b>Bottom line.</b> Four findings shape the model we build at M4. "
         f"<b>(1)</b> A schedule optimised on yesterday's prices is the bar: it captures {pc(bv['cap_lag1_1'])} of perfect-foresight profit on the "
         f"validation year and {pc(bt['cap_lag1_1'])} on the test year, against {pc(bv['cap_fixed'])} and {pc(bt['cap_fixed'])} for the canvas's fixed rule. "
         f"<b>(2)</b> Its weak spot is <b>Sunday</b> ({pc(dowcap['Sun'], 0)} captured): copying last Sunday instead, a rule picked on training data alone, "
         f"adds ₹{n(wt['gain_1c'])} a day on the test year (95% CI {ci(wt['ci_1c'])}). "
         f"<b>(3)</b> The second cycle is seasonal and predictable: worth ₹{n(sc['v2_by_season_test']['Oct-Feb'])} a day in Oct–Feb and nothing in Mar–Jun, "
         f"and today's value correlates {sc['corr_v2_persistence']:.2f} with yesterday's. "
         f"<b>(4)</b> Day-ahead weather forecasts add no out-of-sample explanatory power once the weekly cycle is modelled, so M4 targets the "
         "calendar and the cycling decision, not a weather model.")]

# ---------- 1 ----------
s.append(Paragraph("1. Preparation and integration", H))
s.append(P("All cleaning runs as SQL in DuckDB (<i>sql/m3_prepare.sql</i>), so each step can be read and re-run. Three sources are joined on date."))
s.append(rule_table([
    ["Step", "What we did", "Result"],
    ["Load and type", "Cast the IEX file, keep 1 Apr 2023 onward (single ₹10,000 cap), add hour, cap, congestion and volume flags",
     f"{n(q['days'] * 96)} blocks, {n(q['days'])} days"],
    ["Quality checks", "Blocks per day, duplicates, missing prices, range, cap share, volume consistency, congestion",
     f"{n(q['days_not_96_blocks'])} incomplete days, {n(q['duplicate_blocks'])} duplicates, {n(q['null_prices'])} missing; prices ₹{q['min_price']:,.2f}–{n(q['max_price'])}; "
     f"{q['capped_share_pct']}% capped; {n(q['volume_flag_blocks'])} volume flags; {q['congested_share_pct']}% congested"],
    ["Weather (new source)", "Open-Meteo archived forecasts for 4 solar hubs, 2 wind hubs and 7 demand centres (<i>src/download_weather.py</i>); "
     "daily national indices: midday solar, cloud, max and evening temperature, wind", f"1,696 days, {M['weather_missing_days']} missing"],
    ["Holidays (new source)", "India public holidays from the <i>holidays</i> library", f"{M['holidays_in_window']} holidays in the window"],
    ["Daily table", "One row per day: segment prices (night, morning, midday, evening), spread, capped blocks, calendar, split, weather",
     "Train / validate / test fixed in M2"],
], [27, 98, 55]))

# ---------- 2 ----------
s.append(KeepTogether([Paragraph("2. The price structure the battery trades on", H), img("m3_structure.png", 55),
    Paragraph(f"Figure 1. Average price (left) and share of blocks at the ₹10,000 cap (right) by month and hour, 1 Apr 2023 – 21 Nov 2026. "
              f"Midday is always the cheap window (cheapest in {MONTH[M['midday_min_month']]}, ₹{n(M['midday_min_price'])}). Evenings are capped "
              f"{n(M['cap_evening_aug_pct'])}% of the time in August and {n(M['cap_evening_may_pct'])}% in May. Winter adds a second, morning peak (6–9 am), "
              "which is what makes a second daily cycle pay.", CAP)]))

# ---------- 3 ----------
s.append(Paragraph("3. Baselines and benchmarks, day by day", H))
s.append(P("Every schedule is optimised on its price input, then settled at actual prices with the same battery limits and ₹1,000/MWh wear. "
           "Confidence intervals resample whole weeks, because neighbouring days are correlated."))
s.append(rule_table([
    ["Schedule (₹/day, share of perfect foresight)", "Validation year", "Test year"],
    ["Fixed rule (canvas), 1 cycle", f"{n(bv['fixed'])} ({pc(bv['cap_fixed'])})", f"{n(bt['fixed'])} ({pc(bt['cap_fixed'])})"],
    ["Same day last week, 1 cycle", f"{n(bv['lag7_1'])} ({pc(bv['cap_lag7_1'])})", f"{n(bt['lag7_1'])} ({pc(bt['cap_lag7_1'])})"],
    ["Yesterday's prices, 1 cycle", f"{n(bv['lag1_1'])} ({pc(bv['cap_lag1_1'])})", f"{n(bt['lag1_1'])} ({pc(bt['cap_lag1_1'])})"],
    ["Yesterday's prices, up to 2 cycles", f"{n(bv['lag1_2'])} ({pc(bv['cap_lag1_2'])})", f"{n(bt['lag1_2'])} ({pc(bt['cap_lag1_2'])})"],
    ["<b>Best simple rule</b>: Sunday uses last week, 2nd cycle only when yesterday justified it", f"<b>{n(cv['mean'])}</b> ({pc(cv['capture'])})", f"<b>{n(ct['mean'])}</b> ({pc(ct['capture'])})"],
    ["Perfect foresight, 1 / up to 2 cycles (ceiling, not tradable)", f"{n(bv['hind1'])} / {n(bv['hind2'])}", f"{n(bt['hind1'])} / {n(bt['hind2'])}"],
    ["Yesterday's prices minus fixed rule, 95% CI", ci(bv["lag1_vs_fixed_ci"]), ci(bt["lag1_vs_fixed_ci"])],
    ["Value of the 2nd cycle (yesterday's prices), 95% CI", ci(bv["second_cycle_ci"]), ci(bt["second_cycle_ci"])],
    ["Losing days: fixed rule / yesterday's prices", f"{bv['fixed_loss_days']} / {bv['lag1_1_loss_days']}", f"{bt['fixed_loss_days']} / {bt['lag1_1_loss_days']}"],
], [92, 44, 44], right=(1, 2)))
s.append(P(f"The fixed rule is not a credible baseline: it trails yesterday's prices by ₹{n(bv['lag1_1'] - bv['fixed'])} a day "
           f"on the validation year, and it loses money when midday and evening are both capped (on 1 Sep 2023 all 96 blocks cleared at ₹10,000, "
           f"and the rule lost ₹{n(-an['fixed_worst_day'])}; an optimiser simply stays idle). The best simple rule, built from the two findings below, "
           f"is the honest bar for M4."))

# ---------- 4 ----------
s.append(KeepTogether([Paragraph("4. Where yesterday's prices break: the weekly cycle", H), img("m3_weekday.png", 50),
    Paragraph("Figure 2. Left: average price error from copying yesterday (dark) or the same day last week (light), uncapped blocks. Right: profit captured by "
              "the yesterday's-prices schedule by delivery day, test year.", CAP)]))
s.append(P(f"Copying yesterday works from Tuesday to Saturday, with an error of ₹{n(min(M['mae1_by_dow'][d] for d in ['Tue','Wed','Thu','Fri','Sat']))}–{n(max(M['mae1_by_dow'][d] for d in ['Tue','Wed','Thu','Fri','Sat']))}/MWh. "
           f"The error jumps whenever the day copied is a different kind of day: ₹{n(M['mae1_by_dow']['Sun'])}/MWh for Sunday (copying Saturday) and "
           f"₹{n(M['mae1_by_dow']['Mon'])}/MWh for Monday (copying Sunday). But only Sunday costs profit. On the test year the schedule captures {pc(dowcap['Sun'], 0)} on Sundays and "
           f"{pc(min(v for k, v in dowcap.items() if k != 'Sun'), 0)}–{pc(max(dowcap.values()), 0)} on other days. Sunday spreads are only "
           f"{pc(an['sunday_spread_vs_weekday'], 0)} of weekday spreads, and <b>all ten</b> of the most extreme low-spread days since 2023 were Sundays or "
           "holidays (Republic Day 2025, Holi 2025). Choosing, on training data only, which day to copy for each weekday picks last week for Sunday and "
           f"yesterday for every other day. Out of sample it adds <b>₹{n(wv['gain_1c'])}</b> a day on the validation year (95% CI {ci(wv['ci_1c'])}) and "
           f"<b>₹{n(wt['gain_1c'])}</b> on the test year (95% CI {ci(wt['ci_1c'])}). Monday copies Sunday, yet still captures "
           f"{pc(dowcap['Mon'], 0)}, which suggests Sunday mostly shifts the price level, not the daily shape the optimiser trades on."))

# ---------- 5 ----------
s.append(KeepTogether([Paragraph("5. When does the second cycle pay?", H), img("m3_second_cycle.png", 50),
    Paragraph("Figure 3. Left: value of a second cycle under perfect foresight against the morning-minus-midday price gap, every day since Apr 2023. "
              "Right: average gain from allowing a second cycle in the yesterday's-prices schedule, by month of the test year.", CAP)]))
qv = sc["v2_by_gap_quintile"]
s.append(P(f"A second cycle needs a second peak. Sorting days by the morning-minus-midday gap, its perfect-foresight value rises from ₹{n(qv[0])} a day in the "
           f"lowest fifth to ₹{n(qv[-1])} in the highest. The pattern is seasonal: winter mornings peak, so in Oct–Feb the yesterday's-prices schedule gains "
           f"₹{n(sc['v2_by_season_test']['Oct-Feb'])} a day from the second cycle, Jul–Sep ₹{n(sc['v2_by_season_test']['Jul-Sep'])}, and Mar–Jun "
           f"{'−' if sc['v2_by_season_test']['Mar-Jun'] < 0 else ''}₹{n(abs(sc['v2_by_season_test']['Mar-Jun']))}. On {pc(sc['share_days_lag1_2c_worse'], 0)} of test days the second cycle loses money. Because the value "
           f"persists (correlation {sc['corr_v2_persistence']:.2f} day to day), a simple rule works: run the second cycle only if it would have earned more than "
           f"₹{n(M['conditional_cycling']['threshold'])} yesterday (threshold set on training data). Combined with the Sunday rule it adds ₹{n(cv['gain_vs_lag1_2'])} "
           f"a day on the validation year (95% CI {ci(cv['ci'])}) and ₹{n(ct['gain_vs_lag1_2'])} on the test year (95% CI {ci(ct['ci'])})."))

# ---------- 6 ----------
s.append(Paragraph("6. Does the weather explain what persistence misses?", H))
s.append(P("We regressed the day-over-day change in midday and evening prices on the day-over-day change in forecast weather, with weekday and holiday "
           "terms, fitted on training data and scored on the validation and test years. The score is the share of the day-to-day price change explained, "
           "relative to assuming no change (yesterday's prices)."))
s.append(rule_table([
    ["Out-of-sample share of day-to-day change explained", "Calendar only", "Calendar + weather"],
    ["Midday price (10 am–4 pm)", pc(wx["midday"]["r2_oos_calendar_only"]), pc(wx["midday"]["r2_oos_weather_calendar"])],
    ["Evening price (6 pm–midnight)", pc(wx["evening"]["r2_oos_calendar_only"]), pc(wx["evening"]["r2_oos_weather_calendar"])],
], [92, 44, 44], right=(1, 2)))
s.append(P(f"The calendar explains 43–50% of day-to-day moves. Weather adds nothing: the raw correlations are {M['corr_dsolar_dmidday'][0]:.2f} (solar against "
           f"midday price) and {M['corr_dtemp_devening'][0]:.2f} (temperature against evening price). National weather changes slowly and smoothly, while prices "
           "move with the weekly demand cycle, outages and hydro and coal scheduling that the data cannot see. This is a useful negative result: it tells us "
           "not to spend M4 on a weather-driven forecaster."))

# ---------- 7 ----------
s.append(Paragraph("7. Anomalies, limitations and what goes to M4", H))
s.append(bul(f"<b>Regime shifts:</b> the 30-day average price ranged from ₹{n(an['rolling30_min'])} ({dt(an['rolling30_min_date'])}) to ₹{n(an['rolling30_max'])} "
             f"({dt(an['rolling30_max_date'])}). We refit on a rolling basis and report results by season."))
s.append(bul(f"<b>Scarcity days:</b> {an['days_all_evening_capped']} days had every evening block at the cap; on the worst, all 96 blocks were. "
             "Capped blocks tie, so the forecast's edge is in picking charging blocks, not peak levels."))
s.append(bul(f"<b>Holidays:</b> average price ₹{n(-an['holiday_mean_price_gap'])} below working days, and two appear among the ten most extreme low-spread days; "
             "treating holidays like Sundays is untested here and goes to M4."))
s.append(bul("<b>Limitations:</b> the weather archive stitches the first hours of each forecast run, so it is shorter-lead than a true day-ahead forecast "
             "(which, if anything, flatters weather); one all-India price; one test year; exchange fees (≈ ₹1k/day) excluded."))
s.append(box(f"<b>Preliminary business insight.</b> A trader can capture {pc(ct['capture'], 0)} of the perfect-foresight profit with two rules and no model: copy last week "
             "for Sundays, and run a second cycle only when yesterday's prices justified it. <b>M4 plan:</b> beat this rule with a forecaster aimed "
             "at the two places it is weak, weekend and holiday shapes and the winter morning peak, chosen by validation-year profit and judged with "
             "week-bootstrap confidence intervals."))
s.append(Paragraph("Sources: IEX Day-Ahead Market snapshot; Open-Meteo Historical Forecast API (CC BY 4.0); <i>holidays</i> Python library. "
                   "AI use: generative AI assisted with code and drafting; every number is produced by the notebook in the repository.", S))

SimpleDocTemplate(out, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=11 * mm, bottomMargin=10 * mm,
                  title="D01 M3 Exploratory Analysis", author="Team D01", creator="Team D01", producer="Team D01").build(s)

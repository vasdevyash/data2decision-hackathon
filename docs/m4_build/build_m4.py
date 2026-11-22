"""Build the M4 working-solution PDF (max 3 pages) from outputs/m4_metrics.json and figures.
Usage: python build_m4.py <out.pdf> <outputs/m4_metrics.json> <outputs/figures>
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


t, v, TS, SEN, RK, SEG = M["test"], M["validate"], M["tests"], M["sensitivity"], M["risk"], M["segments"]
sh, sh1, nd, ex = M["share_test"], M["share_test_1"], M["next_day"], M["example_day"]
g2t, g2v = TS["test"]["blend_vs_today_2"], TS["validate"]["blend_vs_today_2"]
REPO = "github.com/vasdevyash/data2decision-hackathon"
def lakh(x): return f"₹{x / 1e5:.2f} lakh"
def crore(x): return f"₹{x * 365 / 1e7:.2f} crore"

s = [Paragraph("M4 Build: A Battery Trading Assistant That Writes Tomorrow's Bid", T),
     Paragraph(f"Team D01 · Energy &amp; Renewables · Code, app and data: {REPO} (web/index.html, app/app.py, notebooks/D01_M4_solution.ipynb)", META)]
s.append(Paragraph(
    "We built an assistant that does the battery trader's daily job. Each morning it guesses tomorrow's price for all 96 fifteen-minute slots, works "
    "out the most profitable plan (when to buy, when to sell, how much), and writes the bid, ready to submit. It runs as a live app, and every number "
    "below comes from running it on two years of real Indian Energy Exchange prices that it had never seen.", B))
s.append(Paragraph("Results at a glance", H))
glance = [
    f"<b>It earns {lakh(t['blend_2'])} a day</b> on the test year, about <b>{crore(t['blend_2'])} a year</b> for a 10 MW / 20 MWh battery, "
    f"{pc(sh['blend'])} of what a perfect guess of tomorrow would earn.",
    f"<b>It beats every simple plan.</b> ₹{n(t['blend_1'] - t['fixed'])} a day more than the canvas's fixed timetable, and ₹{n(g2t['gain'])} a day "
    f"(₹{g2t['gain'] * 365 / 1e5:.1f} lakh a year) more than assuming <i>tomorrow = today</i>.",
    f"<b>The gain is real.</b> It is ahead on both unseen years (+₹{n(g2v['gain'])} and +₹{n(g2t['gain'])} a day), in {M['months_positive']} of "
    f"{M['months_total']} months, and the chance it is luck is below {max(g2t['p'], g2v['p']) * 100:.1f}%.",
    "<b>It holds when our assumptions change:</b> wear cost from ₹0 to ₹1,500, exchange fees, a 4-hour battery, lower efficiency.",
    f"<b>It is ready to use.</b> For {datetime.date.fromisoformat(nd['date']).strftime('%d %b %Y')}, the first day after our data, it bids to buy "
    f"{nd['buy_mwh']} MWh and sell {nd['sell_mwh']} MWh, expecting ₹{n(nd['expected_profit'])}.",
]
for i, x in enumerate(glance, 1):
    s.append(Paragraph(f"{i}.&nbsp;&nbsp;{x}", NUM))

s.append(Paragraph("1. How it works, and why we chose this method", H))
s.append(table([
    ["Step", "What it does", "Why this choice"],
    ["1. Guess tomorrow's prices", "Blend of two forecasters: <b>LEAR</b>, the standard research model for electricity prices (Lago et al., 2021), and "
     "<b>Chronos</b>, Amazon's deep-learning foundation model, a transformer pre-trained on many time series and used as it comes (Ansari et al., 2024). "
     "Mix: 40% LEAR, 60% Chronos, chosen on the validation year by money earned.",
     "In M3 each beat <i>tomorrow = today</i>; they make different mistakes, so the blend is steadier. Chronos also gives a likely range, not just one number."],
    ["2. Plan the battery", "A linear-programming optimiser picks how much to buy or sell in each slot to make the most money at the forecast prices.",
     "It finds the exact best plan in about a millisecond and can never break the battery's limits."],
    ["3. Write the bid", "Buy and sell orders for each active slot, with price limits taken from the forecast range, downloadable from the app.", "Ready to submit; the limits protect the trader if prices land far from the forecast."],
], [30, 92, 58]))
s.append(Paragraph(
    "<b>The optimiser in one line.</b> Maximise Σ<sub>t</sub> [ price<sub>t</sub> × sold<sub>t</sub> − price<sub>t</sub> × bought<sub>t</sub> − wear × sold<sub>t</sub> ] over the 96 slots, "
    "subject to: stored<sub>t</sub> = stored<sub>t−1</sub> + 0.938 × bought<sub>t</sub> − sold<sub>t</sub> / 0.938 (88% round trip); 2 ≤ stored ≤ 20 MWh, starting and ending at 2; "
    "bought and sold at most 2.5 MWh per slot (10 MW); and at most two full rounds a day. Profit is then counted at the <i>actual</i> prices.", B))

s.append(Paragraph("2. The working solution", H))
s.append(KeepTogether([fig("m4_app.jpg", 168), Paragraph(
    "Figure 1. The working solution (web/index.html; run <i>python3 -m http.server 8600 --directory web</i>). It opens on the trader's decision: "
    "tomorrow's plan in one sentence (when to buy, when to sell), the expected profit, a one-click download of the exchange orders with safety price "
    "limits, and the proof (₹/day and ₹ crore/year on an unseen year, extra over copying yesterday). Below it, a live simulator replays any of 730 real "
    "days slot by slot, with a day-night clock, battery gauge, running money ledger, live KPIs and a strategy switch, and eight one-click test days "
    "(winter, heatwave, monsoon, Sunday, holiday, price at the cap, best and worst day). Battery settings and presets sit in a drawer and re-plan "
    "everything instantly. A Streamlit version (app/app.py) adds an AI assistant on a local model (Qwen3 on Ollama).", CAP)]))

s.append(Paragraph("3. Performance", H))
rows = [["Plan (10 MW / 20 MWh, ₹1,000 wear)", "Validation year, ₹/day", "Test year, ₹/day", "Share of best (test)", "Per year (test)"]]
for lbl, k, shr in [("Fixed timetable (canvas)", "fixed", sh["fixed_vs_p1"]), ("Tomorrow = today, 1 round", "today_1", sh1["today"]),
                    ("Tomorrow = today, up to 2 rounds", "today_2", sh["today"]), ("Tomorrow = today + Sunday fix (M3)", "today_sun_2", sh["today_sun"]),
                    ("<b>Our assistant, 1 round</b>", "blend_1", sh1["blend"]), ("<b>Our assistant, up to 2 rounds</b>", "blend_2", sh["blend"]),
                    ("Perfect guess, up to 2 rounds (ceiling)", "perfect_2", 1.0)]:
    rows.append([lbl, n(v[k]), f"<b>{n(t[k])}</b>" if "assistant" in lbl else n(t[k]), pc(shr), crore(t[k])])
s.append(table(rows, [62, 32, 30, 28, 28]))
s.append(KeepTogether([fig("m4_monthly.png"), Paragraph(
    f"Figure 2. Left: extra money per day over <i>tomorrow = today</i>, month by month; the assistant is ahead in {M['months_positive']} of "
    f"{M['months_total']} months. Right: the same, added up, against the fixed timetable, which falls further behind every month.", CAP)]))

s.append(Paragraph("4. Validation: is the gain real?", H))
s.append(Paragraph(
    "Everything is tested on days the models never saw: the blend weight was chosen on the validation year and then fixed for the test year. We use two "
    "standard checks on the daily difference in money: a bootstrap that resamples whole weeks for a 95% range (Künsch, 1989), and the "
    "Diebold–Mariano test for the chance a gain is luck (Diebold and Mariano, 1995).", B))
trows = [["Our assistant compared with", "Validation: extra ₹/day (95% range)", "Test: extra ₹/day (95% range)", "Chance it is luck (test)", "Days better (test)"]]
for lbl, k in [("Tomorrow = today, up to 2 rounds", "blend_vs_today_2"), ("Tomorrow = today, 1 round", "blend_vs_today_1"),
               ("Tomorrow = today + Sunday fix", "blend_vs_todaysun_2"), ("Fixed timetable", "blend_vs_fixed_1")]:
    a_, b_ = TS["validate"][k], TS["test"][k]
    trows.append([lbl, f"+{n(a_['gain'])} ({ci(a_['ci'])})", f"+{n(b_['gain'])} ({ci(b_['ci'])})", pv(b_["p"]), pc(b_["share_days_better"], 0)])
s.append(table(trows, [50, 40, 38, 26, 26]))
s.append(KeepTogether([fig("m4_day.png"), Paragraph(
    f"Figure 3. One test-year winter day ({datetime.date.fromisoformat(ex['date']).strftime('%d %b %Y')}). The battery charges overnight and at midday, "
    f"sells into both the morning and the evening peak, and earns ₹{n(ex['assistant'])} against ₹{n(ex['perfect'])} for a perfect guess.", CAP)]))
s.append(Paragraph(
    f"<b>Where the gain comes from.</b> Sundays gain most (+₹{n(SEG['Sun']['gain'])} a day), because copying Saturday is a poor guess for Sunday. "
    f"By season the gain is +₹{n(SEG['Mar–Jun']['gain'])} in Mar–Jun, +₹{n(SEG['Jul–Sep']['gain'])} in Jul–Sep and +₹{n(SEG['Oct–Feb']['gain'])} in "
    f"Oct–Feb, when <i>tomorrow = today</i> is already strong. One weak spot: on Thursdays the assistant trails by ₹{n(-SEG['Thu']['gain'])} a day. "
    f"It runs a second round on {pc(M['share_days_two_rounds'], 0)} of days, only when its forecast says the second round pays for its wear.", B))

s.append(KeepTogether([fig("m3_models.png"), Paragraph(
    "Figure 4. Why we blend (from M3). Left: extra money over <i>tomorrow = today</i> for each forecaster, adding up over two years. Right: price error "
    "against money earned. Chronos guesses prices no better than copying yesterday, yet earns more, because it gets the shape of the day right. "
    "So we judge forecasters by money, not by price error, and pick the blend that earns most on the validation year.", CAP)]))
s.append(Paragraph("5. Robustness and risk", H))
srows = [["Setting (test year)", "Assistant, ₹/day", "Tomorrow = today, ₹/day", "Extra, ₹/day", "Share of best"]]
for r in SEN:
    srows.append([r["setting"], n(r["assistant ₹/day"]), n(r["tomorrow = today ₹/day"]), f"+{n(r['extra ₹/day'])}", pc(r["share of best"])])
s.append(table(srows, [62, 30, 34, 26, 28]))
s.append(Paragraph(
    f"<b>Bad days.</b> On the worst 5% of test days the assistant still earns ₹{n(RK['blend_2']['worst 5% of days, ₹'])}, its worst month averages "
    f"₹{n(RK['blend_2']['worst month avg, ₹/day'])} a day, and it had {RK['blend_2']['losing days']} losing days; the fixed timetable had "
    f"{RK['fixed']['losing days']}, with a worst 5% of ₹{n(RK['fixed']['worst 5% of days, ₹'])}.", B))

s.append(KeepTogether([fig("m4_risk.png", 170), Paragraph(
    "Figure 5. Money earned per day on the test year. The assistant moves the whole spread of days to the right: bad days are no worse, typical days are better.", CAP)]))
s.append(Paragraph("6. Assumptions and limitations", H))
for x in [
    "<b>Battery.</b> 10 MW / 20 MWh, 88% round trip, charge kept between 10% and 100% and back to 10% each night, at most two rounds a day, wear "
    "₹1,000 per MWh sold. The app lets the user change all of these.",
    "<b>Market.</b> One all-India price; the battery is too small to move it (0.13% of typical volume). The ₹10,000 cap hides true scarcity. Exchange fees, "
    "transmission and taxes are excluded in the base case; fees are tested in Section 5.",
    "<b>Models.</b> LEAR is refitted weekly, and Chronos is not fine-tuned on Indian prices; both could improve further. The blend's edge over plain LEAR "
    "(M3) is small. The assistant trails on Thursdays, which is the next thing to fix. Results come from one test year.",
]:
    s.append(Paragraph(x, B))

s.append(Paragraph("References", H))
for r in [
    "Ansari, A. F. et al. (2024). Chronos: Learning the language of time series. <i>Transactions on Machine Learning Research</i>.",
    "Diebold, F. X. and Mariano, R. S. (1995). Comparing predictive accuracy. <i>Journal of Business &amp; Economic Statistics</i>, 13(3), 253–263.",
    "Künsch, H. R. (1989). The jackknife and the bootstrap for general stationary observations. <i>Annals of Statistics</i>, 17(3), 1217–1241.",
    "Lago, J., Marcjasz, G., De Schutter, B. and Weron, R. (2021). Forecasting day-ahead electricity prices: A review of state-of-the-art algorithms, "
    "best practices and an open-access benchmark. <i>Applied Energy</i>, 293, 116983.",
    "Data: Indian Energy Exchange Day-Ahead Market; Chronos-Bolt model weights (amazon/chronos-bolt-small, Hugging Face).",
]:
    s.append(Paragraph(r, REF))

SimpleDocTemplate(out, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=11 * mm, bottomMargin=10 * mm,
                  title="D01 M4 Working Solution", author="Team D01", creator="Team D01", producer="Team D01").build(s)

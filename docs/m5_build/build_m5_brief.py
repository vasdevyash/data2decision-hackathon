"""Build the M5 decision brief (max 2 pages). Usage: python build_m5_brief.py <out.pdf> <outputs/m4_metrics.json> <outputs/figures>"""
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
sh, sh1 = M["share_test"], M["share_test_1"]
g2, gf = TS["test"]["blend_vs_today_2"], TS["test"]["blend_vs_fixed_1"]
vs_fixed = t["blend_2"] - t["fixed"]
M3 = json.load(open(sys.argv[2].replace("m4_metrics", "m3_metrics")))
dbl = next(k for k in M3["day_types"]["table"] if k.startswith("Double"))
cr = lambda x: f"₹{x / 1e7:.2f} crore"
op = t["blend_2"] * 365; capex = 0.80e7 * 20; om = 0.02 * capex; cf = op - om
npv = -capex + sum(cf / 1.10 ** y for y in range(1, 13)); pay = capex / cf
B2 = st("b2", fontSize=9.4, leading=12.6, spaceAfter=3)
P = lambda x: Paragraph(x, B)

s = [Paragraph("Decision Brief: Run the Battery Copilot on the IEX Day-Ahead Market", T),
     Paragraph("Team D01 · Energy &amp; Renewables · For the trading and operations head of a battery storage operator · "
               "Prototype: web/index.html · github.com/vasdevyash/data2decision-hackathon", META)]
s.append(Paragraph(
    f"<b>Recommendation: adopt the Battery Copilot to plan and bid the battery every day, starting with a 30-day shadow run.</b> On a full year of real "
    f"prices it had never seen, it earned <b>₹{n(t['blend_2'])} a day ({cr(op)} a year)</b> for a 10 MW / 20 MWh battery: {pc(sh['blend'])} of the most "
    f"any trader could have earned with perfect hindsight, <b>₹{n(vs_fixed)} a day more</b> than the fixed timetable in the brief, and "
    f"<b>₹{n(g2['gain'])} a day (₹{g2['gain'] * 365 / 1e5:.1f} lakh a year) more</b> than copying yesterday's prices. The battery pays back its capital in "
    f"<b>{pay:.1f} years</b> (net present value {cr(npv)} over 12 years at 10%).", B2))

s.append(Paragraph("1. The decision", H))
s.append(P("Every morning the trader must commit tomorrow's plan to the exchange before noon: for each of 96 fifteen-minute slots, buy, sell or wait, and how "
           "much, without knowing tomorrow's prices. Prices swing from about ₹1,500 at midday to the ₹10,000 cap in the evening, so the plan decides most of the "
           "battery's income. Today this is done with a fixed timetable or by copying yesterday."))

s.append(Paragraph("2. What we found", H))
for i, x in enumerate([
    f"<b>A fixed timetable leaves {cr(vs_fixed * 365)} a year on the table.</b> It captures only {pc(sh['fixed_vs_p1'], 0)} of the possible profit and loses money on "
    f"scarcity days, when midday and evening are both at the cap.",
    f"<b>Forecasting plus optimisation captures {pc(sh['blend'], 0)}, and the gain is real.</b> It beats copying yesterday on both unseen years (95% range ₹{n(g2['ci'][0])} to "
    f"₹{n(g2['ci'][1])} a day; chance it is luck below 0.1%) and in {M['months_positive']} of {M['months_total']} months, with no losing days.",
    f"<b>The biggest lever is a second buy-sell round on winter days with a morning and an evening peak.</b> On those days it is worth "
    f"₹{n(M3['day_types']['table'][dbl]['v2_hind'])}; the copilot uses it only when it pays for the wear ({pc(M['share_days_two_rounds'], 0)} of days).",
    f"<b>It wins most where simple rules fail.</b> On Sundays it earns ₹{n(SEG['Sun']['gain'])} a day more than copying Saturday. Its weak spot is Thursday "
    f"(₹{n(-SEG['Thu']['gain'])} a day behind), which is the first thing to improve.",
    "<b>It is cheap to run.</b> Weather data adds nothing, and a ready-made AI forecasting model (Chronos) earns as much as a tuned research model (LEAR), "
    "so the system needs only exchange prices and runs on a laptop in seconds.",
], 1):
    s.append(Paragraph(f"{i}.&nbsp;&nbsp;{x}", NUM))
s.append(KeepTogether([fig("m4_monthly.png", 172), Paragraph(
    f"Figure 1. Extra profit over copying yesterday, month by month (left; ahead in {M['months_positive']} of {M['months_total']} months) and added up over two "
    "years (right), against the fixed timetable.", CAP)]))

s.append(Paragraph("3. Expected value", H))
s.append(table([
    ["10 MW / 20 MWh battery, test year", "Per day", "Per year", "Share of best possible"],
    ["Fixed timetable (today's practice in the brief)", f"₹{n(t['fixed'])}", cr(t["fixed"] * 365), pc(sh["fixed_vs_p1"])],
    ["Copy yesterday's prices", f"₹{n(t['today_2'])}", cr(t["today_2"] * 365), pc(sh["today"])],
    ["<b>Battery Copilot</b>", f"<b>₹{n(t['blend_2'])}</b>", f"<b>{cr(op)}</b>", f"<b>{pc(sh['blend'])}</b>"],
    ["Perfect hindsight (ceiling, not achievable)", f"₹{n(t['perfect_2'])}", cr(t["perfect_2"] * 365), "100%"],
], [80, 30, 34, 36]))
s.append(P(f"<b>Business case.</b> Trading profit after wear {cr(op)} a year, fixed O&amp;M {cr(om)}, cash flow {cr(cf)}. Capital {cr(capex)} at the CTUIL benchmark "
           f"of ₹0.80 crore per MWh: payback {pay:.1f} years, net present value {cr(npv)}. The copilot alone is worth ₹{g2['gain'] * 365 / 1e5:.1f} lakh a year per "
           "10 MW battery over copying yesterday, and scales with storage while the battery stays too small to move prices (about 300 MW)."))

s.append(Paragraph("4. How to implement it", H))
s.append(table([
    ["Phase", "What happens", "Success test"],
    ["Weeks 1–4: shadow", "Copilot plans every day; trader keeps current method; both are scored at real prices", "Copilot ahead on most days, alerts quiet"],
    ["Month 2: live with approval", "Trader approves the copilot's bid each morning (one click); safety price limits on every order", "Profit share above 90%; no limit breaches"],
    ["Month 3 on: scale", "Roll out across the fleet; monthly model review; fix the Thursday weak spot; re-test when market coupling goes live", "Gain holds by season"],
], [32, 98, 50]))
s.append(P("<b>Daily routine:</b> 09:00 data loads, 09:30 forecast, 10:00 plan and pre-bid checks, 10:30 trader approves, orders in before the 12:00 exchange deadline, "
           "results logged next morning. <b>Needs:</b> the IEX price feed, one small server, and the trader's approval step; all software is open source."))

s.append(Paragraph("5. Risks and how we control them", H))
s.append(table([
    ["Risk", "Control"],
    ["Prices behave differently (new regime, market coupling)", f"Weekly refits; Audit tab alerts when profit share falls below 90% or error rises (it flags review today after a volatile month)"],
    ["A forecast is badly wrong on the day", f"Safety price limits on every order; worst 5% of test days still earned ₹{n(RK['blend_2']['worst 5% of days, ₹'])}"],
    ["Battery wear or fees higher than assumed", "Stress-tested: still ahead at wear ₹0–1,500/MWh, ₹20/MWh fees, 4-hour battery, 85% efficiency"],
    ["Limits of the evidence", "One all-India price, one test year, prices capped at ₹10,000; transmission charges and taxes excluded, as in the brief"],
], [62, 118]))
s.append(Paragraph("6. The working solution", H))
s.append(KeepTogether([fig("m5_tomorrow.jpg", 165), Paragraph(
    "Figure 2. The Battery Copilot (web/index.html). It opens on tomorrow's decision in one sentence, the expected profit and a one-click download of the "
    "exchange orders, with pre-bid checks and an approval button. Other tabs replay any of 730 real days, show the business case (P&amp;L, payback, NPV) "
    "and monitor the model every day.", CAP)]))
s.append(P("<b>What we ask.</b> Approve a 30-day shadow run on one battery, with access to the IEX day-ahead price feed and one trader for a ten-minute "
           "review each morning. Go-live is decided on the shadow results."))
s.append(P("<b>Conclusion.</b> The battery's income depends on one daily decision. The copilot makes that decision better than today's methods, proves it on a year "
           "it never saw, and fits the existing trading routine with a single approval step. We recommend a 30-day shadow run, then going live."))

SimpleDocTemplate(out, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=11 * mm, bottomMargin=10 * mm,
                  title="D01 M5 Decision Brief", author="Team D01", creator="Team D01", producer="Team D01").build(s)

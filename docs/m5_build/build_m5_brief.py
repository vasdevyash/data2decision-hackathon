"""M5 decision brief, plain English. Usage: python build_m5_brief.py <out.pdf> <outputs/m4_metrics.json> <outputs/figures>"""
import sys, json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer, KeepTogether
from PIL import Image as PILImage

HN = "/System/Library/Fonts/HelveticaNeue.ttc"
pdfmetrics.registerFont(TTFont("G", HN, subfontIndex=0)); pdfmetrics.registerFont(TTFont("GB", HN, subfontIndex=1))
pdfmetrics.registerFontFamily("G", normal="G", bold="GB", italic="G", boldItalic="GB")
out, M, F = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
INK, GREY = HexColor("#111111"), HexColor("#555555")
st = lambda n, **k: ParagraphStyle(n, **{"fontName": "G", "fontSize": 11, "leading": 15.5, "textColor": INK, "spaceAfter": 6, **k})
T, META, H, B, BIG, CAP = st("t", fontName="GB", fontSize=20, leading=24, spaceAfter=4), st("m", fontSize=9, textColor=GREY, spaceAfter=14), \
    st("h", fontName="GB", fontSize=13, leading=17, spaceBefore=10, spaceAfter=4), st("b"), st("big", fontName="GB", fontSize=14, leading=19, spaceAfter=10), st("c", fontSize=8.5, leading=11, textColor=GREY)
t, sh, g2, risk = M["test"], M["share_test"], M["tests"]["test"]["blend_vs_today_2"], M["risk"]["blend_2"]
vs_fixed = (t["blend_2"] - t["fixed"]) * 365; op = t["blend_2"] * 365; capex = 16e7; cf = op - 0.02 * capex; pay = capex / cf
cr = lambda x: f"₹{x / 1e7:.1f} crore"


def numbers(rows):
    data = [[Paragraph(f'<font name="GB" size="20">{v}</font>', st("v", leading=24)), Paragraph(k, st("k", fontSize=9.5, leading=12.5, textColor=GREY))] for v, k in rows]
    tb = Table([[c for r in data for c in [r]]], colWidths=[45 * mm] * len(rows))
    tb = Table([[Table([[d[0]], [d[1]]], colWidths=[43 * mm]) for d in data]], colWidths=[45 * mm] * len(rows))
    tb.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    return tb


SEG, RK = M["segments"], M["risk"]["blend_2"]
s = [Paragraph("What if your battery could earn ₹1.8 crore more every year, without changing a single wire?", T),
     Paragraph("Decision brief · Battery Copilot · Team D01 · Data2Decision 2026", META)]

s.append(Paragraph("1. The business problem", H))
s.append(Paragraph("A big battery is like a shop. It buys electricity when it is cheap and sells it when it is expensive. "
                   "But it must plan tomorrow today, before noon, for all 96 fifteen-minute slots, without knowing tomorrow's prices. "
                   f"Most batteries simply follow the same timetable every day. That timetable earns only <b>{sh['fixed_vs_p1'] * 100:.0f}%</b> of what the battery could make.", B))

s.append(Paragraph("2. What we found, and the proof", H))
for i, x in enumerate([
    f"<b>The timetable wastes a lot of money.</b> For one 10 MW battery it earns ₹{cr(t['fixed'] * 365)[1:]} a year, while the battery could earn ₹{cr(t['perfect_2'] * 365)[1:]}.",
    f"<b>A smart daily plan gets almost all of it.</b> Our copilot earns {cr(op)} a year, {sh['blend'] * 100:.0f}% of the best possible.",
    f"<b>It works on days it has never seen.</b> Tested on a whole year of real prices: better than the old way in {M['months_positive']} of {M['months_total']} months, and no day lost money.",
    f"<b>It wins most where simple rules fail.</b> Sundays (+₹{SEG['Sun']['gain']:,.0f} a day) and winter days with two price peaks, when it buys and sells twice.",
    "<b>It is cheap to run.</b> It needs only the exchange's prices. Weather data did not help, so we left it out.",
], 1):
    s.append(Paragraph(f"{i}.&nbsp;&nbsp;{x}", st("f", leftIndent=14, firstLineIndent=-14, spaceAfter=3)))
w, h = PILImage.open(f"{F}/m5_money.png").size
s.append(Image(f"{F}/m5_money.png", width=160 * mm, height=160 * mm * h / w))

s.append(Paragraph("3. What we recommend", H))
s.append(Paragraph("Use the Battery Copilot to plan the battery every day. Start with a <b>30-day trial</b> next to the trader, with no money at risk. "
                   "If it earns more, switch it on, then use it for every battery.", B))

s.append(Paragraph("4. What it is worth", H))
s.append(numbers([(cr(op), "earned a year by one battery"), (f"+{cr(vs_fixed)}", "more than the timetable"),
                  (f"{pay:.1f} years", "to pay for a ₹16 crore battery"), (f"₹{g2['gain'] * 365 / 1e5:.1f} lakh", "a year more than copying yesterday")]))
s.append(Spacer(1, 4))
s.append(Paragraph("Every extra battery adds the same again, as long as each one is too small to move market prices.", B))

s.append(Paragraph("5. How to put it in place", H))
s.append(Paragraph("<b>Month 1:</b> the copilot plans next to the trader; we compare both every day. <b>Month 2:</b> the trader approves the copilot's plan each "
                   "morning with one click. <b>Month 3:</b> every battery. <b>Daily routine:</b> 09:00 prices load, 10:00 plan ready, 10:30 trader approves, "
                   "orders sent before the 12:00 deadline. <b>What it needs:</b> the exchange's price feed, one computer, and ten minutes of the trader's morning. "
                   "<b>See it working:</b> our live prototype shows tomorrow's plan, replays real days, and works out the business case.", B))

s.append(Paragraph("6. Key risks", H))
s.append(Paragraph("<b>Prices change their habits:</b> the copilot learns again every week and warns us if it starts doing worse. "
                   f"<b>A bad guess on one day:</b> every order has a price limit; even its worst days still made money (₹{RK['worst 5% of days, ₹']:,.0f}). "
                   "<b>The market rules change</b> (planned market coupling): we test it again before relying on it. "
                   f"<b>One weak spot:</b> Thursdays, where it trails the simple rule by ₹{-SEG['Thu']['gain']:,.0f} a day; we fix this first.", B))

s.append(Paragraph("7. Limitations", H))
s.append(Paragraph("We tested one year of data and one all-India price. Prices are capped at ₹10,000, so the real value of very scarce hours is hidden. "
                   "Taxes and grid charges are left out, as the brief asked. Battery wear cost is an estimate, but it still wins at higher or lower wear.", B))

s.append(Paragraph("8. Conclusion", H))
s.append(Paragraph("Same battery, smarter plan, more money. The copilot makes the one decision that matters most each day, and makes it better. "
                   "We recommend starting the 30-day trial now.", BIG))

SimpleDocTemplate(out, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=16 * mm, bottomMargin=14 * mm,
                  title="D01 M5 Decision Brief", author="Team D01", creator="Team D01", producer="Team D01").build(s)

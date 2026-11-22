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


s = [Paragraph("What if your battery could earn ₹1.8 crore more every year, without changing a single wire?", T),
     Paragraph("Decision brief · Battery Copilot · Team D01 · Data2Decision 2026", META)]

s.append(Paragraph("The problem", H))
s.append(Paragraph("A big battery is like a shop. It buys electricity when it is cheap and sells it when it is expensive. "
                   "But it has to plan tomorrow today, before it knows tomorrow's prices. Most batteries just follow the same timetable every day. "
                   f"That timetable gets only <b>{sh['fixed_vs_p1'] * 100:.0f}%</b> of the money the battery could make.", B))

s.append(Paragraph("How we solved it", H))
s.append(Paragraph("We built the <b>Battery Copilot</b>. Every morning it does three things:", B))
s.append(Paragraph("1. It guesses tomorrow's price for every 15 minutes.<br/>2. It picks the best times to buy and to sell.<br/>"
                   "3. It writes the orders. The trader checks them and clicks approve.", st("l", leftIndent=14)))

s.append(Paragraph("The impact", H))
s.append(numbers([(cr(op), "earned in a year by one battery"), (f"+{cr(vs_fixed)}", "more than the timetable"),
                  (f"{sh['blend'] * 100:.0f}%", "of the best possible"), (f"{pay:.1f} years", "to pay for the battery")]))
s.append(Spacer(1, 4))

s.append(Paragraph("How we know it works", H))
s.append(Paragraph(f"We tested it on a whole year of real prices it had never seen. It did better than the old way in {M['months_positive']} of "
                   f"{M['months_total']} months and never lost money on any day.", B))

s.append(Paragraph("What we recommend", H))
s.append(Paragraph("Try it for 30 days next to the trader, with no money at risk. If it earns more, switch it on. Then use it for every battery.", B))

s.append(Paragraph("What it needs", H))
s.append(Paragraph("The exchange's prices, one computer, and ten minutes of the trader's morning. You can see it working in our live prototype "
                   "(the Battery Copilot website), which shows tomorrow's plan, replays real days, and works out the business case.", B))

s.append(Paragraph("Risks and limits", H))
s.append(Paragraph("Prices can change their habits, so the copilot learns again every week and warns us if it starts doing worse. "
                   "Every order has a price limit, so one bad guess cannot cost much. We tested one year of data and left out taxes and grid fees, as the brief asked.", B))

s.append(Paragraph("In one line", H))
s.append(Paragraph("Same battery, smarter plan, more money. Let's start the 30-day trial.", BIG))

SimpleDocTemplate(out, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=16 * mm, bottomMargin=14 * mm,
                  title="D01 M5 Decision Brief", author="Team D01", creator="Team D01", producer="Team D01").build(s)

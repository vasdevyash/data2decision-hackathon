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


s = [Paragraph("Battery Copilot: a better plan for the battery, every day", T),
     Paragraph("Decision brief · Team D01 · Energy &amp; Renewables · Data2Decision 2026", META),
     Paragraph(f"We recommend running the Battery Copilot alongside the trader for 30 days, then switching it on. "
               f"It would earn about <b>{cr(op)} a year</b> from one 10 MW battery, <b>{cr(vs_fixed)} more</b> than today's fixed timetable.", BIG)]

s.append(Paragraph("The problem", H))
s.append(Paragraph("A battery makes money by buying electricity when it is cheap, around midday, and selling it when it is dear, in the evening. "
                   "Every morning the trader must lock in tomorrow's plan, slot by slot, before noon, without knowing tomorrow's prices. "
                   f"Today this is done by a fixed timetable, which captures only {sh['fixed_vs_p1'] * 100:.0f}% of what the battery could earn.", B))

s.append(Paragraph("What we built", H))
s.append(Paragraph("A copilot that does this job in seconds. Each morning it predicts tomorrow's prices, works out the best times to buy and sell, "
                   "and writes the orders. The trader checks the plan and approves it with one click.", B))
w, h = PILImage.open(f"{F}/m5_tomorrow.jpg").size
s.append(KeepTogether([Image(f"{F}/m5_tomorrow.jpg", width=150 * mm, height=150 * mm * h / w),
                       Paragraph("The copilot opens on tomorrow's plan: when to buy, when to sell, the expected profit, and a button to send the orders.", CAP)]))

s.append(Paragraph("What it earns", H))
s.append(numbers([(cr(op), "profit a year, one 10 MW battery"), (f"{sh['blend'] * 100:.0f}%", "of the most any trader could earn"),
                  (f"+{cr(vs_fixed)}", "a year more than the fixed timetable"), (f"{pay:.1f} years", "to pay back the battery")]))
s.append(Spacer(1, 6))

s.append(Paragraph("Why you can trust it", H))
s.append(Paragraph(f"We tested it on a full year of real prices it had never seen. It beat today's methods in {M['months_positive']} of {M['months_total']} months "
                   f"and never had a losing day. Even on its worst days it still made money (₹{risk['worst 5% of days, ₹']:,.0f} on a bad day).", B))

s.append(Paragraph("What it is worth", H))
s.append(Paragraph(f"For one battery: {cr(op)} of profit a year and a {pay:.1f}-year payback on a ₹16 crore battery. "
                   f"The copilot itself adds ₹{g2['gain'] * 365 / 1e5:.1f} lakh a year over simply copying yesterday's plan, and the value grows with every battery added.", B))

s.append(Paragraph("How to start", H))
s.append(Paragraph("<b>Month 1:</b> the copilot plans every day next to the trader, with no money at risk. "
                   "<b>Month 2:</b> the trader approves the copilot's plan each morning. "
                   "<b>Month 3:</b> roll it out to every battery. All it needs is the exchange's price feed, one computer, and ten minutes of the trader's morning.", B))

s.append(Paragraph("Risks", H))
s.append(Paragraph("Prices can change their pattern, so the copilot re-learns every week and flags anything unusual. A bad forecast is capped by price "
                   "limits on every order. Results come from one year of data and leave out taxes and grid charges, as the brief did.", B))

s.append(Paragraph("Our recommendation", H))
s.append(Paragraph("Approve a 30-day side-by-side trial. If the copilot wins, switch it on.", B))

SimpleDocTemplate(out, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=16 * mm, bottomMargin=14 * mm,
                  title="D01 M5 Decision Brief", author="Team D01", creator="Team D01", producer="Team D01").build(s)

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


s = [Paragraph("Your battery is leaving money on the table every day. We fixed that.", T),
     Paragraph("Decision brief · Battery Copilot · Team D01 · Data2Decision 2026", META),
     Paragraph(f"For one 10 MW battery, the Battery Copilot earns <b>{cr(op)} a year</b>, which is <b>{cr(vs_fixed)} more</b> than today's way of trading. "
               "We ask you to try it for 30 days, at no risk.", BIG)]

s.append(Paragraph("The problem nobody talks about", H))
s.append(Paragraph("A battery only makes money one way: buy electricity when it is cheap and sell it when it is dear. Simple. But every morning, before noon, "
                   "the trader has to lock in tomorrow's plan, 96 decisions in all, without knowing tomorrow's prices. Most operators fall back on a fixed timetable: "
                   f"charge at midday, sell in the evening. It feels safe. It is not. It captures only <b>{sh['fixed_vs_p1'] * 100:.0f}%</b> of what the battery could earn, "
                   f"and quietly gives away <b>{cr(vs_fixed)}</b> every year.", B))

s.append(Paragraph("Our solution", H))
s.append(Paragraph("The Battery Copilot does the trader's hardest job in seconds. Every morning it predicts tomorrow's prices, finds the best moments to buy and to sell, "
                   "and writes the orders ready to send. The trader reads one sentence, checks the plan, and approves it with one click. "
                   "No new hardware. No new team. Just a better decision, every single day.", B))

s.append(Paragraph("The results speak for themselves", H))
s.append(numbers([(cr(op), "profit a year from one battery"), (f"{sh['blend'] * 100:.0f}%", "of the most any trader could earn"),
                  (f"+{cr(vs_fixed)}", "a year more than today"), (f"{pay:.1f} years", "to pay back the battery")]))
s.append(Spacer(1, 4))
s.append(Paragraph(f"We did not test it on easy data. We tested it on a full year of real market prices it had never seen. It beat today's methods in "
                   f"<b>{M['months_positive']} of {M['months_total']} months</b>, and it <b>never lost money on a single day</b>. Even on its worst days, it still made a profit.", B))

s.append(Paragraph("Why now", H))
s.append(Paragraph("India is adding solar and batteries faster than ever. That makes prices swing harder between midday and evening, and every swing is money for "
                   "whoever times it best. The operators who plan smartly will earn more from the same battery. The ones who stick to a timetable will fall further behind.", B))

s.append(Paragraph("Why it is safe", H))
s.append(Paragraph("The trader stays in charge. Every plan is checked before it goes out, every order carries a price limit so a bad surprise cannot hurt much, "
                   "and the copilot is watched every day so any drop in performance is flagged at once. It re-learns every week as the market changes.", B))

s.append(Paragraph("What it is worth to you", H))
s.append(Paragraph(f"One battery: {cr(op)} a year and a {pay:.1f}-year payback. Every battery you add multiplies the gain. And it costs almost nothing to run: "
                   "it needs only the exchange's prices and one computer.", B))

s.append(Paragraph("What we are asking for", H))
s.append(Paragraph("<b>30 days, side by side.</b> The copilot plans every day next to your trader, with no money at risk. You compare the results. "
                   "If it earns more, and we are confident it will, switch it on. Month two: the trader approves its plan each morning. Month three: every battery.", B))

s.append(Paragraph("Every day you wait, the battery earns less than it could. Let's start the trial.", BIG))

SimpleDocTemplate(out, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=16 * mm, bottomMargin=14 * mm,
                  title="D01 M5 Decision Brief", author="Team D01", creator="Team D01", producer="Team D01").build(s)

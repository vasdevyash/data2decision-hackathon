"""Board deck for M5 (16:9 PDF). Usage: python build_m5_deck.py <out.pdf> <outputs/m4_metrics.json> <outputs/figures>"""
import sys, json
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

HN = "/System/Library/Fonts/HelveticaNeue.ttc"
pdfmetrics.registerFont(TTFont("R", HN, subfontIndex=0)); pdfmetrics.registerFont(TTFont("B", HN, subfontIndex=1))
out, M, F = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
W, H = 960, 540
INK, MUTED, BLUE, LINE, GREEN, RED, SOFT = HexColor("#0b1220"), HexColor("#4b5563"), HexColor("#2563eb"), HexColor("#e5e7eb"), HexColor("#059669"), HexColor("#dc2626"), HexColor("#f6f7f9")
t, sh, TS, SEG, RK = M["test"], M["share_test"], M["tests"], M["segments"], M["risk"]
g2 = TS["test"]["blend_vs_today_2"]; vs_fixed = t["blend_2"] - t["fixed"]
op = t["blend_2"] * 365; capex = 16e7; cf = op - 0.02 * capex; npv = -capex + sum(cf / 1.1 ** y for y in range(1, 13)); pay = capex / cf
n = lambda x: f"{x:,.0f}"; cr = lambda x: f"₹{x / 1e7:.2f} crore"
c = canvas.Canvas(out, pagesize=(W, H)); c.setTitle("Battery Copilot · Board presentation · Team D01"); c.setAuthor("Team D01")
page = [0]


def text(x, y, s, size=16, font="R", color=INK, anchor="l"):
    c.setFont(font, size); c.setFillColor(color)
    (c.drawString if anchor == "l" else c.drawRightString if anchor == "r" else c.drawCentredString)(x, y, s)


def wrap(x, y, s, size=16, width=800, font="R", color=INK, lead=1.35):
    words, line, yy = s.split(), "", y
    for w in words:
        trial = (line + " " + w).strip()
        if pdfmetrics.stringWidth(trial, font, size) > width: text(x, yy, line, size, font, color); yy -= size * lead; line = w
        else: line = trial
    if line: text(x, yy, line, size, font, color); yy -= size * lead
    return yy


def slide(kicker, title, sub=None):
    page[0] += 1
    if page[0] > 1: c.showPage()
    c.setFillColor(HexColor("#ffffff")); c.rect(0, 0, W, H, fill=1, stroke=0)
    text(56, H - 58, kicker.upper(), 11, "B", BLUE)
    yy = wrap(56, H - 92, title, 30, 850, "B", INK, 1.18)
    if sub: yy = wrap(56, yy - 4, sub, 15, 840, "R", MUTED)
    c.setStrokeColor(LINE); c.line(56, 34, W - 56, 34)
    text(56, 18, "Battery Copilot · Team D01 · Data2Decision 2026", 9, "R", MUTED); text(W - 56, 18, str(page[0]), 9, "R", MUTED, "r")
    return yy


def tile(x, y, w, h, label, value, sub, dark=False, vcolor=None):
    c.setFillColor(INK if dark else SOFT); c.setStrokeColor(INK if dark else LINE); c.roundRect(x, y, w, h, 12, fill=1, stroke=1)
    text(x + 18, y + h - 28, label, 12, "R", HexColor("#cbd5e1") if dark else MUTED)
    vs = 32
    while pdfmetrics.stringWidth(value, "B", vs) > w - 34 and vs > 18: vs -= 1
    text(x + 18, y + h - 70, value, vs, "B", HexColor("#ffffff") if dark else (vcolor or INK))
    wrap(x + 18, y + 22, sub, 11, w - 30, "R", HexColor("#cbd5e1") if dark else MUTED)


def image(path, x, y, w, h=None, border=True):
    img = ImageReader(path); iw, ih = img.getSize(); h = h or w * ih / iw
    if h > 0 and w * ih / iw > h: w = h * iw / ih
    else: h = w * ih / iw
    c.drawImage(img, x, y, w, h, mask="auto")
    if border: c.setStrokeColor(LINE); c.rect(x, y, w, h, fill=0, stroke=1)
    return w, h


# 1 Title
page[0] += 1; c.setFillColor(INK); c.rect(0, 0, W, H, fill=1, stroke=0)
text(64, 380, "BATTERY COPILOT", 14, "B", HexColor("#93c5fd"))
text(64, 320, "One daily decision,", 46, "B", HexColor("#ffffff")); text(64, 266, f"{cr(op)} a year.", 46, "B", HexColor("#ffffff"))
wrap(64, 220, "An AI copilot that plans and bids a grid battery on the Indian Energy Exchange every day, proven on a year of real prices it never saw.", 17, 760, "R", HexColor("#cbd5e1"))
text(64, 70, "Team D01 · Energy & Renewables · Data2Decision 2026", 12, "R", HexColor("#94a3b8"))

# 2 The decision
yy = slide("The decision", "Every morning, the trader commits 96 buy or sell decisions before noon, without knowing tomorrow's prices.")
tile(56, 150, 268, 170, "Prices swing every day", "₹1,500 to ₹10,000", "from a cheap solar midday to the capped evening peak, per MWh")
tile(346, 150, 268, 170, "Today's practice", f"{sh['fixed_vs_p1'] * 100:.0f}%", "of the possible profit captured by the fixed timetable in the brief")
tile(636, 150, 268, 170, "Money left on the table", cr(vs_fixed * 365), "a year, per 10 MW / 20 MWh battery", dark=True)
wrap(56, 110, "The plan decides most of the battery's income. Getting it right every day is the whole business.", 16, 840, "R", MUTED)

# 3 Our answer
slide("Our answer", "Forecast tomorrow, find the best plan, send the orders. In under a second.")
steps = [("1", "Forecast", "Two models predict all 96 prices for tomorrow and we blend them: LEAR, the standard research model for electricity prices, and Chronos, a deep-learning foundation model."),
         ("2", "Optimise", "An exact optimiser finds the buy and sell plan that earns the most after losses and battery wear, and never breaks the battery's limits."),
         ("3", "Bid", "The plan becomes exchange orders with safety price limits. The trader reviews the pre-bid checks and approves with one click.")]
for i, (num, head, body) in enumerate(steps):
    x = 56 + i * 292; c.setFillColor(SOFT); c.setStrokeColor(LINE); c.roundRect(x, 110, 270, 250, 12, fill=1, stroke=1)
    c.setFillColor(INK); c.circle(x + 34, 322, 17, fill=1, stroke=0); text(x + 34, 316, num, 16, "B", HexColor("#ffffff"), "c")
    text(x + 62, 315, head, 22, "B"); wrap(x + 22, 270, body, 14, 230, "R", MUTED)

# 4 The product
slide("The product", "It opens on the answer: what to buy, when to sell, and what it will earn.")
image(f"{F}/m5_tomorrow.jpg", 56, 48, 560, 330)
yy = 370
for hd, bd in [("Tomorrow's plan in one sentence", "Expected profit, pre-bid checks and one-click approval"), ("Exchange orders, ready to download", "with safety price limits from the forecast range"),
               ("Replay, business case, audit", "any of 730 real days, payback and NPV, daily model monitoring")]:
    yy = wrap(640, yy, hd, 16, 260, "B"); yy = wrap(640, yy - 2, bd, 14, 260, "R", MUTED) - 22

# 5 Results
slide("Results on a year it never saw", f"{sh['blend'] * 100:.1f}% of the best possible profit, every day, automatically.")
tile(56, 170, 200, 170, "Profit per day", f"₹{n(t['blend_2'])}", "10 MW / 20 MWh battery, after wear", dark=True)
tile(272, 170, 200, 170, "Profit per year", cr(op), "test year, real prices")
tile(488, 170, 200, 170, "vs fixed timetable", f"+₹{n(vs_fixed)}", "per day, same battery", vcolor=GREEN)
tile(704, 170, 200, 170, "vs copying yesterday", f"+₹{n(g2['gain'])}", f"per day · ₹{g2['gain'] * 365 / 1e5:.1f} lakh a year", vcolor=GREEN)
wrap(56, 130, f"Biggest gains on Sundays (+₹{n(SEG['Sun']['gain'])} a day) and on winter days with two price peaks, where simple rules fail.", 16, 840, "R", MUTED)

# 6 Proof
slide("Proof", "The gain is real, steady and safe, not luck.")
image(f"{F}/m4_monthly.png", 56, 190, 560, border=False)
for i, (h, b) in enumerate([("Two unseen years", "Model chosen on year one, frozen, then tested on year two"),
                            (f"Ahead in {M['months_positive']} of {M['months_total']} months", "steady, not one lucky season"),
                            ("Chance it is luck < 0.1%", f"95% range +₹{n(g2['ci'][0])} to +₹{n(g2['ci'][1])} a day"),
                            (f"{RK['blend_2']['losing days']} losing days", f"worst 5% of days still earned ₹{n(RK['blend_2']['worst 5% of days, ₹'])}")]):
    y = 372 - i * 78; text(640, y, h, 17, "B"); wrap(640, y - 22, b, 13, 270, "R", MUTED)

# 7 Business case
slide("Business case", f"Pays back in {pay:.1f} years. Worth {cr(npv)} over its life.")
tile(56, 200, 200, 150, "Capital cost", cr(capex), "₹0.80 crore per MWh, CTUIL benchmark")
tile(272, 200, 200, 150, "Cash flow per year", cr(cf), "after wear and 2% O&M", dark=True)
tile(488, 200, 200, 150, "Payback", f"{pay:.1f} years", "capital ÷ yearly cash flow")
tile(704, 200, 200, 150, "Net present value", cr(npv), "12 years at 10% a year", vcolor=GREEN)
wrap(56, 160, f"The copilot alone adds ₹{g2['gain'] * 365 / 1e5:.1f} lakh a year per 10 MW battery over copying yesterday, and {cr(vs_fixed * 365)} over the fixed timetable. Value scales with the fleet while each battery stays too small to move prices.", 16, 850, "R", MUTED)

# 8 Control
slide("The trader stays in control", "Every bid is checked, approved and audited.")
image(f"{F}/m5_audit.jpg", 56, 60, 470, 300)
for i, (h, b) in enumerate([("Pre-bid checks", "power, reserve, wear, low-price exposure, price limits"), ("One-click approval", "logged with time, battery and expected profit"),
                            ("Safety price limits", "orders stop if prices land far from the forecast"), ("Daily monitoring", "alerts if profit share drops below 90% or errors rise")]):
    y = 360 - i * 74; text(560, y, h, 17, "B"); wrap(560, y - 22, b, 13, 340, "R", MUTED)

# 9 Risks
slide("Risks and controls", "We know where it can go wrong, and what we do about it.")
rows = [("Prices change behaviour (new regime, market coupling)", "Weekly refits, daily alerts, re-test when coupling goes live"),
        ("A forecast is badly wrong on the day", "Safety price limits on every order; bad days stay profitable"),
        ("Wear or fees higher than assumed", "Stress-tested: still ahead at wear ₹0–1,500/MWh, fees, 4-hour battery, 85% efficiency"),
        ("Thursday weak spot", f"Trails the simple rule by ₹{n(-SEG['Thu']['gain'])} a day on Thursdays; first fix in the roadmap")]
y = 372
for r, ctl in rows:
    y1 = wrap(56, y, r, 15, 380, "B"); y2 = wrap(470, y, ctl, 14, 430, "R", MUTED); yb = min(y1, y2) + 4
    c.setStrokeColor(LINE); c.line(56, yb, W - 56, yb); y = yb - 26

# 10 The ask
slide("The ask", "Approve a 30-day shadow run, then go live.")
phases = [("Weeks 1–4", "Shadow run", "Copilot plans every day alongside the current method; both scored at real prices"),
          ("Month 2", "Live with approval", "Trader approves each morning; safety limits on every order"),
          ("Month 3 on", "Scale", "Roll out across the fleet; monthly model review")]
for i, (when, what, body) in enumerate(phases):
    x = 56 + i * 292; c.setFillColor(INK if i == 0 else SOFT); c.setStrokeColor(INK if i == 0 else LINE); c.roundRect(x, 150, 270, 200, 12, fill=1, stroke=1)
    col = HexColor("#ffffff") if i == 0 else INK
    text(x + 22, 318, when, 13, "B", HexColor("#93c5fd") if i == 0 else BLUE); text(x + 22, 288, what, 22, "B", col)
    wrap(x + 22, 252, body, 14, 230, "R", HexColor("#cbd5e1") if i == 0 else MUTED)
wrap(56, 112, "We need: the IEX day-ahead price feed, one small server, and ten minutes of a trader's time each morning. All software is open source.", 16, 850, "R", MUTED)
c.save(); print("deck pages:", page[0])

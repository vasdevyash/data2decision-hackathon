"""M5 deck as PDF, matching web/present.html slide for slide (live demos shown as screenshots)."""
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
HN = "/System/Library/Fonts/HelveticaNeue.ttc"
pdfmetrics.registerFont(TTFont("R", HN, subfontIndex=0)); pdfmetrics.registerFont(TTFont("B", HN, subfontIndex=1))
out, F = sys.argv[1], sys.argv[3]
W, H = 960, 540; GREY, GREEN, BLUE, INK = HexColor("#9ca3af"), HexColor("#34d399"), HexColor("#60a5fa"), HexColor("#0b1220")
c = canvas.Canvas(out, pagesize=(W, H)); c.setTitle("Battery Copilot · Team D01")
first = [True]


def page(bg=black):
    if not first[0]: c.showPage()
    first[0] = False; c.setFillColor(bg); c.rect(0, 0, W, H, fill=1, stroke=0)


def wrap(x, y, parts, size, width, lead=1.12):
    # parts: list of (text, color); wraps word by word keeping colours
    words = [(w, col) for txt, col in parts for w in txt.split()]
    line, yy, lines = [], y, []
    for w, col in words:
        trial = " ".join(t for t, _ in line + [(w, col)])
        if pdfmetrics.stringWidth(trial, "B", size) > width and line: lines.append(line); line = [(w, col)]
        else: line.append((w, col))
    if line: lines.append(line)
    for ln in lines:
        xx = x
        for w, col in ln:
            c.setFont("B", size); c.setFillColor(col); c.drawString(xx, yy, w); xx += pdfmetrics.stringWidth(w + " ", "B", size)
        yy -= size * lead
    return yy


def statement(parts, sub=None):
    page(); n = 1 + sum(len(t) for t, _ in parts) // 34
    y = H / 2 + n * 24 + (20 if sub else 0)
    y = wrap(86, y, parts, 46, 790)
    if sub:
        c.setFont("R", 20); c.setFillColor(GREY); c.drawString(86, y - 18, sub)


def demo(img, caption):
    page(white); c.setFont("B", 16); c.setFillColor(HexColor("#2563eb")); c.drawString(48, H - 42, "Live demo")
    c.setFillColor(INK); c.setFont("R", 16); c.drawString(140, H - 42, "· " + caption)
    im = ImageReader(img); iw, ih = im.getSize(); w = W - 96; h = w * ih / iw
    if h > H - 90: h = H - 90; w = h * iw / ih
    c.drawImage(im, (W - w) / 2, 26, w, h); c.setStrokeColor(HexColor("#e5e7eb")); c.rect((W - w) / 2, 26, w, h)


wh = white
statement([("A battery makes money by buying power when it is cheap and selling it when it is dear.", wh)])
statement([("But every morning, the trader has to guess tomorrow.", wh)], "96 decisions for the next day, locked in before noon.")
statement([("Guessing by rule leaves", wh), ("₹1.8 crore", GREEN), ("a year on the table.", wh)], "For one 10 MW battery. That is today's practice.")
statement([("So we built a copilot that makes the plan for them.", wh)], "It predicts tomorrow's prices, finds the best time to buy and sell, and writes the orders.")
demo(f"{F}/m5_tomorrow.jpg", "Tomorrow's plan: one sentence, the profit, one click to send the orders.")
demo(f"{F}/m5_replay.jpg", "Watch it trade a real day, slot by slot, at real prices.")
page(); y = wrap(86, 380, [("Tested on a full year it had never seen.", wh)], 46, 790)
for i, (v, k, col) in enumerate([("₹4.5 cr", "profit a year", GREEN), ("95%", "of the best possible", wh), ("22 of 25", "months ahead of today's method", wh)]):
    x = 86 + i * 270; c.setFont("B", 52); c.setFillColor(col); c.drawString(x, y - 70, v); c.setFont("R", 16); c.setFillColor(GREY); c.drawString(x, y - 98, k)
statement([("It pays for the battery in under", wh), ("4 years.", GREEN)], "And the copilot is cheap to run: exchange prices and a laptop.")
demo(f"{F}/m5_business.jpg", "The business case: change the battery and the numbers update.")
statement([("The trader stays in control.", wh)], "Every plan is checked, approved with one click, and watched every day.")
statement([("Start with", wh), ("30 days,", BLUE), ("side by side.", wh)], "No risk. If it wins, go live.")
statement([("Thank you.", wh)], "Battery Copilot · Team D01 · Data2Decision 2026")
c.save(); print("ok")

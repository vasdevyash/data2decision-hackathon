import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer, KeepTogether

F = "/System/Library/Fonts/Supplemental/"
pdfmetrics.registerFont(TTFont("G", F + "Georgia.ttf"))
pdfmetrics.registerFont(TTFont("GB", F + "Georgia Bold.ttf"))
pdfmetrics.registerFont(TTFont("GI", F + "Georgia Italic.ttf"))
pdfmetrics.registerFontFamily("G", normal="G", bold="GB", italic="GI", boldItalic="GB")

out, fig1, fig2 = sys.argv[1:4]
B = ParagraphStyle("b", fontName="G", fontSize=9, leading=12, spaceAfter=3)
H = ParagraphStyle("h", fontName="GB", fontSize=10.5, leading=13, spaceBefore=7, spaceAfter=3, keepWithNext=1)
T = ParagraphStyle("t", fontName="GB", fontSize=13, leading=16, spaceAfter=2)
S = ParagraphStyle("s", fontName="G", fontSize=8.5, leading=11)
SB = ParagraphStyle("sb", parent=S, fontName="GB")
CAP = ParagraphStyle("cap", fontName="GI", fontSize=8, leading=10, spaceAfter=4)
BL = ParagraphStyle("bl", parent=B, leftIndent=9, bulletIndent=0, spaceAfter=1.5)
P = lambda s: Paragraph(s, B)
bul = lambda s: Paragraph(s, BL, bulletText="•")


def plain(rows, widths):
    data = [[Paragraph(c, SB if i == 0 else S) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
    return t


s = [Paragraph("M2 FIND · Data Note: Battery Dispatch Against Day-Ahead Prices", T),
     P("Team D01 · Energy &amp; Renewables · Data and code: github.com/vasdevyash/data2decision-hackathon")]

s.append(Paragraph("1. The problem we received, and how we sharpened it", H))
s.append(P("<b>Received:</b> help the trading head of a battery storage operator decide when to charge and discharge a 20 MWh battery each day "
           "in the electricity market, measured by net daily revenue, against a fixed schedule and a perfect-hindsight upper bound."))
s.append(P("<b>Refined:</b> help the trading and operations head of a standalone 10 MW / 20 MWh battery decide how much to charge, discharge "
           "or stay idle in each 15-minute block of tomorrow on the IEX Day-Ahead Market, measured by <b>daily trading profit</b>. "
           "The industry, the stakeholder and the decision are unchanged."))

s.append(Paragraph("2. What we changed and why", H))
s.append(plain([
    ["Change", "Why"],
    ["KPI: from net daily revenue to <b>daily trading profit</b> = sales − cost of the electricity bought to charge − battery wear",
     "Revenue ignores what charging costs. Profit is what the trading head is judged on."],
    ["New benchmark: a schedule optimised on <b>yesterday's prices</b>", "A one-line rule already earns 93–95% of the perfect-foresight profit, so it is the honest bar; the fixed rule earns only 70%"],
    ["Fixed rule made feasible: 18 MWh spread evenly over 11:00–15:00 and 18:00–22:00",
     "Four hours at 10 MW is 40 MWh, more than the 18 MWh the battery can use"],
    ["Battery starts and ends every day at 10% charge", "Otherwise a schedule could profit from energy it never bought"],
    ["Cycles counted as full cycles (18 MWh out); base case up to 2 a day (1.5 used on average), 1 as a test",
     "The second cycle adds about ₹19,000 a day after wear; most Indian battery capacity awarded in 2025 was 2-hour, 2-cycle"],
    ["Battery wear: ₹1,000 per MWh (canvas ₹500; range ₹0–1,500 kept)",
     "Benchmark cost ₹0.80 crore per MWh over about 6,000 cycles (our assumption) gives ₹740–1,480"],
    ["Data window: train Apr 2023–Nov 2025, test the most recent year (Nov 2025–Nov 2026)",
     "The price ceiling was ₹20,000 and ₹12,000 before 4 Apr 2023 and ₹10,000 since"],
    ["Forecast for a day uses only data known the day before", "That day's bid volumes appear only after prices are set"],
    ["Stakeholder narrowed to a standalone operator", "A solar owner charging from its own plant has a different cost"],
], [92, 86]))

s.append(Paragraph("3. The data", H))
s.append(P("<b>IEX Day-Ahead Market prices, 15-minute blocks</b>, published by the Indian Energy Exchange on its public market snapshot page. "
           "These are real auction results, downloaded on 22 Nov 2026 with a script in the repository so anyone can reproduce them. "
           "162,816 rows (1 Apr 2022 – 21 Nov 2026: 1,696 days × 96 blocks), 10 columns, 14.7 MB. One row is one 15-minute block of the all-India market. "
           "We model 127,776 rows from 1 Apr 2023."))
s.append(plain([
    ["Column", "What it holds", "How we use it"],
    ["mcp_rs_mwh", "Clearing price, ₹ per MWh", "Target: forecast it, then value every block at the actual price"],
    ["datetime, date, block (1–96), time_block", "When the 15-minute block starts: timestamp, day, block number, clock range", "Time and calendar features"],
    ["purchase_bid_mw, sell_bid_mw", "Total buy and sell bids, MW", "Features from earlier days only"],
    ["mcv_mw, final_scheduled_volume_mw", "Cleared and scheduled volume, MW", "Features from earlier days; checks the battery is too small to move prices"],
    ["congestion", "Whether regional congestion split the market", "Limitation flag"],
], [52, 56, 70]))

s.append(KeepTogether([Image(fig1, width=178 * mm, height=62 * mm),
                       Paragraph("Figure 1. Average price through the day, most recent year. It falls to about ₹1,570 at 1 pm (solar) and peaks near ₹8,000 at "
                                 "7 pm: the gap the battery earns from. Shaded: the canvas's fixed charging and discharging windows.", CAP)]))

s.append(Paragraph("4. Target and KPIs", H))
s.append(P("The target variable is tomorrow's price for each of the 96 blocks. The forecast feeds an optimiser that sets the charge and discharge "
           "quantities, and profit is then counted at the <i>actual</i> prices. We forecast prices rather than the schedule itself, because the optimiser "
           "guarantees every schedule respects the battery's power, capacity and charge-level limits; a model that predicts actions directly can produce "
           "schedules the battery cannot physically follow. The KPIs are all measures of profit:"))
s.append(bul("<b>Primary: daily trading profit (₹ per day)</b> = sales − cost of charging energy − ₹1,000 per MWh of wear. Fixed costs are left out "
             "because the schedule cannot change them."))
s.append(bul("<b>Profit added by forecasting</b> = profit of our schedule − profit of the yesterday's-prices schedule. This is the bar our model must clear."))
s.append(bul("<b>Share of the profit gap closed</b> between the yesterday's-prices schedule and perfect foresight, over the whole test year."))
s.append(bul("<b>Extra profit from the second cycle</b> = profit with 2 cycles − profit with 1, after wear. A second cycle pays only if this is positive "
             "(about ₹19,000 a day using yesterday's prices)."))
s.append(bul("<b>Worst 5% of days</b>, because a trader is judged on bad days too."))
s.append(KeepTogether([Image(fig2, width=178 * mm, height=54 * mm),
                       Paragraph("Figure 2. Average daily trading profit over the most recent year for each schedule (battery limits and wear identical). "
                                 "Perfect foresight cannot be traded; it only shows the ceiling. Using yesterday's prices with up to 2 cycles earns ₹121,401 a day, "
                                 "₹4.43 crore a year, after wear.", CAP)]))
s.append(P("So the prize for a better forecast is small: at most about ₹9,000 a day over yesterday's prices. The bigger lever is how much to cycle. "
           "Our refined question: <b>how much profit does a forecast-driven schedule add over yesterday's prices and over the fixed rule, and when does a "
           "second daily cycle earn more than its wear</b>, by season, weekday or weekend, and how wide the day's price spread is?"))

s.append(Paragraph("5. Data quality, limitations and preparation", H))
s.append(bul("<b>Complete:</b> every day has 96 blocks; no gaps, duplicates or blanks. A spot check against the IEX page matched."))
s.append(bul("<b>Price ceiling:</b> 18.8% of blocks since Apr 2023 clear at exactly ₹10,000 (14.8% of all rows), and about half of the blocks after 6 pm in the most recent year. "
             "The true peak value is hidden, so our profit is a floor. We add a ceiling flag and judge forecast error on the other blocks."))
s.append(bul("<b>The price level moves:</b> average ₹5,239 in FY24, ₹4,471 in FY25, ₹3,861 in FY26, ₹5,443 so far in FY27. We train from Apr 2023, refit as we go and add season features."))
s.append(bul("<b>Volume columns are slightly noisy</b> (32 blocks where cleared volume exceeds a bid side; grid cuts in scheduled volume). The price is unaffected."))
s.append(bul("<b>Very low prices are real:</b> 253 blocks at ₹100 or less, all between 8 am and 4 pm, when solar output is high. We keep them; they are the best blocks to charge in."))
s.append(bul("<b>Limits:</b> all-India price, not regional (congestion in 2% of blocks); the battery is 0.13% of typical traded volume (3% in the thinnest block); "
             "CERC has ordered market coupling, which may change how prices form; transmission charges and taxes are left out, as in the canvas."))
s.append(P("<b>Preparation:</b> reshape to one row per day with 96 prices; build features from earlier days (same block 1 and 7 days back, rolling averages, "
           "previous-day volumes) plus block, weekday, month and holidays; split by date; optimise each day as a linear program, already working in the repository. "
           "One source, so nothing to merge."))

s.append(Paragraph("6. Problem–data–KPI fit: proceed", H))
s.append(P("The data matches the decision exactly: the same market, the same 15-minute blocks, the day before delivery, from an official public source. "
           "Profit needs only the price per block plus the battery settings, and every benchmark above is already computed from this data."))
s.append(Paragraph("Sources: IEX Day-Ahead Market snapshot (iexindia.com/market-data/day-ahead-market/market-snapshot); CERC price-ceiling order (April 2023); CERC and APTEL on market coupling (2025–26); "
                   "IEEFA–JMK Research on 2025 battery awards; CTUIL benchmark battery cost (2025).", S))

SimpleDocTemplate(out, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=12 * mm, bottomMargin=11 * mm,
                  title="D01 M2 Data Note", author="Team D01", creator="Team D01", producer="Team D01").build(s)

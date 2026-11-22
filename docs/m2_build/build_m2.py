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

out, fig1, fig2 = sys.argv[1:4]
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

s = [Paragraph("M2 FIND · Data Note: Battery Dispatch Against Day-Ahead Prices", T),
     Paragraph(f"Team D01 · Energy &amp; Renewables · Data link: {a(REPO + '/blob/main/data/raw/iex_dam_15min.csv', 'dataset (CSV)')} · "
               f"Code: {a(REPO, 'github.com/vasdevyash/data2decision-hackathon')}", SUB),
     Spacer(1, 3),
     box("<b>Bottom line.</b> The data fits the problem exactly: 1,696 days of official IEX day-ahead prices in the same 15-minute blocks the trader bids. "
         "It also sharpens the question. A schedule optimised on <i>yesterday's</i> prices already earns 93–95% of the perfect-foresight profit (the canvas's "
         "fixed rule: 70%), so a better forecast can add at most ₹9k a day, while a second daily cycle adds ₹19k a day and pays for its wear up to "
         "roughly ₹3,000/MWh. <b>Fit: PROCEED.</b>")]

s.append(Paragraph("1. The problem we received, and how we refined it", H))
s.append(Paragraph("<b>Received (canvas, verbatim):</b> “We are helping the trading head of a grid-scale battery storage operator decide when to charge and "
                   "discharge a 20 MWh battery each day in the electricity market, measured by net daily revenue (₹), compared with a fixed-schedule "
                   "baseline and a perfect-hindsight upper bound.”", QUOTE))
s.append(P("<b>Refined:</b> We are helping the <b>trading and operations head of a standalone 10 MW / 20 MWh battery</b> decide <b>how much to charge, "
           "discharge or hold in each 15-minute block</b> of tomorrow's IEX Day-Ahead Market, measured by <b>daily trading profit</b> (₹/day after charging "
           "cost and battery wear). <b>Unchanged:</b> industry, stakeholder and core decision; every change below sharpens scope, makes the KPI measurable "
           "or updates an assumption."))
s.append(rule_table([
    ["Area", "Canvas", "Refined", "Why (evidence)"],
    ["Primary KPI", "Net daily revenue", "<b>Daily trading profit</b> = sales − charging cost − wear",
     "“Revenue” hides the cost of bought energy; profit is the P&amp;L line"],
    ["Supporting KPI", "Daily capture ratio vs hindsight", "Share of the beatable gap closed, summed over the year",
     "A daily ratio explodes on flat days; the gap above the bar is what a model can win"],
    ["Benchmarks", "(a) fixed rule, (b) forecast, (c) hindsight", "All kept; <b>added a schedule optimised on yesterday's prices</b> as the bar",
     "It earns 93–95% of hindsight vs 70% for the fixed rule (Fig. 2)"],
    ["Feasibility", "Fixed rule 4 h at 10 MW; charge 10–100%", "Rule stores 18 MWh, spread evenly; every day starts and ends at 10%", "40 MWh exceeds the 18 MWh usable; no selling energy never bought"],
    ["Cycles", "“At most 1–2 full cycles”", "1 cycle = 18 MWh drawn from the battery; base up to 2 a day (1.5 used on average), 1 as a test",
     "The 2nd cycle is worth more than forecasting (Table 1); most 2025 Indian awards were 2-hour, 2-cycle"],
    ["Wear cost", "₹500/MWh (range 0–1,500)", "₹1,000 per MWh sold; range kept", "₹0.80 crore/MWh capex over ~6,000 cycles (assumed) gives ₹740–1,480"],
    ["Scope", "Operator (or solar owner)", "Standalone operator", "A solar owner charging from its own plant has a different cost of energy"],
    ["Data window", "From Apr 2022", "From Apr 2023; train to Nov 2024, validate to Nov 2025, test last year once",
     "One price-cap regime (₹10,000); no tuning on the test year"],
    ["Information", "Not stated", "Forecast for day D uses data up to D−1 only", "D's bid volumes are published with its prices: using them leaks the answer"],
], [21, 37, 55, 67]))

s.append(Paragraph("2. The dataset", H))
s.append(P("<b>IEX Day-Ahead Market clearing prices and volumes, 15-minute blocks.</b> <b>Source:</b> Indian Energy Exchange public " + a("https://www.iexindia.com/market-data/day-ahead-market/market-snapshot", "market snapshot") +
           " (official auction results). <b>Provenance:</b> downloaded with <i>src/download_iex_dam.py</i> on 22 Nov 2026; re-runnable for any window. "
           "<b>Size and structure:</b> 162,816 rows × 10 columns, 14.7 MB CSV; one row per block, 1 Apr 2022 – 21 Nov 2026 (1,696 days × 96 blocks, IST). "
           "We model the 127,776 rows from 1 Apr 2023; a public holiday list (joined on date) is added at M3."))
s.append(rule_table([
    ["Column", "What it holds", "How we use it"],
    ["<b>mcp_rs_mwh</b>", "Market clearing price, ₹/MWh", "<b>Target</b>: forecast it; settle every schedule at the actual value"],
    ["datetime, date, block (1–96), time_block", "Start of the 15-minute block", "Calendar and time-of-day features"],
    ["purchase_bid_mw, sell_bid_mw", "Total buy and sell bids, MW", "Lagged features only (D−1 and earlier)"],
    ["mcv_mw, final_scheduled_volume_mw", "Cleared and scheduled volume, MW", "Lagged features; proves the battery cannot move the price"],
    ["congestion", "YES if regional congestion split the market", "Limitation flag"],
], [58, 52, 70]))
s.append(KeepTogether([Image(fig1, width=160 * mm, height=46 * mm),
                       Paragraph("Figure 1. Price through the day, test year (22 Nov 2025 – 21 Nov 2026). The mean falls to ₹1,570 at 1 pm (solar) and peaks near "
                                 "₹8,000 at 7 pm. The upper edge of the middle 50% of days sits at the ₹10,000 ceiling all evening and night, so peak prices are often "
                                 "capped. Shaded: the canvas's fixed windows.", CAP)]))

s.append(Paragraph("3. Target variable and KPIs", H))
s.append(P("<b>Target:</b> tomorrow's price in each of the 96 blocks. The forecast feeds a linear-programming optimiser that sets the charge and discharge "
           "quantities, and the schedule is then settled at <i>actual</i> prices. We forecast prices rather than actions because the optimiser guarantees "
           "every schedule respects the battery's power, energy and charge-level limits; predicting actions directly does not."))
s.append(bul("<b>Primary: daily trading profit (₹/day)</b> = Σ price × MWh sold − Σ price × MWh bought − ₹1,000 × MWh sold. Fixed costs are excluded: the schedule cannot change them."))
s.append(bul("<b>Profit added by forecasting</b> = our schedule − the yesterday's-prices schedule. <b>Share of the beatable gap closed</b> = Σ(ours − bar) ÷ Σ(perfect − bar) over the test year."))
s.append(bul("<b>Second-cycle value</b> = profit with up to 2 cycles − profit with 1, after wear. <b>Downside:</b> worst 5% of days and worst month."))
s.append(bul("<b>Diagnostic only:</b> forecast error on blocks below the cap. Price error is not profit."))
s.append(KeepTogether([Image(fig2, width=160 * mm, height=40 * mm),
                       Paragraph("Figure 2. Average daily trading profit, test year; identical battery limits and wear for every schedule. Perfect foresight cannot be "
                                 "traded: it is only the ceiling. Yesterday's prices with up to 2 cycles earn ₹121,401 a day (₹4.43 crore a year) after wear.", CAP)]))

seg = rule_table([
    ["Segment", "Fixed rule", "Yesterday's prices"],
    ["Oct–Feb", "54%", "94%"], ["Mar–Jun", "75%", "95%"], ["Jul–Sep", "84%", "96%"],
    ["Weekday / weekend", "70% / 68%", "97% / 90%"], ["Lowest-spread third of days", "56%", "94%"],
], [44, 20, 26], right=(1, 2))
wear = rule_table([
    ["Wear cost, ₹/MWh", "2nd cycle adds, ₹/day"],
    ["0", "28,975"], ["500", "24,150"], ["1,000 (base)", "19,291"], ["1,500", "14,575"], ["Break-even (extrapolated)", "≈ 3,000"],
], [40, 34], right=(1,))
both = Table([[seg, wear]], colWidths=[100 * mm, 80 * mm])
both.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
s.append(KeepTogether([Paragraph("Table 1. Left: share of perfect-foresight profit captured (1 cycle, ₹1,000 wear). Right: value of the 2nd cycle (yesterday's-prices schedule). Test year.", CAP), both]))
s.append(P("The fixed rule fails exactly where the canvas asks us to look (winter and low-spread days), while yesterday's prices hold up everywhere except weekends, "
           "the gap a forecast with calendar features can close. <b>Refined question:</b> <b>how much profit does a forecast-driven schedule add over yesterday's "
           "prices (and over the fixed rule), and when does a second daily cycle earn more than its wear</b>, by season, weekday or weekend, and daily price spread?"))

s.append(Paragraph("4. Data quality, limitations and preparation", H))
s.append(bul("<b>Complete:</b> 96 blocks every day; no gaps, duplicates or blanks; a spot check against the IEX page matched."))
s.append(bul("<b>Price ceiling:</b> ₹20,000 in Apr 2022, ₹12,000 to Mar 2023, ₹10,000 since 4 Apr 2023 (confirmed in the data). 18.8% of blocks since Apr 2023 "
             "clear at exactly ₹10,000 (14.8% of all rows), and 52% of 6 pm–midnight blocks in the test year. We still earn the actual settled price, "
             "but the ceiling hides how scarce power was above it, and capped blocks tie: the forecast's edge is in picking charging blocks. We add a cap flag and score forecast error on uncapped blocks."))
s.append(bul("<b>Level shifts:</b> mean price ₹5,239 in FY24, ₹4,471 in FY25, ₹3,861 in FY26, ₹5,443 in FY27 to date. We refit on a rolling basis and report results by season."))
s.append(bul("<b>Noise and outliers:</b> 32 blocks where cleared volume exceeds a bid side (volumes used only as lagged features). 253 blocks at ₹100 or less since Apr 2023, all "
             "8 am–4 pm (solar): real, kept, the best charging blocks. Minimum ₹20.8, never negative, so charging and discharging at once never pays and the model stays linear."))
s.append(bul("<b>Limits:</b> all-India price, not regional (congestion in 2.5% of blocks since Apr 2023); the battery is 0.13% of median cleared volume (3% in the thinnest block), so it "
             "is a price-taker; CERC-ordered market coupling may change how prices form; exchange fees (≈ ₹1k/day), transmission and taxes excluded, as in the canvas."))
s.append(P("<b>Preparation:</b> reshape to one row per day × 96 prices; lagged features (same block D−1 and D−7, rolling means, D−1 volumes) plus block, weekday, "
           "month and holiday; time-ordered train, validation and test sets; one linear program per day (<i>src/dispatch_lp.py</i>, already working)."))

s.append(Paragraph("5. Problem–data–KPI fit: PROCEED", H))
s.append(P("<b>Problem and data:</b> the same market, the same 15-minute blocks and the same day-ahead timing, from the official source. <b>Data and KPI:</b> profit "
           "needs only block prices and the battery settings, and every benchmark above is already computed from this data. <b>What would change our view:</b> "
           "if no model beats yesterday's prices by more than exchange fees, the recommendation becomes “bid on yesterday's prices and run two cycles”, which our KPIs still measure."))
s.append(Paragraph(
    "Sources: " + a("https://www.iexindia.com/market-data/day-ahead-market/market-snapshot", "IEX DAM market snapshot") + "; " +
    a("https://indianinfrastructure.com/2023/04/28/cerc-reduces-ceiling-price-for-power-trading/", "CERC price ceiling (Apr 2023)") + "; " +
    a("https://powerline.net.in/2026/04/21/cerc-issues-draft-cerc-power-market-second-amendment-regulations-2026/", "CERC market coupling draft (Apr 2026)") + "; " +
    a("https://www.pv-magazine-india.com/?p=15030", "IEEFA–JMK on 2025 storage awards") + "; " +
    a("https://www.energy-storage.news/?p=93699", "CTUIL benchmark cost") + ". "
    "AI use: generative AI assisted with code and drafting; every number here was recomputed from the data with the scripts in the repository.", S))

SimpleDocTemplate(out, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=11 * mm, bottomMargin=10 * mm,
                  title="D01 M2 Data Note", author="Team D01", creator="Team D01", producer="Team D01").build(s)

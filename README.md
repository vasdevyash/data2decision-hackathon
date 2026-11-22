# Data2Decision Hackathon

Team workspace for the Data2Decision Hackathon (November 2026).

## Where we are

| Phase | Status |
|---|---|
| M1 – Decide (problem canvas) | Done |
| M2 | **In progress**: problem statement received |

## Rules and deadlines

Full rules (photos of the printed instructions): [`docs/Hackathon_Rules.pdf`](docs/Hackathon_Rules.pdf)

| Milestone | Deadline | Marks | Deliverable |
|---|---|---|---|
| M2 – FIND | 11:15 AM | 10 | Data Note (max 2-page PDF) + dataset or data link |
| M3 – UNDERSTAND | 1:00 PM | 15 | Exploratory analysis (max 3-page PDF) + notebook/code |
| M4 – BUILD | 2:45 PM | 20 | Working solution + validation (max 3-page PDF) + notebook/code |
| M5 – ACT | 3:45 PM | 10 | Decision brief (max 2-page PDF) + final presentation/demo, AI use record, signed declaration |

- File names: Team ID + milestone, e.g. `D01_M2.pdf`.
- We may refine the received problem but not replace it: no change to industry, stakeholder or core decision. Log every refinement in the M2 Data Note.
- Everything is frozen at 3:45 PM. Shortlisted teams present 4:00–6:00 PM, so keep the deck and demo ready.
- Disclose significant AI use and be ready to explain every result; cite reused code and data.

## Problem statement (M2)

**Battery Dispatch Against Day-Ahead Prices** (Energy & Renewables). Full canvas:
[`docs/M2_Problem_Statement_Battery_Dispatch.pdf`](docs/M2_Problem_Statement_Battery_Dispatch.pdf)

- **User:** trading head of a grid-scale battery operator who submits tomorrow's schedule to the power exchange.
- **Decision:** for each 15-minute block of the next day, charge, discharge or idle, and how much.
- **Primary KPI:** net daily revenue (₹/day) after efficiency losses and degradation cost.
  Supporting: capture ratio = revenue ÷ perfect-hindsight revenue for the same day.
- **Question:** how much more does a forecast-driven schedule earn than a fixed daily rule, and in which
  conditions (season, weekday, volatility) does the edge shrink or vanish?
- **Battery (assumed):** 10 MW / 20 MWh (2 h), 88% round-trip efficiency, 1–2 full cycles/day,
  state of charge 10–100%, price-taker.
- **Degradation cost:** ₹500 per MWh discharged; sensitivity ₹0–₹1,500.
- **Benchmarks:** (a) fixed rule: charge 11:00–15:00, discharge 18:00–22:00; (b) forecast-based; (c) perfect hindsight.
- **Data:** IEX day-ahead market clearing price (₹/MWh), 15-minute blocks, from April 2022. If unusable,
  another public day-ahead series with the same logic; record it in the M2 Data Note.
- **Out of scope:** transmission charges, taxes, other market segments.

## Repo layout

```
data/raw/          original datasets (NOT committed: see below)
data/processed/    cleaned / feature-engineered data (NOT committed)
notebooks/         exploration and modelling notebooks, prefix with your initials (e.g. yv_01_eda.ipynb)
src/               reusable Python code (cleaning, features, model, evaluation)
outputs/figures/   charts for the deck
docs/              problem statement, canvas, slides, notes
```

## Data

**`data/raw/iex_dam_15min.csv`**: IEX Day-Ahead Market clearing prices, 15-minute blocks,
1 Apr 2022 to 21 Nov 2026 (162,816 rows = 1,696 days × 96 blocks, no gaps or duplicates).
Source: [IEX market snapshot](https://www.iexindia.com/market-data/day-ahead-market/market-snapshot).
Refresh or change the window with `python src/download_iex_dam.py [YYYY-MM-DD] [YYYY-MM-DD]`.

| Column | Meaning |
|---|---|
| `datetime`, `date`, `block` (1–96), `time_block` | when the 15-minute block starts |
| `purchase_bid_mw`, `sell_bid_mw` | total buy and sell bids |
| `mcv_mw`, `final_scheduled_volume_mw` | cleared and scheduled volume |
| `mcp_rs_mwh` | **market clearing price, ₹/MWh: the target** |
| `congestion` | YES when regional congestion split the market (~2% of blocks) |

Watch out: prices hit regulatory caps (₹20,000 early in 2022, ₹10,000 later; ~19% of blocks since Apr 2023 (15% of all rows) sit
at ₹10,000), so the price distribution is clipped at the top.

Other datasets stay local in `data/raw/` and are not pushed.

## Getting started

```bash
git clone https://github.com/vasdevyash/data2decision-hackathon.git
cd data2decision-hackathon
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Working together

1. `git pull` before you start.
2. Work in your own notebook; don't edit someone else's without telling them.
3. Commit small and often with a clear message, then `git push`.
4. Clear notebook outputs that contain large tables before committing.

## Team

| Name | Role |
|---|---|
| Yash Vasdev | |
| | |
| | |

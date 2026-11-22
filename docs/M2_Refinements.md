# M2 refinements to the received canvas: Battery Dispatch (Energy & Renewables)

**Allowed by the rules:** sharpen the scope, make the KPI measurable, update assumptions, reframe the
analytical question. **Unchanged:** industry (Energy), stakeholder (battery trading and operations head),
core decision (charge, discharge or idle, and how much, per 15-minute block of the next day).

Evidence: `data/raw/iex_dam_15min.csv` and a day-by-day linear-programming dispatch model
(`src/dispatch_lp.py`). Test year = 22 Nov 2025 – 21 Nov 2026, degradation cost ₹1,000/MWh unless stated.

---

## 1. Refined problem statement

> We are helping the **trading and operations head of a standalone grid-scale battery operator** decide the
> **charge, discharge or idle quantity for each 15-minute block of the next day** in the IEX Day-Ahead Market,
> for a 10 MW / 20 MWh battery, measured by **Net Dispatch Value (₹/day)**. That is the money from selling
> energy, minus the cost of buying the charging energy, minus battery wear. All strategies face the same
> physical limits and start and end each day at the same state of charge.

## 2. What the data says (this drives every refinement)

| Strategy (test year, ₹1,000/MWh wear) | Net Dispatch Value ₹/day | ₹ crore/yr | Worst day (5th pct) | Worst month avg |
|---|---|---|---|---|
| Fixed rule, made feasible (1 cycle) | 75,091 | 2.74 | 12,981 | 27,575 |
| **Naive: tomorrow = today's prices**, optimised, 1 cycle | 102,110 | 3.73 | 36,110 | 71,968 |
| Naive, 2 cycles | 121,401 | 4.43 | 39,371 | 82,854 |
| Perfect information, 1 cycle | 107,757 | 3.93 | 39,326 | 76,570 |
| Perfect information, 2 cycles | 130,354 | 4.76 | 45,078 | 93,216 |

Three findings the canvas misses:

1. **The fixed rule is a straw man.** A naive "yesterday's prices" schedule already captures **95%** (1 cycle) or
   **93%** (2 cycles) of perfect-information value. The fixed rule captures 70%. Today's price for a block has a
   0.89 correlation with the same block yesterday.
2. **Forecasting can add at most ₹5.6k/day (1 cycle) or ₹9.0k/day (2 cycles) over naive.** That is the real prize
   for any ML model. Beating the fixed rule proves nothing.
3. **The second cycle is worth more than forecasting.** Going from 1 to 2 cycles adds about ₹19k/day under the
   naive schedule, even after ₹1,000/MWh of wear. So "how much to cycle" is part of the core decision, not a
   footnote.

## 3. KPIs: replaced and sharpened

The canvas says "net daily revenue" and gives a daily capture ratio. Both are vague: does "revenue" subtract
the cost of buying charging energy? And a daily ratio blows up on flat days. The reviewer's suggested set
(uplift vs fixed, capture vs fixed, MAE, cycles) anchors on the fixed rule, which the data shows is a straw man.
That set would report about a +60% "uplift" that a one-line naive rule also achieves. **Final set:**

| Role | KPI | Definition | Why this one |
|---|---|---|---|
| **Primary** | **Net Dispatch Value (NDV), ₹/day** | Σₜ Pₜ·Dₜ − Pₜ·Cₜ − c_deg·Dₜ over 96 blocks. Cₜ and Dₜ are grid-side MWh; efficiency is handled in the state-of-charge equation; SoC₉₆ = SoC₀. Settled at **actual** prices on the test year. Also reported as ₹ crore/yr. | It is the trading head's P&L line. "Revenue" wrongly implies charging is free. |
| Supporting | **Value of forecasting, ₹/day** | NDV(forecast) − NDV(naive yesterday-price schedule) | The honest bar any model must clear |
| Supporting | **Headroom captured, %** | Σ[NDV(forecast) − NDV(naive)] ÷ Σ[NDV(perfect) − NDV(naive)], summed over the test period | Shows how much of the beatable gap is closed. Summed totals avoid daily blow-ups. |
| Supporting | **Downside: 5th-percentile day and worst-month NDV** | Distribution of daily NDV | A trader is judged on bad days, not on the average |
| Supporting | **NDV per equivalent full cycle (₹/EFC)** | NDV ÷ (MWh discharged from the battery ÷ 18 MWh) | Tests whether the extra cycling pays for its wear |
| Diagnostic | Forecast MAE, **excluding ₹10,000-cap blocks**; hit rate on the cheapest 8 blocks | — | Price error is not profit. Capped blocks distort MAE. |

**Dropped:** "net daily revenue" (ambiguous), the daily capture ratio (unstable), and uplift vs the fixed rule
as a headline (inflated). The fixed rule stays only as a reference line.

## 4. Benchmarks: three roles, kept apart

| Role | Strategy | Can a trader use it? |
|---|---|---|
| Reference | Fixed rule: charge 11:00–15:00, discharge 18:00–22:00, 18 MWh spread evenly (the canvas's rule, made feasible) | Yes |
| **Operational benchmark (new)** | Optimise on yesterday's prices; also on the same day last week | Yes |
| Proposed | Optimise on an ML price forecast | Yes |
| Theoretical upper bound | Optimise on the actual prices | **No.** It only measures the size of the gap. |

## 5. Assumptions: updated, with sources

| Area | Canvas | Refined | Basis |
|---|---|---|---|
| Fixed rule | 4 h at 10 MW (40 MWh): infeasible | 18 MWh spread evenly over each window | 20 MWh × (100% − 10%) usable |
| State of charge | 10–100% | 2 ≤ SoC ≤ 20 MWh; **SoC₀ = SoC₉₆ = 2 MWh** (10%) | No borrowing energy from a previous day |
| Cycles | "1–2 a day" (ambiguous) | Defined as **equivalent full cycles = MWh discharged from the battery ÷ 18**. **Base case 2 EFC/day**, 1 EFC as sensitivity | Most Indian standalone battery capacity awarded in 2025 was 2-hour, 2-cycle (IEEFA–JMK) |
| Efficiency | 88% round trip | η_c = η_d = √0.88 ≈ 93.8% | Symmetric split |
| Degradation | ₹500/MWh (range 0–1,500) | **Base ₹1,000/MWh**, range 0–1,500 kept | CTUIL benchmark capex ₹0.80 crore/MWh. Assuming about 6,000 LFP cycles (typical spec, *assumption*), full-capex wear ≈ ₹1,480/MWh and cells-only ≈ ₹740/MWh. ₹500 is at the low end. |
| Charge and discharge at once | Not stated | Not needed as a separate constraint: with all prices > 0 (min ₹20.8) and losses, the optimiser never does both, so the model stays a linear program | Data check |
| Information set | Not stated | Forecast for day D uses only data up to D-1 (DAM bidding closes about 10:00–12:00 on D-1). **D's bid volumes are not allowed as features.** | Bid volumes are published when D clears, so using them would leak the answer |
| Price regime | Apr 2022 onward | **Train from 1 Apr 2023**: ₹10,000 cap since 4 Apr 2023; ₹20,000 and ₹12,000 caps before that | CERC order, Apr 2023; data shows nothing above ₹10,000 after 29 Mar 2023 |
| Cap clipping | Not mentioned | 50–59% of 18:00–24:00 blocks clear at exactly ₹10,000 in the test year. Peak value is understated, so the forecast's edge is in choosing charging blocks | Data |
| Price-taker | Assumed | Holds: 10 MW vs median 7,498 MW cleared (0.13%). Thinnest block 331 MW (3%), flagged | Data |
| Fees | Excluded | Excluded in base. Sensitivity: IEX fee of up to 2 paise/kWh per side (≈ ₹20/MWh, about ₹1k/day at 2 cycles) | CERC fee cap |
| Transmission | Excluded | Excluded. ISTS waiver for storage extended to June 2028, but it is conditional (co-located and commissioned by then), so a standalone unit may not qualify. State it. | MoP, June 2025 |
| Market structure | Not mentioned | **Regime risk:** CERC ordered DAM market coupling. Draft regulations Apr 2026, go-live not confirmed. Coupled prices may behave differently from the history. | CERC / APTEL Feb 2026 |
| Stakeholder | "Operator (or a solar owner)" | Standalone operator only. A co-located solar owner charges from its own plant, which is a different cost of charging. | Scope sharpening |

## 6. Refined analytical question

> Over a held-out year, how much Net Dispatch Value does a forecast-driven schedule add over a
> **naive yesterday-price schedule** (and over the fixed rule), how close does it get to perfect information,
> and **when does a second daily cycle earn more than its wear**, by season (Mar–Jun, Jul–Sep, Oct–Feb),
> weekday vs weekend, and tercile of daily price spread?

Segment evidence so far (₹500 wear, 1 cycle): the fixed rule's capture falls to **58% in Oct–Feb** and **60% on
low-spread days**, while the naive schedule holds 94–97% in every segment except weekends (90%).
The fixed rule fails exactly where the canvas asks us to look.

## 7. Reviewer points: accepted or rejected

| Point | Verdict |
|---|---|
| Rename the KPI and subtract charging cost | **Accepted** (NDV) |
| Fixed rule infeasible; same limits for all strategies | **Accepted** |
| Terminal state of charge | **Accepted** (SoC₀ = SoC₉₆ = 10%) |
| Define cycles as equivalent full cycles | **Accepted.** Base case moved to 2. |
| Perfect information = theoretical bound only | **Accepted** |
| Uplift and capture measured **vs the fixed rule** | **Rejected.** Measure against naive instead (§2). |
| Binary constraint against simultaneous charge and discharge | **Not needed:** prices stay positive, so a linear program is enough |
| Verify 96 blocks, gaps, bulk download | **Done:** 1,696 days × 96 blocks, no gaps or duplicates, bulk script in `src/` |

## Sources

- CERC ceiling cut to ₹10/kWh from 4 Apr 2023: https://indianinfrastructure.com/2023/04/28/cerc-reduces-ceiling-price-for-power-trading/
- Market coupling, draft regulations Apr 2026: https://powerline.net.in/2026/04/21/cerc-issues-draft-cerc-power-market-second-amendment-regulations-2026/
- APTEL on coupling, Feb 2026: https://solarquarter.com/2026/02/16/aptel-disposes-iex-appeal-allows-cerc-to-proceed-on-market-coupling-framework/
- 2-hour, 2-cycle share of 2025 awards: https://www.pv-magazine-india.com/?p=15030
- CTUIL benchmark ₹0.80 crore/MWh: https://www.energy-storage.news/?p=93699
- ISTS waiver to June 2028: https://jmkresearch.com/inter-state-transmission-waiver-for-energy-storage-projects-extended-by-three-years/
- Exchange fee cap 2 paise/kWh: https://www.businesstoday.in/latest/policy/story/power-trading-overhaul-cerc-eyes-fee-rationalisation-as-market-coupling-nears-2026-rollout-508383-2025-12-28

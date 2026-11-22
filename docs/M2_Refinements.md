# M2 refinements to the received canvas (Battery Dispatch, Energy)

Rules allow sharpening scope, making the KPI measurable, updating assumptions and reframing the
analytical question. Industry, stakeholder and core decision stay unchanged.
Evidence below comes from `data/raw/iex_dam_15min.csv`. "Last 12 months" means 22 Nov 2025 – 21 Nov 2026.

## Must fix: the problem can't be solved or scored as written

| # | Gap in the canvas | Evidence | Refinement |
|---|---|---|---|
| 1 | **Fixed-rule benchmark can't physically happen.** Charging at full 10 MW from 11:00 to 15:00 is 40 MWh, but the battery holds only 18 MWh usable (10–100% of 20 MWh). | Arithmetic | Fixed rule = charge 18 MWh spread evenly over 11:00–15:00 and discharge it evenly over 18:00–22:00. All three strategies use the same battery limits. |
| 2 | **Day-end state of charge is not stated.** Without it, an optimiser can empty the battery on the last block of the day and look richer than it is. | Modelling gap | Each day starts and ends at 10% state of charge (SoC). Days are independent. |
| 3 | **"1–2 cycles/day" is ambiguous.** | — | Base case is at most 1 full cycle a day (18 MWh discharged). 2 cycles is a sensitivity case. |
| 4 | **Forecast information cut-off isn't stated: leakage risk.** The bid volumes for day D only appear when D clears, so they can't be used to forecast D. | Market timing | To forecast day D, use only prices and volumes up to and including day D-1, plus calendar features. |
| 5 | **Capture ratio breaks on a single day.** When hindsight revenue is near zero, the ratio blows up. | — | Capture ratio = total strategy revenue ÷ total hindsight revenue over the test period. Daily ratios are reported only as a distribution. |
| 6 | **No train/test split, so "net daily revenue" can't be measured honestly.** | — | Train on 1 Apr 2023 – 21 Nov 2025. Test on the last 12 months (all seasons). KPI = realised net ₹/day on the test period when the schedule is built from the forecast and settled at actual prices. |

## Should fix: the conclusion could mislead

| # | Gap | Evidence | Refinement |
|---|---|---|---|
| 7 | **The price cap changed during the data window.** | Max MCP ₹20,000 (2022) and ₹12,000 (early 2023). Nothing above ₹10,000 after 29 Mar 2023. | Use data from 1 Apr 2023 onward, when the cap was a constant ₹10,000. |
| 8 | **The cap clips the evening peak.** | Last 12 months: 50–59% of blocks between 18:00 and 23:59 clear at exactly ₹10,000, and 41% at midnight. | Revenue is a lower bound because prices are capped. The forecast's edge is mainly in picking the cheapest charging blocks and the off-cap shoulder hours, since the peak price is often a flat ₹10,000. State this. |
| 9 | **Fixed rule is a weak benchmark, and the canvas lacks the honest one.** | Price vs the same block yesterday: correlation 0.89. | Add **(b0) naive forecast**: tomorrow = today's prices, optimised the same way. The ML forecast has to beat b0, not just the fixed rule. |
| 10 | **Fixed discharge window misses part of the peak.** | 51% of 23:00 blocks and 41% of 00:00 blocks are at the cap, outside 18:00–22:00. | Keep the canvas's rule as a benchmark, but report how much the late-night peak costs it. |
| 11 | **"Price conditions" in the question isn't measurable.** | — | Segment test-period results by season (Mar–Jun, Jul–Sep monsoon, Oct–Feb), weekday vs weekend, and tercile of daily price spread (max–min). |

## Assumptions that hold (state them, don't change them)

- **Price-taker:** 10 MW against cleared volume with median 7,498 MW (0.13%). Minimum is 331 MW (3%) in the thinnest block, so flag it.
- **Arbitrage exists:** over the last 12 months the median daily max–min spread is ₹8,335/MWh. A feasible fixed rule nets about ₹78k/day on average with no losing day. A rough 1-cycle hindsight bound is about ₹109k/day, so a forecast can add at most about ₹31k/day.
- **Congestion:** 2% of blocks. Use the all-India MCP and state it as a limitation (as the canvas says).

## Scope sharpening

- Stakeholder: the standalone battery storage operator. A solar owner with a co-located battery would charge from its own solar output, which changes the cost of charging and is a different model.
- Exchange fees and transmission charges stay excluded (as the canvas says). Add an IEX transaction fee as a sensitivity case.
- Round-trip efficiency of 88% is split evenly as about 93.8% when charging and about 93.8% when discharging.

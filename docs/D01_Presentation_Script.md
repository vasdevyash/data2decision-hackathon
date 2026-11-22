# Battery Copilot · Team D01 · Presentation script

Deck: `present.html` (arrow keys to move, F for full screen). About 6 minutes. Live slides: 6, 7, 10.
Speak slowly; the slide carries the numbers, you carry the story.

| Speaker | Slides | Part |
|---|---|---|
| Yash Vasdev | 1–2 | Hook, the business |
| Kartikeya Singh | 3–4 | The problem |
| Arnav Patil | 5 | Our solution |
| Aryan Shankhapal | 6–7 | Live demo |
| Mohd. Suhaib Ansari | 8–10 | Impact and business case |
| Ashwin Vaishampayan | 11–14 | Safety, limits, the ask, close |

---

## Yash · slides 1–2 (45 s)

**1 · Hook.** "Good afternoon. What if your battery could earn ₹1.8 crore more every year, without changing a single wire? That is what our project found, and we will show it to you live."

**2 · The business.** "A grid battery is a shop. It buys electricity when it is cheap, around noon when solar floods the grid, and sells it in the evening when everyone comes home. In India the noon price is often below ₹2,000 a megawatt-hour and the evening price close to ₹8,000. That gap is the profit."

## Kartikeya · slides 3–4 (45 s)

**3 · The catch.** "The catch is timing. Batteries trade on the IEX Day-Ahead Market. Every morning, before noon, the trader must lock in tomorrow's plan: 96 fifteen-minute slots, buy, sell or wait, without knowing tomorrow's prices. Ninety-six decisions a day, real money on every one."

**4 · Today's practice.** "Most plans today follow a fixed rule, like 'charge at midday, sell in the evening'. We tested exactly that rule on a full year of real IEX prices. It leaves about ₹1.8 crore a year on the table, for one 10 megawatt battery."

## Arnav · slide 5 (30 s)

**5 · Solution.** "So we built a copilot that makes the plan for the trader. It does three things. It predicts all 96 of tomorrow's prices using two models, a standard research model and an AI forecasting model. It works out the most profitable time to buy and sell within the battery's limits. And it writes the orders, ready to submit. Aryan will show it live."

## Aryan · slides 6–7 · LIVE (90 s)

**6 · Tomorrow's plan.** *(Point at the headline.)* "This is what the trader sees each morning: one sentence. Buy at 2:30 and 11:30, sell at 6:15 and 5:15 pm. Expected profit about ₹1.25 lakh. Below it, automatic checks: power limit, battery back to 10 percent, wear within two cycles. One click approves, one click downloads the 30 orders for the exchange."

**7 · A real day.** *(Press Play.)* "Here it trades a real winter day, slot by slot, at the real prices. Watch it buy overnight and at noon when power is cheap, and sell into both the morning and the evening peak. The money ticks up as it goes, and the battery ends the day back at 10 percent, ready for tomorrow."

## Suhaib · slides 8–10 (75 s)

**8 · Results.** "We tested it on a full year it had never seen. It earns ₹4.5 crore a year, 95 percent of the most anyone could earn even with perfect knowledge of prices. It beat the simple 'copy yesterday' method in 22 of 25 months, and the gain held on two separate years."

**9 · Payback.** "At the benchmark battery cost of ₹0.80 crore per megawatt-hour, that pays for the battery in under four years. And the copilot is cheap to run: it only needs exchange prices and a laptop."

**10 · Business case, LIVE.** *(Click Battery settings, pick the 4-hour battery.)* "If the client has a different battery, they change it here and every number updates: profit, payback, project value. This is the tool a CFO would use to decide."

## Ashwin · slides 11–14 (60 s)

**11 · Safe.** "The trader stays in control. Every plan is checked before it goes out, approved with one click, and monitored every day. If performance drops below 90 percent of the best possible, it raises an alert."

**12 · Limits.** "We want to be clear about what it cannot do yet. We tested one year of prices. Thursdays are its weakest day. Taxes and grid fees are left out, as the brief asked. And we will keep testing as the market changes."

**13 · The ask.** "So our ask is simple. Run it for 30 days, side by side with your current method. No risk. If it wins, go live."

**14 · Close.** "Thank you. We are Team D01, and we are happy to take your questions."

---

## Q&A: who answers what

| Likely question | Answer (short) | Who |
|---|---|---|
| How does the IEX auction work? | Open the demo's **6 · IEX** tab. Bids 10–12, price per slot at about 1 pm, binding next day; we are 0.1% of volume, so we take the price. | Yash |
| Which models? Why two? | LEAR, one LASSO regression per slot, the research benchmark; Chronos, Amazon's pre-trained AI model, used without training on Indian data. Blend 40/60, chosen on the validation year by money earned. They make different mistakes. | Aryan |
| Did the model see the future? | No. Forecasts use only prices known the day before; the blend weight was frozen before the test year; the test year was used once. | Aryan |
| How much does the model add over a simple rule? | ₹2,597 a day, about ₹9.5 lakh a year, over copying yesterday. Small per battery, consistent, statistically very unlikely to be luck, and it scales with every battery. The big jump, ₹1.8 crore, is over the fixed timetable. | Suhaib |
| Where does ₹1.8 crore come from? | Copilot ₹4.53 crore a year minus the fixed timetable's ₹2.74 crore, on the same battery and prices. | Kartikeya |
| Does the ₹10,000 price ceiling understate profit? | No. We are paid the real settlement price; the ceiling only hides how scarce power was above ₹10,000. | Kartikeya |
| Is the payback realistic? | It is before financing and taxes, at the CTUIL benchmark cost, with ₹1,000 per MWh set aside for battery wear. | Suhaib |
| Why Thursdays? | Honest weak spot: the copilot trails copying yesterday by about ₹1,900 on Thursdays; next fix. | Ashwin |
| Who uses this in India today? | Most Indian batteries run on fixed-fee contracts with state utilities. Trading on the exchange is early; abroad it is normal and done by trading software. We are a tool for that next step. | Arnav |
| Do your demo numbers match the report? | Small differences on single days: the demo re-plans in the browser with a quicker method. Yearly figures come from the full model. | Aryan |

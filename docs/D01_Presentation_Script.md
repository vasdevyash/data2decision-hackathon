# Battery Copilot · Team D01 · Presentation script

Deck: `present.html` (arrow keys to move, F for full screen). Two speakers.
**Hard stop at 11:00.** The script runs to about 10:00, leaving a 1-minute buffer.
Live slides: 6, 7, 10. The clock times are when each slide should *start*.

| Speaker | Slides | Part | Time |
|---|---|---|---|
| Person 1 | 1–4 | Hook and problem | 0:00 – 2:15 |
| Person 2 | 5–7 | Solution and live demo | 2:15 – 6:00 |
| Person 1 | 8–10 | Impact and business case | 6:00 – 8:15 |
| Person 2 | 11–12 | Safety and limits | 8:15 – 9:15 |
| Person 1 | 13–14 | The ask and close | 9:15 – 10:00 |

**Running late?** Cut in this order: the 4-hour battery click on slide 10 (saves 30 s), the second half of slide 7 (stop Play early, saves 40 s), the Monday/Thursday line on slide 12 (saves 15 s).

---

## Person 1 · slides 1–4 · 0:00 – 2:15

**1 · Hook (0:00).** "Good afternoon. What if your battery could earn ₹1.8 crore more every year, without changing a single wire? That is what we found when we studied three and a half years of Indian electricity prices, and in the next ten minutes we will show you how, live."

**2 · The business (0:30).** "Start with how a grid battery makes money. It is a shop. It buys electricity when it is cheap and sells it when it is dear. In India, power is cheapest around noon, when solar panels flood the grid: in the last year the average price at 1 pm was about ₹1,600 a megawatt-hour. It is dearest in the evening, when the sun has set and everyone comes home: about ₹8,000 at 7 pm. That gap, five times over, is the profit."

**3 · The catch (1:10).** "The catch is timing. Batteries sell on the IEX Day-Ahead Market. Every morning between 10 and 12, the trader must lock in tomorrow's whole plan: 96 fifteen-minute slots, buy, sell or wait, before anyone knows tomorrow's prices. At about 1 pm the exchange sets one price per slot, and the plan is binding. So the trader makes 96 guesses a day, with real money on every one."

**4 · Today's practice (1:45).** "Most operators guess with a fixed rule, like 'charge at midday, sell in the evening'. We tested exactly that rule on a full year of real prices. For one 10-megawatt battery it leaves about ₹1.8 crore a year on the table, because prices shift with the season, the weekday and holidays, and a fixed rule cannot follow them. My colleague will show you what we built instead."

## Person 2 · slides 5–7 · 2:15 – 6:00

**5 · The solution (2:15).** "We built a copilot that makes the plan for the trader. It does three things.
First, it predicts all 96 of tomorrow's prices. It blends two models: LEAR, the standard model in electricity-price research, which learns how each 15-minute slot follows the days before it; and Chronos, an AI forecasting model from Amazon, pre-trained on thousands of time series, which is good at spotting the shape of a day.
Second, an optimiser works out the most profitable plan: when to buy, when to sell, how much, while respecting the battery's limits. It can never ask the battery to do something it physically cannot.
Third, it writes the orders, ready to submit before the noon deadline.
We judge every model by one thing: the money it earns, not how close its price guesses are."

**6 · Tomorrow's plan, LIVE (3:15).** *(Point at the headline.)* "This is what the trader sees each morning. One sentence: buy at 2:30 and 11:30 am, sell at 6:15 am and 5:15 pm. The expected profit for tomorrow is about ₹1.25 lakh.
*(Scroll to Pre-bid checks.)* Before anything goes out, it checks itself: never above 10 megawatts, the battery ends the day at its 10 percent reserve, wear stays within two cycles, and sell prices stay profitable even if prices come in low.
*(Point at the buttons.)* The trader approves with one click and downloads the 30 orders for the exchange. A job that takes a desk hours is ready by 10 am."

**7 · A real day, LIVE (4:30).** *(Press Play.)* "Now let us watch it trade a real winter day from our test year, slot by slot, at the real prices.
*(As it runs.)* Overnight, power is cheap, so it buys. *(Morning peak.)* At the morning peak it sells. *(Noon.)* At noon, when solar makes power cheap again, it buys a second time. *(Evening.)* And it sells into the evening peak.
*(At the end.)* It finishes the day back at 10 percent, ready for tomorrow, and on this day it earned 99 percent of what perfect knowledge of the prices would have earned. This is the part a fixed rule cannot do: it found two buy-sell rounds because this winter day had two peaks."

## Person 1 · slides 8–10 · 6:00 – 8:15

**8 · Results (6:00).** "How do we know it works? We tested it on a full year of prices it had never seen. It earns ₹4.5 crore a year for one 10-megawatt battery. That is 95 percent of the most anyone could earn, even someone who knew every price in advance. It beat the simple method of copying yesterday's prices in 22 of 25 months, on two separate years, and statistical tests say a gain like this is very unlikely to be luck."

**9 · Payback (6:45).** "At the government benchmark cost of ₹0.80 crore per megawatt-hour, that profit pays for the battery in under four years. And the copilot itself costs almost nothing to run. It needs only the exchange's own prices and a laptop: no new hardware, no new wires."

**10 · Business case, LIVE (7:20).** *(Point at the profit and loss.)* "This is the business case a CFO would look at: revenue, the cost of power bought, a reserve for battery wear, and the profit. *(Open Battery settings, choose 10 MW · 4 h.)* If the client has a different battery, they change it here and every number updates: profit, payback, project value. So the same tool answers two questions: how to trade tomorrow, and whether a battery is worth building."

## Person 2 · slides 11–12 · 8:15 – 9:15

**11 · Safe (8:15).** "A trading head will ask: can I trust it? The trader stays in control. Every plan is checked before it goes out and approved with one click. And it is watched every day: if the copilot falls below 90 percent of the best possible profit, or behind the simple method, it raises an alert."

**12 · Limits (8:45).** "We also want to be clear about what it cannot do yet. We tested one year of prices, and markets change, so it re-learns every week. Thursdays are its weakest day, and that is our next fix. Taxes and grid fees are left out, as the brief asked. And we model one all-India price, not a specific region."

## Person 1 · slides 13–14 · 9:15 – 10:00

**13 · The ask (9:15).** "So our ask is simple. Run the copilot for 30 days, side by side with your current method. It costs nothing and changes nothing on the ground. If it earns more, go live."

**14 · Close (9:40).** "Thank you. We are Team D01, and we are happy to take your questions."

---

## Q&A: who answers

| Likely question | Short answer | Who |
|---|---|---|
| How does the IEX auction work? | Open the demo's **6 · IEX** tab. Bids 10–12, one price per slot at about 1 pm, binding next day. The battery is about 0.1% of the volume, so it takes the price. | Person 1 |
| Which models, and why two? | LEAR: one regression per slot, the research benchmark. Chronos: Amazon's pre-trained AI model, used without training on Indian data. Blend 40/60, chosen on the validation year by money earned; they make different mistakes. | Person 2 |
| Did the model see the future? | No. Forecasts use only prices known the day before; the blend weight was frozen before the test year; the test year was used once. | Person 2 |
| How much does the model add over a simple rule? | About ₹2,600 a day, ₹9.5 lakh a year, over copying yesterday. Consistent and unlikely to be luck, and it scales with every battery. The ₹1.8 crore is over the fixed timetable. | Person 1 |
| Where does ₹1.8 crore come from? | Copilot ₹4.53 crore a year minus the fixed timetable's ₹2.74 crore, same battery, same prices. | Person 1 |
| Does the ₹10,000 price ceiling understate profit? | No. We are paid the real settlement price; the ceiling only hides how scarce power was above ₹10,000. | Person 1 |
| Is the payback realistic? | It is before financing and taxes, at the CTUIL benchmark cost, with ₹1,000 per MWh set aside for wear. | Person 1 |
| Who does this in India today? | Most Indian batteries run on fixed-fee contracts with state utilities. Trading on the exchange is early; abroad it is normal and done by trading software. We are a tool for that next step. | Person 1 |
| Why do demo numbers differ slightly from the report on a single day? | The demo re-plans in the browser with a quicker method; yearly figures come from the full model. | Person 2 |
| Why Thursdays? | Honest weak spot: it trails copying yesterday by about ₹1,900 on Thursdays. Next fix. | Person 2 |

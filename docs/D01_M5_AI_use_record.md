# D01 · AI Use Record and Team Declaration (Data2Decision 2026)

## AI use record

| What | Tool | How it was used | How we verified it |
|---|---|---|---|
| Code, analysis and drafting | Claude (Anthropic), coding assistant | Wrote and reviewed Python (data preparation, SQL, notebooks, optimiser, forecasting scripts), the web prototype, and drafts of the M2–M5 documents | Every number in the reports is produced by the notebooks; key figures were re-computed with separate code (for example the Sunday capture rate and the test-year benchmarks) |
| Price forecasting | Chronos-Bolt (Amazon, pretrained time-series model) | Used as released, with no training on our data, as one of two forecasters | Scored by trading profit on two unseen years; Diebold–Mariano tests and week-bootstrap ranges |
| In-app assistant (Streamlit version) | Qwen3 4B via Ollama, run locally | Answers questions about the results from a fixed fact sheet | Answers checked against the metrics files; falls back to a rule-based guide |

The team chose the problem refinements, methods and recommendations, checked the outputs, and can explain every result.
No synthetic data was used. Data sources: IEX Day-Ahead Market prices; Open-Meteo archived forecasts (CC BY 4.0); India public holidays.

## Team declaration

We declare that this submission is our team's work, that significant AI use is disclosed above, that all data, code and
research reused are cited, and that we are ready to explain every result.

| Team | Signature | Date |
|---|---|---|
| Team D01 (all members) | /s/ Team D01: typed electronic signature, given with the agreement of every team member | 22 Nov 2026 |

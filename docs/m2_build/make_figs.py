"""Draw the two M2 figures. Usage: python make_figs.py <iex_dam_15min.csv> <out_dir>"""
import sys, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
csv, out = sys.argv[1:3]
fm.fontManager.addfont("/System/Library/Fonts/HelveticaNeue.ttc")
plt.rcParams.update({"font.family": "Helvetica Neue", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "0.35", "xtick.color": "0.25", "ytick.color": "0.25", "axes.labelcolor": "0.2"})
d = pd.read_csv(csv, parse_dates=["datetime"]); t = d[d.datetime >= "2025-11-22"]
h = t.groupby(t.block).mcp_rs_mwh.mean(); x = (h.index - 1) / 4
fig, ax = plt.subplots(figsize=(6.6, 2.3))
ax.axvspan(11, 15, color="0.92", lw=0); ax.axvspan(18, 22, color="0.82", lw=0)
ax.plot(x, h.values, color="black", lw=1.5); ax.axhline(10000, color="0.45", ls="--", lw=0.8)
ax.text(13, 8600, "cheap: charge", ha="center", fontsize=8); ax.text(20, 2000, "dear: discharge", ha="center", fontsize=8)
ax.text(0.2, 10250, "price ceiling ₹10,000", fontsize=7.5, color="0.35")
ax.set_xlim(0, 24); ax.set_ylim(0, 11000); ax.set_xticks(range(0, 25, 3)); ax.set_xticklabels([f"{i:02d}:00" for i in range(0, 25, 3)])
ax.set_ylabel("₹ per MWh"); ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
fig.tight_layout(); fig.savefig(f"{out}/fig1.png", dpi=250)
# Values from src/dispatch_lp.py, test year 22 Nov 2025 - 21 Nov 2026, wear Rs 1,000/MWh
labs = ["Fixed rule (1 cycle)", "Yesterday's prices (1 cycle)", "Yesterday's prices (2 cycles)", "Perfect foresight (1 cycle)", "Perfect foresight (2 cycles)"]
vals = [75091, 102110, 121401, 107757, 130354]
fig, ax = plt.subplots(figsize=(6.6, 2.0)); y = np.arange(5)[::-1]
ax.barh(y, [v / 1000 for v in vals], color=["0.75", "0.4", "0.4", "0.86", "0.86"], height=0.62, lw=0)
for yi, v in zip(y, vals): ax.text(v / 1000 + 1.5, yi, f"₹{v / 1000:,.0f}k", va="center", fontsize=8)
ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=8); ax.tick_params(axis="y", length=0); ax.set_xlim(0, 150)
ax.set_xlabel("Average trading profit, ₹ thousand per day (test year)")
fig.tight_layout(); fig.savefig(f"{out}/fig2.png", dpi=250)

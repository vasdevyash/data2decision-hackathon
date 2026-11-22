# %% [markdown]
# # How should a battery trade electricity? (Team D01, M3)
#
# **The idea in one line.** A big battery makes money like a shop: it **buys electricity when it is cheap** (around noon, when solar
# power floods the grid) and **sells it when it is expensive** (in the evening). The catch: every day it must tell the power exchange
# what it will do in each 15-minute slot of **tomorrow**, before it knows tomorrow's prices.
#
# **Our question.** What is the best way to guess tomorrow, and how much extra money does a better guess make?
#
# **What you will see, step by step**
# 1. Load and check the data
# 2. When is power cheap, and when is it expensive?
# 3. How much do simple guesses earn?
# 4. Where simple guesses fail: Sundays
# 5. Does the weather help?
# 6. When is a second buy-sell round in one day worth it?
# 7. Unusual days
# 8. Four kinds of days
# 9. Price "moods" that last for months
# 10. A forecasting model from research vs the simple guesses
#
# Each step starts with **What we ask**, then the code, then **What we see**. All charts are also saved in `outputs/figures/`.

# %%
import os, sys, json
from pathlib import Path
import numpy as np, pandas as pd, duckdb, holidays
import matplotlib
if "ipykernel" not in sys.modules: matplotlib.use("Agg")
import matplotlib.dates
from IPython.display import display
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from scipy import stats

ROOT = Path.cwd() if (Path.cwd() / "src").exists() else Path.cwd().parent
os.chdir(ROOT); sys.path.insert(0, str(ROOT / "src"))
import battery as bt

FIG = ROOT / "outputs/figures"; FIG.mkdir(parents=True, exist_ok=True)
M = {}  # every number quoted in the PDF
try:
    fm.fontManager.addfont("/System/Library/Fonts/HelveticaNeue.ttc"); FONT = "Helvetica Neue"
except Exception:
    FONT = "DejaVu Sans"
plt.rcParams.update({"font.family": FONT, "font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "0.35", "xtick.color": "0.25", "ytick.color": "0.25", "axes.labelcolor": "0.2",
                     "axes.titlesize": 9, "axes.titleweight": "bold", "axes.titlelocation": "left"})
ACC, GREY, LIGHT = "#1f4e8c", "0.55", "#c9d6e8"

# %% [markdown]
# ## 1. Load and check the data
#
# We join three sources: **IEX prices** (every 15 minutes since April 2023), **weather forecasts** for 13 places in India, and **public holidays**. The cleaning is written in SQL (`sql/m3_prepare.sql`) so anyone can read each step.
# %%
con = duckdb.connect()
hol = pd.DataFrame([(d, n) for y in range(2022, 2027) for d, n in holidays.India(years=y).items()], columns=["d", "name"])
hol["d"] = pd.to_datetime(hol["d"]); con.register("holidays", hol)
con.execute(open("sql/m3_prepare.sql").read())
quality = con.execute("SELECT * FROM quality").df().set_index("check_name").value
print(quality.round(2).to_string())
M["quality"] = quality.round(2).to_dict()

blocks = con.execute("SELECT d, block, price, capped FROM blocks ORDER BY d, block").df()
days = con.execute("SELECT * FROM days ORDER BY d").df(); days["d"] = pd.to_datetime(days.d); days = days.set_index("d")
P = blocks.pivot(index="d", columns="block", values="price"); P.index = pd.to_datetime(P.index)
CAP = blocks.pivot(index="d", columns="block", values="capped"); CAP.index = pd.to_datetime(CAP.index)
M["n_days"] = len(days); M["weather_missing_days"] = int(days.solar_midday_wm2.isna().sum()); M["holidays_in_window"] = int(days.holiday.sum())
print(len(days), "days;", M["weather_missing_days"], "without weather;", M["holidays_in_window"], "holidays")

# %% [markdown]
# ## 2. When is power cheap, and when is it expensive?
#
# **What we ask:** at what hours and in which months is power cheap or expensive? The right chart shows how often the price hits the legal maximum of ₹10,000.
# %%
hr = blocks.assign(hour=(blocks.block - 1) // 4, month=pd.to_datetime(blocks.d).dt.month)
mean_mh = hr.pivot_table(index="month", columns="hour", values="price", aggfunc="mean")
cap_mh = hr.pivot_table(index="month", columns="hour", values="capped", aggfunc="mean") * 100
fig, axs = plt.subplots(1, 2, figsize=(7.4, 2.35), sharey=True)
for ax, mat, cmap, title, fmt in [(axs[0], mean_mh / 1000, "Blues", "Average price, ₹ thousand/MWh", "{:.0f}"),
                                  (axs[1], cap_mh, "Oranges", "Share of blocks at the ₹10,000 cap, %", "{:.0f}")]:
    im = ax.imshow(mat.values, aspect="auto", cmap=cmap, origin="upper")
    ax.set_title(title); ax.set_xticks(range(0, 24, 3)); ax.set_xticklabels([f"{h:02d}" for h in range(0, 24, 3)])
    ax.set_yticks(range(12)); ax.set_yticklabels(["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"], fontsize=7)
    ax.set_xlabel("hour of day"); cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02); cb.ax.tick_params(labelsize=7)
    for s in ax.spines.values(): s.set_visible(False)
fig.tight_layout(); fig.savefig(FIG / "m3_structure.png", dpi=250); plt.show()

# %% [markdown]
# **What we see:** noon is always the cheap time. Evenings are expensive and often hit the ₹10,000 cap (2 out of 3 evenings in August). In winter there is a second expensive spell in the morning, 6–9 am.

# %%
M["cap_evening_may_pct"] = round(float(cap_mh.loc[5, 18:23].mean()), 0)
M["cap_evening_aug_pct"] = round(float(cap_mh.loc[8, 18:23].mean()), 0)
M["midday_min_month"] = int(mean_mh.loc[:, 10:15].mean(axis=1).idxmin()); M["midday_min_price"] = round(float(mean_mh.loc[:, 10:15].mean(axis=1).min()), -1)
M["midday_max_month"] = int(mean_mh.loc[:, 10:15].mean(axis=1).idxmax()); M["midday_max_price"] = round(float(mean_mh.loc[:, 10:15].mean(axis=1).max()), -1)
print({k: M[k] for k in ["cap_evening_may_pct", "cap_evening_aug_pct", "midday_min_month", "midday_min_price", "midday_max_month", "midday_max_price"]})

# %% [markdown]
# ## 3. How much do simple guesses earn?
#
# **What we ask:** if the battery simply assumes *tomorrow = today*, how much does it earn? We compare it with the fixed timetable from the problem canvas and with a perfect guess (the most anyone could earn). Each plan is run on every day and paid at the real prices.
# %%
DEG = 1000.0
rows = []
dates = P.index[7:]
for day in dates:
    p = P.loc[day].values; y1 = P.loc[day - pd.Timedelta(days=1)].values; y7 = P.loc[day - pd.Timedelta(days=7)].values
    r = {"d": day, "fixed": bt.fixed_rule(p, DEG)}
    for cyc in (1, 2):
        c, d = bt.solve(p, DEG, cyc); r[f"hind{cyc}"] = bt.settle(c, d, p, DEG)
        c, d = bt.solve(y1, DEG, cyc); r[f"lag1_{cyc}"] = bt.settle(c, d, p, DEG)
        c, d = bt.solve(y7, DEG, cyc); r[f"lag7_{cyc}"] = bt.settle(c, d, p, DEG)
    rows.append(r)
R = pd.DataFrame(rows).set_index("d").join(days[["split", "dow", "season", "spread", "holiday", "morning_midday_gap", "evening_midday_gap"]])
print(R.groupby("split")[["fixed", "lag1_1", "lag7_1", "lag1_2", "hind1", "hind2"]].mean().round(0).to_string())


def week_bootstrap(x, n=4000, seed=0):
    """95% CI of the mean of a daily series, resampling whole weeks to respect autocorrelation."""
    x = pd.Series(x).dropna(); wk = x.groupby(x.index.to_period("W")).apply(list).values
    rng = np.random.default_rng(seed); means = []
    for _ in range(n):
        pick = rng.integers(0, len(wk), len(wk)); means.append(np.mean(np.concatenate([wk[i] for i in pick])))
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


bench = {}
for sp in ["validate", "test"]:
    r = R[R.split == sp]; h1 = r.hind1.sum(); h2 = r.hind2.sum()
    bench[sp] = {k: round(float(r[k].mean())) for k in ["fixed", "lag1_1", "lag7_1", "lag1_2", "hind1", "hind2"]}
    bench[sp].update({"cap_fixed": round(r.fixed.sum() / h1, 3), "cap_lag1_1": round(r.lag1_1.sum() / h1, 3),
                      "cap_lag7_1": round(r.lag7_1.sum() / h1, 3), "cap_lag1_2": round(r.lag1_2.sum() / h2, 3)})
    lo, hi = week_bootstrap(r.lag1_1 - r.fixed); bench[sp]["lag1_vs_fixed_ci"] = [round(lo), round(hi)]
    lo, hi = week_bootstrap(r.lag1_2 - r.lag1_1); bench[sp]["second_cycle_ci"] = [round(lo), round(hi)]
    bench[sp]["fixed_loss_days"] = int((r.fixed < 0).sum()); bench[sp]["lag1_1_loss_days"] = int((r.lag1_1 < 0).sum())
M["bench"] = bench
print(json.dumps(bench, indent=1))

# %% [markdown]
# ## 4. Where simple guesses fail: Sundays
#
# **What we ask:** on which day of the week does *tomorrow = today* go wrong?
# %%
DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
unc = ~CAP.values
err = {}
for lag in (1, 7):
    Pl = P.shift(lag)
    e = (P - Pl).abs().where(~CAP & ~CAP.shift(lag).fillna(True).astype(bool))
    err[lag] = e.mean(axis=1)
pers = pd.DataFrame({"mae1": err[1], "mae7": err[7]}).join(days.dow)
rank1 = pd.Series([stats.spearmanr(P.iloc[i].values, P.iloc[i - 1].values)[0] for i in range(1, len(P))], index=P.index[1:])
pers = pers.join(rank1.rename("rho1"))
train = R[R.split == "train"]
by_dow_train = train.groupby("dow")[["lag1_1", "lag7_1"]].mean()
rule = {int(d): (7 if by_dow_train.loc[d, "lag7_1"] > by_dow_train.loc[d, "lag1_1"] else 1) for d in by_dow_train.index}
print("weekday rule chosen on train (lag per delivery weekday):", {DOW[k]: v for k, v in rule.items()})
for cyc in (1, 2):
    R[f"wk_{cyc}"] = [R.loc[i, f"lag7_{cyc}"] if rule[int(R.loc[i, "dow"])] == 7 else R.loc[i, f"lag1_{cyc}"] for i in R.index]
wk = {}
for sp in ["validate", "test"]:
    r = R[R.split == sp]; lo, hi = week_bootstrap(r.wk_1 - r.lag1_1)
    wk[sp] = {"gain_1c": round(float((r.wk_1 - r.lag1_1).mean())), "ci_1c": [round(lo), round(hi)],
              "gain_2c": round(float((r.wk_2 - r.lag1_2).mean())), "cap_1c": round(r.wk_1.sum() / r.hind1.sum(), 3)}
M["weekday_rule"] = {DOW[k]: v for k, v in rule.items()}; M["weekday_gain"] = wk
tst = R[R.split == "test"]
M["test_by_dow_lag1_capture"] = {DOW[d]: round(g.lag1_1.sum() / g.hind1.sum(), 3) for d, g in tst.groupby("dow")}
M["mae1_by_dow"] = {DOW[d]: round(float(v)) for d, v in pers.groupby("dow").mae1.mean().items()}
M["mae7_by_dow"] = {DOW[d]: round(float(v)) for d, v in pers.groupby("dow").mae7.mean().items()}
print(json.dumps({k: M[k] for k in ["weekday_gain", "test_by_dow_lag1_capture"]}, indent=1))

fig, axs = plt.subplots(1, 2, figsize=(7.4, 2.15))
x = np.arange(7); g1 = pers.groupby("dow").mae1.mean(); g7 = pers.groupby("dow").mae7.mean()
axs[0].bar(x - 0.2, g1.values, 0.4, color=ACC, label="yesterday (D−1)"); axs[0].bar(x + 0.2, g7.values, 0.4, color=LIGHT, label="same day last week (D−7)")
axs[0].set_xticks(x); axs[0].set_xticklabels(DOW); axs[0].set_title("Price error of a naive copy, ₹/MWh (uncapped blocks)")
axs[0].legend(frameon=False, fontsize=7, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.02))
axs[0].set_ylim(0, max(g1.max(), g7.max()) * 1.25)
capd = pd.Series(M["test_by_dow_lag1_capture"]).reindex(DOW) * 100
axs[1].bar(x, capd.values, 0.55, color=[GREY if v > 93 else ACC for v in capd.values])
for xi, v in zip(x, capd.values): axs[1].text(xi, v + 0.4, f"{v:.0f}%", ha="center", fontsize=7)
axs[1].set_ylim(80, 100); axs[1].set_xticks(x); axs[1].set_xticklabels(DOW); axs[1].set_title("Profit captured, yesterday's prices (test year)")
fig.tight_layout(); fig.savefig(FIG / "m3_weekday.png", dpi=250); plt.show()

# %% [markdown]
# **What we see:** *tomorrow = today* works well on most days but badly on **Sundays** (84% of the possible profit, against 94–98% on other days), because Sunday looks nothing like Saturday. Simple fix: for Sundays, copy **last Sunday**. Chosen using only the oldest data, it still adds about **₹850 a day** on the two newer years.

# %%

# %% [markdown]
# ## 5. Does the weather help?
#
# **What we ask:** sunnier days should mean cheaper noon power, and hotter evenings dearer evening power. Does the weather forecast explain the day-to-day price changes?
# %%
D = days.copy()
for c in ["midday_price", "evening_price", "solar_midday_wm2", "cloud_midday_pct", "temp_max_c", "temp_evening_c", "wind_kmh", "wind_evening_kmh"]:
    D[f"d_{c}"] = D[c] - D[c].shift(1)
D["dow_prev"] = D.dow.shift(1)
D = D.dropna(subset=["d_midday_price", "d_solar_midday_wm2"])
trans = pd.get_dummies(D.dow.astype(int).astype(str), prefix="dow", drop_first=True).astype(float)
specs = {"midday": ("d_midday_price", ["d_solar_midday_wm2", "d_cloud_midday_pct", "d_temp_max_c", "d_wind_kmh"]),
         "evening": ("d_evening_price", ["d_temp_evening_c", "d_temp_max_c", "d_wind_evening_kmh", "d_solar_midday_wm2"])}
wx = {}
for seg, (yv, xv) in specs.items():
    X_all = pd.concat([D[xv], trans, D[["holiday"]].astype(float)], axis=1); X_all.insert(0, "const", 1.0)
    tr = D.split == "train"; te = D.split != "train"
    beta, *_ = np.linalg.lstsq(X_all[tr].values, D.loc[tr, yv].values, rcond=None)
    pred = X_all[te].values @ beta; y = D.loc[te, yv].values
    r2_oos = 1 - np.sum((y - pred) ** 2) / np.sum(y ** 2)  # vs predicting "no change" = persistence
    Xc = pd.concat([trans, D[["holiday"]].astype(float)], axis=1); Xc.insert(0, "const", 1.0)
    bc, *_ = np.linalg.lstsq(Xc[tr].values, D.loc[tr, yv].values, rcond=None)
    r2_cal = 1 - np.sum((y - Xc[te].values @ bc) ** 2) / np.sum(y ** 2)
    wx[seg] = {"r2_oos_weather_calendar": round(float(r2_oos), 3), "r2_oos_calendar_only": round(float(r2_cal), 3),
               "coef": {k: round(float(v), 2) for k, v in zip(X_all.columns, beta) if k in xv}}
M["weather"] = wx
c_solar = stats.pearsonr(D.d_solar_midday_wm2, D.d_midday_price); c_temp = stats.pearsonr(D.d_temp_evening_c, D.d_evening_price)
M["corr_dsolar_dmidday"] = [round(float(c_solar[0]), 2), float(c_solar[1])]; M["corr_dtemp_devening"] = [round(float(c_temp[0]), 2), float(c_temp[1])]
lvl = stats.pearsonr(days.solar_midday_wm2.dropna(), days.midday_price[days.solar_midday_wm2.notna()])
M["corr_solar_midday_level"] = round(float(lvl[0]), 2)
print(json.dumps(wx, indent=1), M["corr_dsolar_dmidday"], M["corr_dtemp_devening"])

fig, axs = plt.subplots(1, 2, figsize=(7.4, 2.25))
for ax, xc, yc, xl, title in [(axs[0], "d_solar_midday_wm2", "d_midday_price", "change in forecast midday solar radiation, W/m²", "Midday price vs solar, day over day"),
                              (axs[1], "d_temp_evening_c", "d_evening_price", "change in forecast evening temperature, °C", "Evening price vs temperature, day over day")]:
    ax.scatter(D[xc], D[yc] / 1000, s=4, color=ACC, alpha=0.25, lw=0)
    bfit = np.polyfit(D[xc], D[yc] / 1000, 1); xs = np.linspace(D[xc].quantile(0.005), D[xc].quantile(0.995), 50)
    ax.plot(xs, np.polyval(bfit, xs), color="#c0392b", lw=1.4)
    r = stats.pearsonr(D[xc], D[yc])[0]; ax.text(0.98, 0.92, f"r = {r:.2f}", transform=ax.transAxes, ha="right", fontsize=8)
    ax.axhline(0, color="0.8", lw=0.6); ax.axvline(0, color="0.8", lw=0.6)
    ax.set_xlabel(xl); ax.set_title(title); ax.set_ylabel("₹ thousand/MWh")
    ax.set_xlim(D[xc].quantile(0.005), D[xc].quantile(0.995)); ax.set_ylim(-4.5, 4.5)
fig.tight_layout(); fig.savefig(FIG / "m3_weather.png", dpi=250); plt.show()

# %% [markdown]
# **What we see:** almost no link (the dots form a flat cloud). Weather does not explain the day-to-day price moves; the day of the week does. So we will not build the model around weather.

# %%

# %% [markdown]
# ## 6. When is a second buy-sell round in one day worth it?
#
# **What we ask:** the battery can fill and empty itself twice a day. When does the second round earn more than the wear it causes?
# %%
R["v2_hind"] = R.hind2 - R.hind1; R["v2_lag1"] = R.lag1_2 - R.lag1_1
v = R.dropna(subset=["morning_midday_gap"])
M["second_cycle"] = {
    "corr_v2_morning_gap": round(float(stats.pearsonr(v.v2_hind, v.morning_midday_gap)[0]), 2),
    "corr_v2_persistence": round(float(v.v2_hind.autocorr(1)), 2),
    "share_days_lag1_2c_worse": round(float((R[R.split == "test"].v2_lag1 < 0).mean()), 3),
    "v2_by_season_test": {k: round(float(g.v2_lag1.mean())) for k, g in R[R.split == "test"].groupby("season")},
    "v2_hind_mean_test": round(float(R[R.split == "test"].v2_hind.mean())),
}
# Conditional cycling: run the 2nd cycle only if yesterday's perfect-foresight 2nd-cycle value (known at bid time)
# exceeded a threshold. Source prices follow the weekday rule from section 4. Threshold chosen on train only.
R["v2_prev"] = R.v2_hind.shift(1)
def cond(r, th): return np.where(r.v2_prev > th, r.wk_2, r.wk_1)
trn = R[(R.split == "train") & R.v2_prev.notna()]
grid_th = np.arange(0, 30001, 1000); best_th = int(grid_th[np.argmax([cond(trn, th).mean() for th in grid_th])])
cc = {"threshold": best_th}
for sp in ["validate", "test"]:
    r = R[R.split == sp]; gain = cond(r, best_th) - r.lag1_2; lo, hi = week_bootstrap(pd.Series(gain, index=r.index))
    cc[sp] = {"mean": round(float(cond(r, best_th).mean())), "gain_vs_lag1_2": round(float(gain.mean())), "ci": [round(lo), round(hi)],
              "capture": round(float(cond(r, best_th).sum() / r.hind2.sum()), 3), "share_2c_days": round(float((r.v2_prev > best_th).mean()), 2)}
M["conditional_cycling"] = cc
print("conditional cycling:", json.dumps(cc))
q = pd.qcut(v.morning_midday_gap, 5, labels=False)
M["second_cycle"]["v2_by_gap_quintile"] = [round(float(x)) for x in v.groupby(q).v2_hind.mean().values]
print(json.dumps(M["second_cycle"], indent=1))

fig, axs = plt.subplots(1, 2, figsize=(7.4, 2.15), gridspec_kw={"width_ratios": [1.25, 1]})
axs[0].scatter(v.morning_midday_gap / 1000, v.v2_hind / 1000, s=4, color=ACC, alpha=0.3, lw=0)
axs[0].set_xlabel("morning (5–9 am) minus midday price, ₹ thousand/MWh"); axs[0].set_ylabel("₹ thousand/day")
axs[0].set_title("Value of a 2nd cycle (perfect foresight) vs morning peak"); axs[0].axhline(0, color="0.8", lw=0.6)
t = R[R.split == "test"]; mo = t.groupby(t.index.month).v2_lag1.mean() / 1000
order = [11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]; mo = mo.reindex(order)
axs[1].bar(range(12), mo.values, color=[ACC if x > 0 else "#c0392b" for x in mo.values], width=0.65)
axs[1].set_xticks(range(12)); axs[1].set_xticklabels(["N", "D", "J", "F", "M", "A", "M", "J", "J", "A", "S", "O"])
axs[1].set_title("2nd cycle gain, yesterday's prices, test year"); axs[1].set_ylabel("₹ thousand/day")
fig.tight_layout(); fig.savefig(FIG / "m3_second_cycle.png", dpi=250); plt.show()

# %% [markdown]
# **What we see:** a second round only pays when there is a **morning peak** as well as an evening one. That happens mostly in **winter** (worth ₹38,000 a day in Oct–Feb) and almost never in Mar–Jun.

# %%

# %% [markdown]
# ## 7. Unusual days
#
# **What we ask:** which days look very different from normal, and why?
# %%
roll = days.mean_price.rolling(30).mean()
sp = days.spread; z = (sp - sp.rolling(60, center=True, min_periods=20).median()) / (1.4826 * (sp - sp.rolling(60, center=True, min_periods=20).median()).abs().rolling(60, center=True, min_periods=20).median())
M["anomalies"] = {
    "days_all_evening_capped": int((CAP.loc[:, 73:96].all(axis=1)).sum()),
    "days_any_cap": int(CAP.any(axis=1).sum()),
    "max_capped_blocks_day": int(days.capped_blocks.max()),
    "rolling30_min": round(float(roll.min())), "rolling30_min_date": str(roll.idxmin().date()),
    "rolling30_max": round(float(roll.max())), "rolling30_max_date": str(roll.idxmax().date()),
    "holiday_mean_price_gap": round(float(days[days.holiday].mean_price.mean() - days[~days.holiday & days.dow.between(1, 5)].mean_price.mean())),
    "fixed_worst_day": round(float(R.fixed.min())), "fixed_worst_date": str(R.fixed.idxmin().date()),
}
top = z.abs().sort_values(ascending=False).head(10)
M["anomalies"]["top10_spread_anomalies"] = [[str(i.date()), DOW[int(days.dow[i])], round(float(days.spread[i])), round(float(z[i]), 1)] for i in top.index]
M["anomalies"]["top10_share_sunday_or_holiday"] = round(float(np.mean([(days.dow[i] == 0) or bool(days.holiday[i]) for i in top.index])), 2)
M["anomalies"]["sunday_spread_vs_weekday"] = round(float(days[days.dow == 0].spread.mean() / days[days.dow.between(1, 5)].spread.mean()), 3)
M["anomalies"]["fixed_worst_day_evening_minus_midday"] = round(float(days.evening_midday_gap[R.fixed.idxmin()]))
print(json.dumps(M["anomalies"], indent=1))

# %% [markdown]
# ## 8. Four kinds of days
#
# **What we ask:** do days come in a few typical shapes? We let an algorithm (k-means clustering) group days by the shape of their price curve, then check how often tomorrow is the same kind of day as today.
# %%
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
MED, MAD = float(np.median(P.values)), float(stats.median_abs_deviation(P.values, axis=None, scale="normal"))
fwd = lambda x: np.arcsinh((x - MED) / MAD); inv = lambda z: np.sinh(z) * MAD + MED
Z = fwd(P.values)
M["vst"] = {"skew_raw": round(float(stats.skew(P.values.ravel())), 2), "skew_asinh": round(float(stats.skew(Z.ravel())), 2),
            "kurt_raw": round(float(stats.kurtosis(P.values.ravel())), 2), "kurt_asinh": round(float(stats.kurtosis(Z.ravel())), 2)}
sil = {k: float(silhouette_score(Z, KMeans(k, n_init=10, random_state=0).fit_predict(Z))) for k in range(2, 7)}
K = 4
km = KMeans(K, n_init=20, random_state=0).fit(Z); lab = pd.Series(km.labels_, index=P.index)
# name clusters by their shape
prof = P.groupby(lab).mean()
def name(c):
    r = prof.loc[c]; mid = r.loc[41:64].mean(); eve = r.loc[73:96].mean(); morn = r.loc[25:36].mean(); lvl = r.mean()
    if eve > 9000 * 0.85 and r.loc[1:24].mean() > 7000: return "Scarce (capped evening and night)"
    if morn - mid > 2500: return "Double peak (morning + evening)"
    if lvl < 4000: return "Flat and cheap"
    return "Solar dip, evening peak"
names = {c: name(c) for c in prof.index}
if len(set(names.values())) < K:  # fall back to ordered labels if two clusters share a name
    for i, c in enumerate(prof.mean(axis=1).sort_values().index): names[c] = f"{names[c]} ({i + 1})"
lab_n = lab.map(names)
dt_tab = pd.DataFrame({"share": lab_n.value_counts(normalize=True)})
RR = R.join(lab_n.rename("type")).join(lab_n.shift(1).rename("type_prev"))
dt_tab["sunday_share"] = RR.groupby("type").apply(lambda g: (g.dow == 0).mean())
dt_tab["winter_share"] = RR.groupby("type").apply(lambda g: (g.season == "Oct-Feb").mean())
dt_tab["v2_hind"] = RR.groupby("type").v2_hind.mean()
dt_tab["lag1_capture"] = RR.groupby("type").apply(lambda g: g.lag1_1.sum() / g.hind1.sum())
trans_m = pd.crosstab(lab_n.shift(1), lab_n, normalize="index")
same = RR.type == RR.type_prev
M["day_types"] = {"k": K, "silhouette": {str(k): round(v, 3) for k, v in sil.items()},
                  "table": {t: {c: round(float(v), 3) for c, v in r.items()} for t, r in dt_tab.iterrows()},
                  "share_type_change": round(float(1 - same.mean()), 3),
                  "capture_same_type": round(float(RR[same].lag1_1.sum() / RR[same].hind1.sum()), 3),
                  "capture_type_change": round(float(RR[~same].lag1_1.sum() / RR[~same].hind1.sum()), 3),
                  "regret_share_on_changes": round(float((RR.hind1 - RR.lag1_1)[~same].sum() / (RR.hind1 - RR.lag1_1).sum()), 3)}
print(json.dumps(M["day_types"], indent=1))

order_t = dt_tab.sort_values("share", ascending=False).index.tolist()
cols = [ACC, "#6b8fc2", "0.45", "#c0392b"]
fig, axs = plt.subplots(1, 2, figsize=(7.4, 2.75), gridspec_kw={"width_ratios": [1.45, 1]})
xh = (np.arange(96)) / 4
for t, c in zip(order_t, cols):
    members = lab_n[lab_n == t].index
    axs[0].plot(xh, P.loc[members].mean().values / 1000, color=c, lw=1.6, label=f"{t} ({dt_tab.share[t] * 100:.0f}%)")
axs[0].set_xticks(range(0, 25, 3)); axs[0].set_xlim(0, 24); axs[0].set_ylim(0, 10.5); axs[0].set_xlabel("hour of day")
axs[0].set_ylabel("₹ thousand/MWh"); axs[0].set_title("Average daily curve of each day type")
axs[0].legend(frameon=False, fontsize=6.8, loc="upper center", bbox_to_anchor=(0.5, -0.24), ncol=2)
tm = trans_m.reindex(index=order_t, columns=order_t) * 100
im = axs[1].imshow(tm.values, cmap="Blues", vmin=0, vmax=100)
for i in range(K):
    for j in range(K): axs[1].text(j, i, f"{tm.values[i, j]:.0f}", ha="center", va="center", fontsize=7.5, color="white" if tm.values[i, j] > 55 else "0.15")
short = [t.split(" (")[0].split(",")[0].replace("Solar dip", "Solar dip").replace("Double peak", "Double pk") for t in order_t]
SHORT = {"Solar dip, evening peak": "Solar dip", "Flat and cheap": "Flat", "Double peak (morning + evening)": "Double peak", "Scarce (capped evening and night)": "Scarce"}
tl = [SHORT.get(t, t[:10]) for t in order_t]
axs[1].set_xticks(range(K)); axs[1].set_xticklabels(tl, fontsize=7, rotation=20); axs[1].set_yticks(range(K)); axs[1].set_yticklabels(tl, fontsize=7)
axs[1].set_xlabel("type tomorrow"); axs[1].set_ylabel("type today"); axs[1].set_title("Next-day type, % of days")
for s_ in axs[1].spines.values(): s_.set_visible(False)
fig.tight_layout(); fig.savefig(FIG / "m3_daytypes.png", dpi=250); plt.show()

# %% [markdown]
# **What we see:** four kinds of days. "Double peak" days (22% of days, mostly winter) are where the second round makes money. Tomorrow is the same kind of day as today **77% of the time**, which is why *tomorrow = today* is such a strong guess.

# %%
M["day_type_order"] = order_t

# %% [markdown]
# ## 9. Price "moods" that last for months
#
# **What we ask:** does the price level shift for long stretches? A changepoint method (PELT) marks the dates where the average level jumps.
# %%
import ruptures as rpt
wkly = days.mean_price.resample("W").mean().dropna()
algo = rpt.Pelt(model="l2", min_size=8).fit(wkly.values.reshape(-1, 1) / 1000)
bk = algo.predict(pen=12)
seg_edges = [0] + bk
segs = [(wkly.index[a].date(), wkly.index[b - 1].date(), float(wkly.iloc[a:b].mean())) for a, b in zip(seg_edges[:-1], seg_edges[1:])]
M["changepoints"] = [[str(a), str(b), round(m)] for a, b, m in segs]
print(M["changepoints"])
fig, ax = plt.subplots(figsize=(7.4, 1.75))
ax.plot(wkly.index, wkly.values / 1000, color="0.55", lw=0.9)
for a, b, m in segs: ax.hlines(m / 1000, pd.Timestamp(a), pd.Timestamp(b), color=ACC, lw=2.2)
for b in bk[:-1]: ax.axvline(wkly.index[b], color="#c0392b", lw=0.7, ls="--")
for sp_, c in [("2024-11-22", "validate"), ("2025-11-22", "test")]:
    ax.text(pd.Timestamp(sp_), 9.3, c, fontsize=7, color="0.35"); ax.axvline(pd.Timestamp(sp_), color="0.75", lw=0.6)
ax.set_ylabel("₹ thousand/MWh"); ax.set_ylim(0, 10); ax.set_title("Weekly average price (grey), PELT segments (blue) and breaks (red)")
fig.tight_layout(); fig.savefig(FIG / "m3_changepoints.png", dpi=250); plt.show()

# %% [markdown]
# **What we see:** five long "moods", from about ₹4,000 to ₹7,000 average. One shift happens in April 2026, inside our test year, so any model must keep re-learning.

# %%

# %% [markdown]
# ## 10. A forecasting model from research vs the simple guesses
#
# **What we ask:** can a proper forecasting model beat *tomorrow = today*? We use **LEAR**, the model that a leading review of electricity price forecasting (Lago et al., 2021) recommends as the standard to beat. It learns from the last few days' prices, the weekday and holidays. We judge it by **money earned**, not just by forecast error.
# %%
from sklearn.linear_model import LassoLarsIC
from sklearn.preprocessing import StandardScaler
WX = ["solar_midday_wm2", "cloud_midday_pct", "temp_max_c", "temp_evening_c", "wind_kmh", "wind_evening_kmh"]
Zdf = pd.DataFrame(Z, index=P.index, columns=P.columns)
def feats(use_wx=True):
    f = [Zdf.shift(1).add_prefix("l1_"), Zdf.shift(2).add_prefix("l2_"), Zdf.shift(7).add_prefix("l7_"),
         pd.get_dummies(days.dow.astype(int), prefix="dow").astype(float), days[["holiday"]].astype(float)]
    if use_wx: f.append(days[WX])
    return pd.concat(f, axis=1).dropna()
def lear(use_wx=True):
    X = feats(use_wx); Y = Zdf.loc[X.index]; out = pd.DataFrame(index=X.index[X.index >= "2024-11-22"], columns=P.columns, dtype=float)
    for m0 in pd.date_range("2024-11-22", "2026-11-22", freq="MS").insert(0, pd.Timestamp("2024-11-22")):
        m1 = (m0 + pd.offsets.MonthBegin(1)); idx = out.index[(out.index >= m0) & (out.index < m1)]
        if len(idx) == 0: continue
        tr = X.index < m0; sc_ = StandardScaler().fit(X[tr]); Xtr = sc_.transform(X[tr]); Xte = sc_.transform(X.loc[idx])
        for b in P.columns:
            mdl = LassoLarsIC(criterion="aic").fit(Xtr, Y.loc[tr, b].values); out.loc[idx, b] = mdl.predict(Xte)
    return inv(out.values), out.index
def dm_test(d, lags=7):
    d = np.asarray(d, float); n = len(d); dc = d - d.mean(); g = [np.dot(dc[k:], dc[:n - k]) / n for k in range(lags + 1)]
    v = g[0] + 2 * sum((1 - k / (lags + 1)) * g[k] for k in range(1, lags + 1)); stat = d.mean() / np.sqrt(v / n)
    return float(stat), float(2 * (1 - stats.norm.cdf(abs(stat))))
lear_res = {}
for tag, use_wx in [("lear", True), ("lear_nowx", False)]:
    F, fidx = lear(use_wx)
    pr = []
    for i, day in enumerate(fidx):
        p = P.loc[day].values; r = {"d": day}
        for cyc in (1, 2): c, d = bt.solve(F[i], DEG, cyc); r[f"{tag}_{cyc}"] = bt.settle(c, d, p, DEG)
        pr.append(r)
    R = R.join(pd.DataFrame(pr).set_index("d"))
    err_f = np.abs(F - P.loc[fidx].values)[~CAP.loc[fidx].values].mean()
    lear_res[tag] = {"mae_uncapped": round(float(err_f))}
    if tag == "lear": F_LEAR, IDX_LEAR = F, fidx
mae_l1 = np.abs(P.shift(1).loc[IDX_LEAR].values - P.loc[IDX_LEAR].values)[~CAP.loc[IDX_LEAR].values].mean()
mae_l7 = np.abs(P.shift(7).loc[IDX_LEAR].values - P.loc[IDX_LEAR].values)[~CAP.loc[IDX_LEAR].values].mean()
lear_res["mae_lag1_uncapped"] = round(float(mae_l1)); lear_res["mae_lag7_uncapped"] = round(float(mae_l7))
for sp in ["validate", "test"]:
    r = R[R.split == sp]
    for tag in ["lear", "lear_nowx"]:
        for cyc in (1, 2):
            dlt = r[f"{tag}_{cyc}"] - r[f"lag1_{cyc}"]; lo, hi = week_bootstrap(dlt); st_, pv = dm_test(dlt.values)
            lear_res.setdefault(sp, {})[f"{tag}_{cyc}"] = {"mean": round(float(r[f"{tag}_{cyc}"].mean())), "gain_vs_lag1": round(float(dlt.mean())),
                "ci": [round(lo), round(hi)], "dm": round(st_, 2), "p": round(pv, 4),
                "capture": round(float(r[f"{tag}_{cyc}"].sum() / r[f"hind{cyc}"].sum()), 3)}
M["lear"] = lear_res
print(json.dumps(lear_res, indent=1))

# cumulative profit gained over the yesterday's-prices schedule (up to 2 cycles), validate + test
oos = R[R.split != "train"].copy()
oos["cond"] = np.where(oos.v2_prev > M["conditional_cycling"]["threshold"], oos.wk_2, oos.wk_1)
fig, axs = plt.subplots(1, 2, figsize=(7.4, 2.3), gridspec_kw={"width_ratios": [1.5, 1]})
for col, lbl, c in [("lear_2", "LEAR forecast", ACC), ("cond", "Two simple rules (Sunday + cycling)", "0.45")]:
    axs[0].plot(oos.index, (oos[col] - oos.lag1_2).cumsum() / 1e7, color=c, lw=1.5, label=lbl)
axs[0].axhline(0, color="0.7", lw=0.6); axs[0].axvline(pd.Timestamp("2025-11-22"), color="0.75", lw=0.6)
axs[0].text(pd.Timestamp("2025-11-29"), 0.02, "test year", fontsize=7, color="0.35")
axs[0].set_ylabel("₹ crore, cumulative"); axs[0].set_title("Profit gained over yesterday's prices (≤2 cycles)")
axs[0].legend(frameon=False, fontsize=6.8, loc="upper left"); axs[0].xaxis.set_major_locator(matplotlib.dates.MonthLocator(bymonth=[1, 4, 7, 10]))
axs[0].xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y")); axs[0].tick_params(axis="x", labelsize=7)
labels = ["Fixed", "Last week", "Yesterday", "Simple rules", "LEAR", "Perfect"]
t = R[R.split == "test"]; tt = t.assign(cond=np.where(t.v2_prev > M["conditional_cycling"]["threshold"], t.wk_2, t.wk_1))
vals = [tt.fixed.mean(), tt.lag7_2.mean(), tt.lag1_2.mean(), tt.cond.mean(), tt.lear_2.mean(), tt.hind2.mean()]
axs[1].barh(range(6)[::-1], np.array(vals) / 1000, color=["#c0392b", "0.7", "0.55", "0.45", ACC, "#dfe5ee"], height=0.62)
for yi, v in zip(range(6)[::-1], vals): axs[1].text(v / 1000 + 1.5, yi, f"{v / 1000:.0f}", va="center", fontsize=7)
axs[1].set_yticks(range(6)[::-1]); axs[1].set_yticklabels(labels, fontsize=7.5); axs[1].set_xlim(0, 155)
axs[1].set_title("Test year, ₹ thousand/day (≤2 cycles)"); axs[1].tick_params(axis="y", length=0)
fig.tight_layout(); fig.savefig(FIG / "m3_lear.png", dpi=250); plt.show()

# %% [markdown]
# **What we see:** the research model earns about **₹2,500 a day more** than *tomorrow = today*, every month, on both newer years, and a statistical test says this is very unlikely to be luck. Its guesses are also 24% more accurate. Removing the weather from it changes nothing.

# %%
M["test_ladder_2c"] = {k: round(float(v)) for k, v in zip(labels, vals)}

# %% [markdown]
# ## What we learned
#
# 1. **Don't use the fixed timetable.** Simply assuming *tomorrow = today* earns ₹27,000 a day more.
# 2. **A research forecasting model (LEAR) adds about ₹2,500 a day more**, reliably.
# 3. **The biggest lever is the second daily round**, but only on winter double-peak days.
# 4. **Sundays need special handling.**
# 5. **Weather does not help** at this level, so we skip it.
#
# **Next (M4):** improve the forecaster and decide each day whether to run one round or two.

# %%
json.dump(M, open(ROOT / "outputs/m3_metrics.json", "w"), indent=1, default=float)
print("saved", ROOT / "outputs/m3_metrics.json")

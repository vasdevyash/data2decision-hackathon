# %% [markdown]
# # D01 · M3 UNDERSTAND · Exploratory analysis: battery dispatch against IEX day-ahead prices
#
# Reproduces every number and figure in `docs/D01_M3.pdf`. Run from the repository root or from `notebooks/`.
#
# **Inputs:** `data/raw/iex_dam_15min.csv` (IEX DAM, M2), `data/processed/weather_daily.csv`
# (`src/download_weather.py`, Open-Meteo archived forecasts), India public holidays (`holidays` package).
# **Outputs:** `outputs/figures/m3_*.png`, `outputs/m3_metrics.json`.
#
# Splits are time-ordered and fixed in M2: train 1 Apr 2023 – 21 Nov 2024, validate 22 Nov 2024 – 21 Nov 2025,
# test 22 Nov 2025 – 21 Nov 2026. Any rule chosen here is chosen on **train** only.

# %%
import os, sys, json
from pathlib import Path
import numpy as np, pandas as pd, duckdb, holidays
import matplotlib; matplotlib.use("Agg")
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
# ## 1. Preparation and integration in SQL (DuckDB)
# `sql/m3_prepare.sql` types and flags every block, runs quality checks and builds one row per day joined to
# weather and holidays.

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
# ## 2. Price structure: when is power cheap, when is it capped?

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
fig.tight_layout(); fig.savefig(FIG / "m3_structure.png", dpi=250); plt.close(fig)
M["cap_evening_may_pct"] = round(float(cap_mh.loc[5, 18:23].mean()), 0)
M["cap_evening_aug_pct"] = round(float(cap_mh.loc[8, 18:23].mean()), 0)
M["midday_min_month"] = int(mean_mh.loc[:, 10:15].mean(axis=1).idxmin()); M["midday_min_price"] = round(float(mean_mh.loc[:, 10:15].mean(axis=1).min()), -1)
M["midday_max_month"] = int(mean_mh.loc[:, 10:15].mean(axis=1).idxmax()); M["midday_max_price"] = round(float(mean_mh.loc[:, 10:15].mean(axis=1).max()), -1)
print({k: M[k] for k in ["cap_evening_may_pct", "cap_evening_aug_pct", "midday_min_month", "midday_min_price", "midday_max_month", "midday_max_price"]})

# %% [markdown]
# ## 3. Benchmarks, day by day, on every split
# Each schedule is optimised on its price input and settled at actual prices (₹1,000/MWh wear).

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
# ## 4. Where "yesterday's prices" breaks: the weekly cycle
# Persistence error and rank agreement by delivery weekday, then a weekday-aware rule chosen on train only.

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
fig.tight_layout(); fig.savefig(FIG / "m3_weekday.png", dpi=250); plt.close(fig)

# %% [markdown]
# ## 5. Does the weather explain what persistence misses?
# Day-over-day change in segment prices regressed on day-over-day change in forecast weather plus
# weekday-transition dummies. Fitted on train; scored out of sample on validate + test.

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
fig.tight_layout(); fig.savefig(FIG / "m3_weather.png", dpi=250); plt.close(fig)

# %% [markdown]
# ## 6. When does the second cycle pay?

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
fig.tight_layout(); fig.savefig(FIG / "m3_second_cycle.png", dpi=250); plt.close(fig)

# %% [markdown]
# ## 7. Anomalies and regime shifts

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

# %%
json.dump(M, open(ROOT / "outputs/m3_metrics.json", "w"), indent=1, default=float)
print("saved", ROOT / "outputs/m3_metrics.json")

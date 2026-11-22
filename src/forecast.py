"""Day-ahead price forecasters for M4.

LEAR ensemble (Lago, Marcjasz, De Schutter and Weron, 2021, Applied Energy 293, 116983):
one LASSO model per 15-minute block, penalty chosen by AIC, on prices normalised by the window's median
and MAD and then asinh-transformed (Uniejewski, Weron and Ziel, 2018). Inputs: all 96 prices from D-1, D-2,
D-3 and D-7, weekday and holiday dummies. Four calibration windows (56, 84, 364, 728 days) are fitted
separately and their forecasts averaged. Models are refitted every 7 days (the paper refits daily).

Usage: python src/forecast.py   -> writes outputs/forecasts/lear_ens.npz (validation + test years)
"""
import sys, time
from pathlib import Path
import numpy as np, pandas as pd, holidays
from joblib import Parallel, delayed
from scipy import stats
from sklearn.linear_model import LassoLarsIC

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = (56, 84, 364, 728)
START_MODEL = pd.Timestamp("2023-04-01")      # single Rs 10,000 cap regime
FIRST_FORECAST = pd.Timestamp("2024-11-22")   # validation year starts


def load_prices():
    d = pd.read_csv(ROOT / "data/raw/iex_dam_15min.csv", usecols=["date", "block", "mcp_rs_mwh"])
    P = d.pivot(index="date", columns="block", values="mcp_rs_mwh"); P.index = pd.to_datetime(P.index)
    return P.sort_index()


def calendar(index):
    hol = {d for y in range(index.min().year, index.max().year + 1) for d in holidays.India(years=y)}
    cal = pd.get_dummies(index.dayofweek, prefix="dow").astype(float); cal.index = index
    cal["holiday"] = [float(d.date() in hol) for d in index]
    return cal


def _fit_predict_window(P, cal, refit_day, horizon_days, window):
    """Fit 96 LASSO models on `window` days before refit_day; forecast the next horizon_days days."""
    hist = P.loc[(P.index >= START_MODEL) & (P.index < refit_day)].iloc[-window:]
    med = float(np.median(hist.values)); mad = float(stats.median_abs_deviation(hist.values, axis=None, scale="normal")) or 1.0
    fwd = lambda x: np.arcsinh((x - med) / mad)
    Z = fwd(P)  # whole history in this window's scale (lags reach before the window)
    def X_for(days):
        rows = [np.concatenate([Z.loc[d - pd.Timedelta(days=k)].values for k in (1, 2, 3, 7)] + [cal.loc[d].values]) for d in days]
        return np.vstack(rows)
    tr_days = [d for d in hist.index if d - pd.Timedelta(days=7) in Z.index]
    Xtr = X_for(tr_days); mu, sd = Xtr.mean(0), Xtr.std(0); sd[sd == 0] = 1; Xtr = (Xtr - mu) / sd
    Ytr = Z.loc[tr_days].values
    fc_days = [refit_day + pd.Timedelta(days=i) for i in range(horizon_days) if refit_day + pd.Timedelta(days=i) in P.index]
    if not fc_days: return [], None
    Xte = (X_for(fc_days) - mu) / sd
    out = np.empty((len(fc_days), 96))
    Ylag = Z.loc[[d - pd.Timedelta(days=1) for d in tr_days]].values
    for b in range(96):
        # short windows have fewer days than inputs: give AIC a noise estimate (variance of day-over-day change in this block)
        nv = float(np.var(Ytr[:, b] - Ylag[:, b])) if len(tr_days) <= Xtr.shape[1] + 1 else None
        m = LassoLarsIC(criterion="aic", noise_variance=nv).fit(Xtr, Ytr[:, b]); out[:, b] = m.predict(Xte)
    return fc_days, np.sinh(out) * mad + med


def lear_ensemble(P, refit_every=7, n_jobs=8, verbose=True):
    cal = calendar(P.index)
    refits = pd.date_range(FIRST_FORECAST, P.index.max(), freq=f"{refit_every}D")
    jobs = [(r, w) for r in refits for w in WINDOWS]
    t0 = time.time()
    res = Parallel(n_jobs=n_jobs, verbose=0)(delayed(_fit_predict_window)(P, cal, r, refit_every, w) for r, w in jobs)
    if verbose: print(f"LEAR ensemble: {len(jobs)} window-fits x 96 blocks in {time.time() - t0:.0f}s", flush=True)
    per_window = {w: {} for w in WINDOWS}
    for (r, w), (days, fc) in zip(jobs, res):
        for d, row in zip(days, fc if fc is not None else []): per_window[w][d] = row
    days = sorted(per_window[WINDOWS[0]])
    W = {w: np.vstack([per_window[w][d] for d in days]) for w in WINDOWS}
    return pd.DatetimeIndex(days), W


if __name__ == "__main__":
    P = load_prices()
    days, W = lear_ensemble(P)
    out = ROOT / "outputs/forecasts"; out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / "lear_ens.npz", days=days.values.astype("datetime64[D]").astype(str),
                        **{f"w{w}": W[w] for w in WINDOWS}, ens=np.mean([W[w] for w in WINDOWS], axis=0))
    print("saved", out / "lear_ens.npz", len(days), "days")

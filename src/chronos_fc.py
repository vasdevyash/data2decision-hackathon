"""Zero-shot day-ahead forecasts from a pretrained time-series foundation model.

Chronos-Bolt (Ansari et al., 2024, "Chronos: Learning the language of time series", TMLR; Bolt variant,
amazon/chronos-bolt-small on Hugging Face) is used exactly as released: no training on Indian data.
For each delivery day D it sees the last 2,048 fifteen-minute prices up to the end of D-1 (about 21 days)
and returns quantile forecasts for the 96 blocks of D.

Usage: python src/chronos_fc.py  -> outputs/forecasts/chronos.npz (validation + test years)
"""
import time
from pathlib import Path
import numpy as np, pandas as pd, torch
from chronos import BaseChronosPipeline

ROOT = Path(__file__).resolve().parents[1]
QUANTILES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
CONTEXT = 2048


def main(model="amazon/chronos-bolt-small", first="2024-11-22", batch=32):
    d = pd.read_csv(ROOT / "data/raw/iex_dam_15min.csv", usecols=["date", "block", "mcp_rs_mwh"])
    P = d.pivot(index="date", columns="block", values="mcp_rs_mwh"); P.index = pd.to_datetime(P.index); P = P.sort_index()
    flat = P.values.ravel().astype(np.float32)
    days = P.index[P.index >= first]
    pipe = BaseChronosPipeline.from_pretrained(model, device_map="cpu", torch_dtype=torch.float32)
    qs, means, t0 = [], [], time.time()
    for i in range(0, len(days), batch):
        chunk = days[i:i + batch]
        ctx = torch.tensor(np.stack([flat[(P.index.get_loc(dd)) * 96 - CONTEXT:(P.index.get_loc(dd)) * 96] for dd in chunk]))
        q, m = pipe.predict_quantiles(ctx, prediction_length=96, quantile_levels=QUANTILES)
        qs.append(q.numpy()); means.append(m.numpy())
    print(f"Chronos-Bolt: {len(days)} days in {time.time() - t0:.0f}s", flush=True)
    out = ROOT / "outputs/forecasts"; out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / "chronos.npz", days=days.values.astype("datetime64[D]").astype(str),
                        quantiles=np.concatenate(qs), mean=np.concatenate(means), levels=np.array(QUANTILES))
    print("saved", out / "chronos.npz")


if __name__ == "__main__":
    main()

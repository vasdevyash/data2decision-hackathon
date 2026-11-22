"""Download IEX Day-Ahead Market (DAM) 15-minute prices, one month per request.

Source: https://www.iexindia.com/market-data/day-ahead-market/market-snapshot
(15-minute blocks are published from delivery day 1 April 2022 onwards.)

Usage:
    python src/download_iex_dam.py                      # 2022-04-01 to yesterday
    python src/download_iex_dam.py 2025-01-01 2025-12-31

Output: data/raw/iex_dam_15min.csv, one row per 15-minute block.
"""
import csv
import json
import re
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

URL = ("https://www.iexindia.com/market-data/day-ahead-market/market-snapshot"
       "?interval=ONE_FOURTH_HOUR&dp=SELECT_RANGE&showGraph=false&fromDate={f}&toDate={t}")
OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "iex_dam_15min.csv"
RECORD = re.compile(r'\{\\"date\\":\\"\d\d-\d\d-\d{4}\\",\\"period\\":\\"\d\d:\d\d - \d\d:\d\d\\"[^}]*\}')
COLS = ["datetime", "date", "block", "time_block", "purchase_bid_mw", "sell_bid_mw",
        "mcv_mw", "final_scheduled_volume_mw", "mcp_rs_mwh", "congestion"]


def months(start, end):
    d = start
    while d <= end:
        nxt = (d.replace(day=1) + timedelta(days=32)).replace(day=1)
        yield d, min(nxt - timedelta(days=1), end)
        d = nxt


def fetch(f, t):
    url = URL.format(f=f.strftime("%d-%m-%Y"), t=t.strftime("%d-%m-%Y"))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(3):
        try:
            html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8")
            return [json.loads(m.replace('\\"', '"')) for m in RECORD.findall(html)]
        except Exception as e:  # network hiccup: wait and retry
            print(f"  retry {attempt + 1}: {e}")
            time.sleep(5)
    raise RuntimeError(f"failed {f}..{t}")


def main():
    start = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date(2022, 4, 1)
    end = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today() - timedelta(days=1)
    rows = {}
    for f, t in months(start, end):
        recs = fetch(f, t)
        for r in recs:
            d = datetime.strptime(r["date"], "%d-%m-%Y")
            hh, mm = map(int, r["period"][:5].split(":"))
            ts = d.replace(hour=hh, minute=mm)
            rows[ts] = [ts.strftime("%Y-%m-%d %H:%M"), d.strftime("%Y-%m-%d"), hh * 4 + mm // 15 + 1,
                        r["period"], r["purchase_bid"], r["sell_bid"], r["mcv"],
                        r["final_scheduled_volume"], r["mcp"], r.get("congestion")]
        print(f"{f}..{t}: {len(recs)} blocks")
        time.sleep(1)  # be polite to the server
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        w.writerows(rows[k] for k in sorted(rows))
    print(f"wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()

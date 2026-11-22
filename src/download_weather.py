"""Download archived weather forecasts (Open-Meteo Historical Forecast API, CC BY 4.0) for India's
solar hubs, wind hubs and big demand centres, and aggregate them to daily national indices.

Usage: python src/download_weather.py [start YYYY-MM-DD] [end YYYY-MM-DD]
Writes data/raw/weather_hourly.csv (all sites, hourly) and data/processed/weather_daily.csv.

The Historical Forecast API stores what the weather models forecast at the time (stitched from the first
hours of each run), not reanalysis of what actually happened, so it is close to what a trader could know.
"""
import sys, time, json, urllib.request, urllib.parse
from pathlib import Path
import pandas as pd

SITES = {  # name: (lat, lon, role)
    "jodhpur": (26.24, 73.02, "solar"), "bhuj": (23.25, 69.67, "solar"), "anantapur": (14.68, 77.60, "solar"),
    "pavagada": (14.10, 77.28, "solar"), "jaisalmer": (26.92, 70.91, "wind"), "tirunelveli": (8.73, 77.70, "wind"),
    "delhi": (28.61, 77.21, "demand"), "mumbai": (19.08, 72.88, "demand"), "chennai": (13.08, 80.27, "demand"),
    "kolkata": (22.57, 88.36, "demand"), "lucknow": (26.85, 80.95, "demand"), "hyderabad": (17.39, 78.49, "demand"),
    "ahmedabad": (23.02, 72.57, "demand"),
}
VARS = "shortwave_radiation,temperature_2m,wind_speed_80m,cloud_cover"
URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"


def fetch(start, end):
    names = list(SITES)
    q = {"latitude": ",".join(str(SITES[n][0]) for n in names), "longitude": ",".join(str(SITES[n][1]) for n in names),
         "start_date": start, "end_date": end, "hourly": VARS, "timezone": "Asia/Kolkata"}
    with urllib.request.urlopen(URL + "?" + urllib.parse.urlencode(q), timeout=120) as r:
        js = json.load(r)
    frames = []
    for n, j in zip(names, js):
        h = pd.DataFrame(j["hourly"]); h["site"] = n; h["role"] = SITES[n][2]; frames.append(h)
    return pd.concat(frames)


def main(start="2022-04-01", end="2026-11-21"):
    root = Path(__file__).resolve().parents[1]
    chunks, s = [], pd.Timestamp(start)
    while s <= pd.Timestamp(end):
        e = min(s + pd.DateOffset(months=6) - pd.Timedelta(days=1), pd.Timestamp(end))
        print("fetching", s.date(), "to", e.date(), flush=True)
        chunks.append(fetch(str(s.date()), str(e.date()))); s = e + pd.Timedelta(days=1); time.sleep(1)
    h = pd.concat(chunks); h["time"] = pd.to_datetime(h["time"])
    (root / "data/raw").mkdir(parents=True, exist_ok=True); h.to_csv(root / "data/raw/weather_hourly.csv", index=False)

    h["date"] = h.time.dt.normalize(); h["hour"] = h.time.dt.hour
    solar = h[h.role == "solar"]; wind = h[h.role.isin(["wind", "solar"]) & h.site.isin(["jaisalmer", "tirunelveli", "bhuj"])]
    dem = h[h.role == "demand"]
    d = pd.DataFrame({
        # mean shortwave radiation 10:00-15:59 across solar hubs, W/m2: how much solar the grid gets at midday
        "solar_midday_wm2": solar[solar.hour.between(10, 15)].groupby("date").shortwave_radiation.mean(),
        "cloud_midday_pct": solar[solar.hour.between(10, 15)].groupby("date").cloud_cover.mean(),
        # mean daily max temperature across demand centres, C: cooling demand
        "temp_max_c": dem.groupby(["date", "site"]).temperature_2m.max().groupby("date").mean(),
        # mean evening temperature 18:00-23:59 across demand centres: evening-peak demand
        "temp_evening_c": dem[dem.hour >= 18].groupby("date").temperature_2m.mean(),
        # mean 80 m wind speed across wind hubs, km/h, evening and full day
        "wind_kmh": wind.groupby("date").wind_speed_80m.mean(),
        "wind_evening_kmh": wind[wind.hour >= 18].groupby("date").wind_speed_80m.mean(),
    })
    d.index.name = "date"; (root / "data/processed").mkdir(parents=True, exist_ok=True)
    d.round(3).to_csv(root / "data/processed/weather_daily.csv")
    print("daily rows", len(d), "missing", int(d.isna().sum().sum()))


if __name__ == "__main__":
    main(*sys.argv[1:3])

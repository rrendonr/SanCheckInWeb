"""
Fetch live Google Trends demand for the first 151 Pokémon (weekly timeline) and update data.js.
Run: pip install pytrends pandas  then  python fetch_trends.py
Then refresh the website to see live numbers and weekly timeline.
"""
from datetime import datetime
import json
import os
import time

try:
    from pytrends.request import TrendReq
    import pandas as pd
except ImportError:
    print("Install dependencies: pip install pytrends pandas")
    raise SystemExit(1)

from pokemon_list import POKEMON_151, search_term

BATCH_SIZE = 5
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_JS = os.path.join(SCRIPT_DIR, "data.js")
# 12 months of daily data → resample to weekly (~52 weeks per Pokémon)
TIMEFRAME = "today 12-m"
DELAY_BETWEEN_BATCHES = 2


def fetch_batch_weekly(keywords):
    """Fetch interest over time and return weekly averages (0–100) per keyword."""
    pytrends = TrendReq(hl="en-US", tz=360)
    pytrends.build_payload(keywords, timeframe=TIMEFRAME)
    df = pytrends.interest_over_time()
    if df.empty:
        return {kw: [] for kw in keywords}
    if "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])
    # Resample to week (Monday), take mean
    df = df.resample("W").mean().round(0).astype(int)
    result = {}
    for kw in keywords:
        if kw not in df.columns:
            result[kw] = []
            continue
        series = df[kw]
        weekly = [
            {"week": d.strftime("%Y-%m-%d"), "value": int(series.loc[d])}
            for d in series.index
        ]
        result[kw] = weekly
    return result


def main():
    all_results = []
    total_batches = (len(POKEMON_151) + BATCH_SIZE - 1) // BATCH_SIZE

    for b in range(0, len(POKEMON_151), BATCH_SIZE):
        batch = POKEMON_151[b : b + BATCH_SIZE]
        batch_idx = b // BATCH_SIZE + 1
        keywords = [search_term(name) for _, name in batch]
        try:
            weekly_data = fetch_batch_weekly(keywords)
            for (pid, name) in batch:
                key = search_term(name)
                weekly = weekly_data.get(key, [])
                demand = weekly[-1]["value"] if weekly else 0
                all_results.append(
                    {"id": pid, "name": name, "demand": demand, "weekly": weekly}
                )
            print(f"Batch {batch_idx}/{total_batches} ok ({batch[0][1]} … {batch[-1][1]})")
        except Exception as e:
            print(f"Batch {batch_idx}/{total_batches} failed: {e}")
            for (pid, name) in batch:
                all_results.append({"id": pid, "name": name, "demand": 0, "weekly": []})
        if b + BATCH_SIZE < len(POKEMON_151):
            time.sleep(DELAY_BETWEEN_BATCHES)

    updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "// Live demand from Google Trends (weekly, last 3 months). Run fetch_trends.py to update.",
        "window.POKEMON_LAST_UPDATED = " + json.dumps(updated) + ";",
        "window.POKEMON_DATA = [",
    ]
    for r in all_results:
        name_esc = r["name"].replace("\\", "\\\\").replace('"', '\\"')
        weekly_js = json.dumps(r["weekly"]).replace("<", "\\u003c")
        lines.append(
            f'  {{ id: {r["id"]}, name: "{name_esc}", demand: {r["demand"]}, weekly: {weekly_js} }},'
        )
    lines.append("];")

    with open(DATA_JS, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("Updated data.js with live weekly demand for 151 Pokémon.")
    print("Refresh the website to see timelines.")


if __name__ == "__main__":
    main()

"""Generate data.js with 151 Pokémon, no sample data. Run fetch_trends.py to fill from Google Trends."""
import os
from pokemon_list import POKEMON_151

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_JS = os.path.join(SCRIPT_DIR, "data.js")

lines = [
    "// First 151 Pokémon. Data from Google Trends only — run fetch_trends.py to fetch.",
    "window.POKEMON_LAST_UPDATED = null;",
    "window.POKEMON_DATA = [",
]
for pid, name in POKEMON_151:
    esc = name.replace("\\", "\\\\").replace('"', '\\"')
    lines.append(f'  {{ id: {pid}, name: "{esc}", demand: 0, weekly: [] }},')
lines.append("];")

with open(DATA_JS, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print("Wrote data.js with 151 Pokémon (empty weekly — run fetch_trends.py for Google Trends data).")

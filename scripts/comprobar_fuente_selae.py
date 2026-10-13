"""Read-only live check of official SELAE press PDFs."""
import datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import update_data

rows = json.loads((ROOT / "data/sorteos.json").read_text())["draws"]
last = max(rows, key=lambda row: row["date"])
target = datetime.date.fromisoformat(last["date"])
print("Official URL:", update_data.official_url(target), flush=True)
row = update_data.official(target)
print(json.dumps(row, ensure_ascii=False), flush=True)
if row["nums"] != sorted(last["nums"]) or row["reintegro"] != last.get("reintegro"):
    raise SystemExit("OFFICIAL_CONFLICT: latest historical draw differs")
print("LIVE_OFFICIAL_MATCH", flush=True)

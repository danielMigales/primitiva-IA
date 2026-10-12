"""Generate one auditable prospective prediction before each Mon/Thu/Sat draw."""
import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

now = datetime.now(ZoneInfo("Europe/Madrid"))
tomorrow = (now + timedelta(days=1)).date()
if tomorrow.weekday() not in (0, 3, 5):
    print("No draw tomorrow; nothing to register.")
    raise SystemExit(0)
target = tomorrow.isoformat()
source = Path("data/sorteos.json")
rows = sorted(json.loads(source.read_text(encoding="utf-8"))["draws"], key=lambda r: r["date"])
if not rows or rows[-1]["date"] >= target:
    raise ValueError("The source must precede the target draw.")
path = Path("data/reto-predictor.json")
record = json.loads(path.read_text(encoding="utf-8"))
entries = record["predictions"]
if any(r["target"] == target for r in entries):
    print("Prediction already committed for", target)
    raise SystemExit(0)
window = 500
past = rows[-window:]
counts = Counter(n for r in past for n in r["nums"])
short = Counter(n for r in past[-50:] for n in r["nums"])
# Deterministic selection; no claim of a predictive edge.
ranking = sorted(range(1, 50), key=lambda n: (-0.6 * counts[n] / len(past) - 0.4 * short[n] / min(50, len(past)), n))
nums = sorted(ranking[:6])
entry = {
    "target": target,
    "nums": nums,
    "window": window,
    "historyUntil": rows[-1]["date"],
    "created": now.isoformat(),
    "algorithm": "frequency-weighted-v1",
    "recordedBy": "GitHub Actions"
}
entries.append(entry)
entries.sort(key=lambda r: r["target"])
path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("New prospective prediction:", target, nums)

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
learned = json.loads(Path("data/reto-aprendizaje.json").read_text(encoding="utf-8"))
window = learned["strategy"]["window"]
mode = learned["strategy"]["mode"]
past = rows[-window:]
counts = Counter(n for r in past for n in r["nums"])
recent = Counter(n for r in past[-min(20,len(past)):] for n in r["nums"])
def score(n):
    a = counts[n] / len(past)
    b = recent[n] / min(20,len(past))
    return {"hot":a,"cold":-a,"recent":b,"balanced":0.6*a+0.4*b}[mode]
nums = sorted(sorted(range(1,50),key=lambda n:(-score(n),n))[:6])
entry = {
    "target": target,
    "nums": nums,
    "window": window,
    "historyUntil": rows[-1]["date"],
    "created": now.isoformat(),
    "algorithm": "historical-validation-v1:"+mode,
    "recordedBy": "GitHub Actions"
}
entries.append(entry)
entries.sort(key=lambda r: r["target"])
path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("New prospective prediction:", target, nums)

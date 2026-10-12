"""Register an auditable prospective prediction using a frozen strategy."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

now = datetime.now(ZoneInfo("Europe/Madrid"))
tomorrow = (now + timedelta(days=1)).date()
if tomorrow.weekday() not in (0, 3, 5):
    print("No draw tomorrow; nothing to register.")
    raise SystemExit(0)
target = tomorrow.isoformat()
config = json.loads(Path("data/reto-estrategia-congelada.json").read_text(encoding="utf-8"))
assert config["status"] == "frozen" and config["strategy"]["type"] == "pair"
window = config["strategy"]["window"]
rows = sorted(json.loads(Path("data/sorteos.json").read_text(encoding="utf-8"))["draws"], key=lambda r:r["date"])
if len(rows) < window or rows[-1]["date"] >= target:
    raise ValueError("Insufficient or future historical data.")
path = Path("data/reto-predictor.json")
record = json.loads(path.read_text(encoding="utf-8"))
if any(r["target"] == target for r in record["predictions"]):
    print("Already recorded", target)
    raise SystemExit(0)
counts = [0] * 50
pairs = [[0] * 50 for _ in range(50)]
for row in rows[-window:]:
    a = row["nums"]
    for p in range(6):
        counts[a[p]] += 1
        for q in range(p+1, 6):
            x,y = sorted((a[p],a[q]))
            pairs[x][y] += 1
chosen=[]
while len(chosen) < 6:
    def score(n):
        return .05 * counts[n]/window + sum(pairs[min(n,p)][max(n,p)]/window for p in chosen)
    best = sorted((n for n in range(1,50) if n not in chosen), key=lambda n:(-score(n),n))[0]
    chosen.append(best)
entry={"target":target,"nums":sorted(chosen),"window":window,"historyUntil":rows[-1]["date"],
       "created":now.isoformat(),"algorithm":"frozen-pair-50-v1",
       "strategyFile":"data/reto-estrategia-congelada.json","recordedBy":"GitHub Actions",
       "goal":"at-least-three-main-numbers"}
record["predictions"].append(entry)
record["predictions"].sort(key=lambda r:r["target"])
path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Frozen prospective prediction:",target,entry["nums"])

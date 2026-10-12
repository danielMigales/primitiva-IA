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

# Modelo determinista de recencia del reintegro: ventanas 30, 90 y 365 días.
# No se interpreta como garantía ni como evidencia de sesgo del sorteo.
from math import sqrt
def reintegro_rank(history):
    latest = datetime.fromisoformat(history[-1]["date"]).date()
    valid = [r for r in history if type(r.get("reintegro")) is int and 0 <= r["reintegro"] <= 9]
    weights = ((30, .45), (90, .35), (365, .20))
    scored = []
    for digit in range(10):
        components = []
        score = 0.
        for days, weight in weights:
            sample = [r for r in valid if 0 <= (latest - datetime.fromisoformat(r["date"]).date()).days <= days]
            hits = sum(r["reintegro"] == digit for r in sample)
            z = (hits - .1 * len(sample)) / sqrt(.09 * len(sample)) if sample else 0.
            score += weight * max(-3., min(3., z))
            components.append({"days":days,"hits":hits,"draws":len(sample),"expected":round(len(sample)/10,2)})
        scored.append({"digit":digit,"score":score,"windows":components})
    return sorted(scored, key=lambda e:(-e["score"],e["digit"]))
def reintegro_backtest(history):
    valid = [r for r in history if type(r.get("reintegro")) is int and 0 <= r["reintegro"] <= 9]
    start = max(120, int(len(valid)*.55))
    step = max(1, (len(valid)-start)//140)
    tested = list(range(start,len(valid),step))
    hits = sum(reintegro_rank(valid[:i])[0]["digit"] == valid[i]["reintegro"] for i in tested)
    return {"tests":len(tested),"hits":hits,"expectedRandom":round(len(tested)/10,2)}
reintegro_ranking = reintegro_rank(rows)
reintegro_test = reintegro_backtest(rows)
reintegro_choice = reintegro_ranking[0]
entry={"target":target,"nums":sorted(chosen),"window":window,"historyUntil":rows[-1]["date"],
       "created":now.isoformat(),"algorithm":"frozen-pair-50-v1",
       "strategyFile":"data/reto-estrategia-congelada.json","recordedBy":"GitHub Actions",
       "goal":"at-least-three-main-numbers",
       "reintegro":reintegro_choice["digit"],"reintegroAlgorithm":"recency-z-30-90-365-v1",
       "reintegroEvidence":{"lastHistoricalDate":rows[-1]["date"],"score":round(reintegro_choice["score"],4),"windows":reintegro_choice["windows"],"backtest":reintegro_test,
       "interpretation":"Exploratory ranking, no confirmed predictive advantage; fair-draw probability 10 percent."}}
record["predictions"].append(entry)
record["predictions"].sort(key=lambda r:r["target"])
path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Frozen prospective prediction:",target,entry["nums"])

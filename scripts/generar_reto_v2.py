"""Register an auditable prospective prediction using the current recency model."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from validar_reto import validate_prediction

strategy_path = "data/reto-estrategia-activa.json"
strategy_config = json.loads(Path(strategy_path).read_text(encoding="utf-8"))
strategy = strategy_config["strategy"]
# Version 2 retains exactly the approved motor. Fail before writing if its
# parameters drift; a method change must be implemented as a new version.
expected_strategy = {
    "type": "recency-z", "window": 365,
    "windows": [{"days": 30, "weight": .45}, {"days": 90, "weight": .35}, {"days": 365, "weight": .20}],
    "zClip": 3, "scorePrecision": 5, "tieBreak": "number-ascending",
    "algorithm": "unified-recency-z-30-90-365-v1",
    "reintegroAlgorithm": "recency-z-30-90-365-v1",
}
if strategy_config.get("version") != 2 or strategy_config.get("status") != "active" or strategy != expected_strategy:
    raise ValueError("La estrategia activa no coincide con la versión 2 aprobada.")
weights = tuple((item["days"], item["weight"]) for item in strategy["windows"])

now = datetime.now(ZoneInfo("Europe/Madrid"))
# Choose the next future draw immediately, including after a settled draw.
# Never generate a same-day prediction once the draw has started.
target_day = now.date()
if (now.hour, now.minute) >= (21, 40):
    target_day += timedelta(days=1)
while target_day.weekday() not in (0, 3, 5):
    target_day += timedelta(days=1)
target = target_day.isoformat()
rows = sorted(json.loads(Path("data/sorteos.json").read_text(encoding="utf-8"))["draws"], key=lambda r:r["date"])
if len(rows) < 120 or rows[-1]["date"] >= target:
    raise ValueError("Insufficient or future historical data.")
path = Path("data/reto-predictor.json")
record = json.loads(path.read_text(encoding="utf-8"))
if any(r["target"] == target for r in record["predictions"]):
    print("Already recorded", target)
    raise SystemExit(0)
from math import sqrt
def rank_numbers(history):
    latest = datetime.fromisoformat(history[-1]["date"]).date()
    windows = []
    for days, weight in weights:
        sample = [r for r in history if 0 <= (latest-datetime.fromisoformat(r["date"]).date()).days <= days]
        counts = [0]*50
        for r in sample:
            for n in r["nums"]:
                counts[n] += 1
        windows.append((days,weight,len(sample),counts))
    ranked=[]
    for n in range(1,50):
        evidence=[]
        score=0.
        for days,weight,total,counts in windows:
            expected=total*6/49
            z=(counts[n]-expected)/sqrt(total*(6/49)*(43/49)) if total else 0
            score+=weight*max(-3.,min(3.,z))
            evidence.append({"days":days,"hits":counts[n],"draws":total,"expected":round(expected,2)})
        ranked.append({"number":n,"score":round(score,5),"windows":evidence})
    return sorted(ranked,key=lambda x:(-x["score"],x["number"]))
ranked_numbers=rank_numbers(rows)
chosen=sorted(x["number"] for x in ranked_numbers[:6])
number_evidence=[x for x in ranked_numbers if x["number"] in chosen]
window=strategy["window"]
# Modelo determinista de recencia del reintegro: ventanas 30, 90 y 365 días.
# No se interpreta como garantía ni como evidencia de sesgo del sorteo.
from math import sqrt
def reintegro_rank(history):
    latest = datetime.fromisoformat(history[-1]["date"]).date()
    valid = [r for r in history if type(r.get("reintegro")) is int and 0 <= r["reintegro"] <= 9]
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
       "created":now.isoformat(),"algorithm":strategy["algorithm"],
       "strategyVersion":strategy_config["version"],"strategyFile":strategy_path,
       "numberEvidence":number_evidence,"recordedBy":"Generador determinista; fecha de publicación acreditada por el commit de GitHub",
       "goal":strategy_config["objective"],
       "reintegro":reintegro_choice["digit"],"reintegroAlgorithm":strategy["reintegroAlgorithm"],
       "reintegroEvidence":{"lastHistoricalDate":rows[-1]["date"],"score":round(reintegro_choice["score"],4),"windows":reintegro_choice["windows"],"backtest":reintegro_test,
       "interpretation":"Exploratory ranking, no confirmed predictive advantage; fair-draw probability 10 percent."}}
validate_prediction(entry, rows[-1]["date"])
record["predictions"].append(entry)
record["predictions"].sort(key=lambda r:r["target"])
path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Prospective prediction:",target,entry["nums"])

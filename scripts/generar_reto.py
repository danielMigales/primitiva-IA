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
    for days, weight in ((30,.45),(90,.35),(365,.20)):
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
window=365
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
       "created":now.isoformat(),"algorithm":"unified-recency-z-30-90-365-v1",
       "numberEvidence":number_evidence,"recordedBy":"GitHub Actions",
       "goal":"maximize-main-and-reintegro-hits",
       "reintegro":reintegro_choice["digit"],"reintegroAlgorithm":"recency-z-30-90-365-v1",
       "reintegroEvidence":{"lastHistoricalDate":rows[-1]["date"],"score":round(reintegro_choice["score"],4),"windows":reintegro_choice["windows"],"backtest":reintegro_test,
       "interpretation":"Exploratory ranking, no confirmed predictive advantage; fair-draw probability 10 percent."}}
record["predictions"].append(entry)
record["predictions"].sort(key=lambda r:r["target"])
path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Frozen prospective prediction:",target,entry["nums"])

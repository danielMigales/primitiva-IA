"""Train on past draws, select strategy on earlier validation, test on later holdout."""
import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

rows=sorted(json.loads(Path("data/sorteos.json").read_text())["draws"],key=lambda r:r["date"])
strategies=[(w,mode) for w in (20,50,100,500,1000) for mode in ("hot","cold","recent","balanced")]
def predict(past,w,mode):
    p=past[-w:]
    count=Counter(n for r in p for n in r["nums"])
    recent=Counter(n for r in p[-min(20,len(p)):] for n in r["nums"])
    def score(n):
        a=count[n]/len(p)
        b=recent[n]/min(20,len(p))
        return {"hot":a,"cold":-a,"recent":b,"balanced":0.6*a+0.4*b}[mode]
    return sorted(sorted(range(1,50),key=lambda n:(-score(n),n))[:6])
def evaluate(start,end):
    totals={s:{"threePlus":0,"hits":0,"fourPlus":0} for s in strategies}
    for i in range(start,end):
        actual=set(rows[i]["nums"])
        past=rows[:i]
        for s in strategies:
            hits=len(actual.intersection(predict(past,*s)))
            totals[s]["hits"]+=hits
            totals[s]["threePlus"]+=int(hits>=3)
            totals[s]["fourPlus"]+=int(hits>=4)
    return totals
start=1000
if len(rows)<start+400:raise ValueError("Not enough history")
# Earlier training/selection, then an untouched chronological holdout.
cut=start+int((len(rows)-start)*0.7)
validation=evaluate(start,cut)
chosen=max(strategies,key=lambda s:(validation[s]["threePlus"],validation[s]["fourPlus"],validation[s]["hits"],-s[0],s[1]))
holdout=evaluate(cut,len(rows))
best_hits=holdout[chosen]["hits"]
three_plus=holdout[chosen]["threePlus"]
four_plus=holdout[chosen]["fourPlus"]
from math import comb
chance_three_plus=sum(comb(6,k)*comb(43,6-k) for k in range(3,7))/comb(49,6)
n=len(rows)-cut
expected=n*36/49
advantage=best_hits-expected
# A simple conservative decision rule; not a formal multiple-testing corrected claim.
result={"updatedAt":datetime.now(timezone.utc).isoformat(),"historicalDraws":len(rows),
 "strategy":{"window":chosen[0],"mode":chosen[1]},
 "validationDraws":cut-start,"holdoutDraws":n,"holdoutHits":best_hits,
 "holdoutExpectedHits":round(expected,2),
 "goal":"at-least-three-hits","holdoutThreePlus":three_plus,
 "holdoutFourPlus":four_plus,"holdoutExpectedThreePlus":round(n*chance_three_plus,2),
 "holdoutThreePlusRate":round(three_plus/n,5),
 "randomThreePlusRate":round(chance_three_plus,5),"holdoutDifference":round(advantage,2),
 "hasDemonstratedAdvantage":False,
 "note":"Exploratory holdout only; no reliable predictive advantage established. Strategy selected without using holdout outcomes.",
 "nextCombination":predict(rows,*chosen),"lastHistoricalDate":rows[-1]["date"]}
# Keep the advanced experiment visible without promoting an unverified edge.
advanced_path=Path("data/reto-entrenamientos-avanzados.json")
if advanced_path.exists():
    advanced=json.loads(advanced_path.read_text(encoding="utf-8"))
    result["advancedExperiment"]={
        "strategiesCompared":advanced["strategiesCompared"],
        "testDraws":advanced["totalTestDraws"],
        "threePlus":advanced["totalThreePlus"],
        "randomExpectedThreePlus":round(advanced["randomExpectedThreePlus"],2),
        "status":"exploratory-only"
    }
Path("data/reto-aprendizaje.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print("Selected",chosen,"three or more",three_plus,"random expectation",round(n*chance_three_plus,2))

"""Retrospective main-number comparison; never writes production predictions."""
import ast
from collections import Counter
from datetime import date, datetime
import hashlib
import json
from math import comb, sqrt
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "data/evaluacion-metodos-config.json"
DEST = ROOT / "data/evaluacion-metodos.json"
TRACE = ROOT / "data/evaluacion-metodos-detalle.jsonl"


def validate_rows(rows):
    seen = set()
    for row in rows:
        stamp = date.fromisoformat(row["date"])
        nums = row["nums"]
        if stamp.isoformat() != row["date"] or row["date"] in seen or not isinstance(nums, list) or len(nums) != 6 or len(set(nums)) != 6 or any(type(n) is not int or not 1 <= n <= 49 for n in nums):
            raise ValueError("Invalid or duplicate historical draw")
        seen.add(row["date"])


def bayesian_cdm_adaptation(history, prior=1):
    # Adapt CDM posterior-mean ranking to number-occurrence counts (6/49).
    # This is NOT an exact reproduction of the paper's numeric-position model.
    # A uniform prior preserves frequency ranking; scores are not calibrated
    # inclusion probabilities for draws without replacement.
    counts = Counter(n for row in history for n in row["nums"])
    denominator = 6 * len(history) + 49 * prior
    scores = {n: (counts[n] + prior) / denominator for n in range(1, 50)}
    return sorted(sorted(scores, key=lambda n: (-scores[n], n))[:6])


def knn_prediction(history, neighbors=20, training_pairs=500):
    current = set(history[-1]["nums"])
    candidates = []
    # Labels are draws already in history; never the target being evaluated.
    for j in range(max(0, len(history)-1-training_pairs), len(history)-1):
        distance = len(current.symmetric_difference(history[j]["nums"]))
        candidates.append((distance, -j, history[j+1]["nums"]))
    if not candidates:
        raise ValueError("KNN requires previous state/outcome pairs")
    labels = sorted(candidates)[:neighbors]
    counts = Counter(n for _, _, nums in labels for n in nums)
    return sorted(sorted(range(1, 50), key=lambda n: (-counts[n], n))[:6])


def load_current_recency():
    # Compile only the pure ranking function; importing the generator itself
    # would register a prediction. This uses the exact archived version 2 implementation.
    source = (ROOT / "scripts/generar_reto_v2.py").read_text(encoding="utf-8")
    parsed = ast.parse(source)
    node = next(n for n in parsed.body if isinstance(n, ast.FunctionDef) and n.name == "rank_numbers")
    active = json.loads((ROOT / "data/reto-estrategia-v2.json").read_text())
    if active["version"] != 2:
        raise ValueError("This experiment compares the approved version 2")
    weights = tuple((w["days"], w["weight"]) for w in active["strategy"]["windows"])
    namespace = {"datetime": datetime, "sqrt": sqrt, "weights": weights}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "recency-ranking-only", "exec"), namespace)
    return namespace["rank_numbers"], hashlib.sha256(source.encode()).hexdigest()


def hit_summary(hits):
    histogram = [hits.count(k) for k in range(7)]
    return {"draws": len(hits), "totalHits": sum(hits), "meanHits": round(sum(hits)/len(hits), 5),
            "threePlus": sum(h >= 3 for h in hits), "fourPlus": sum(h >= 4 for h in hits),
            "fivePlus": sum(h >= 5 for h in hits), "six": histogram[6], "histogram0to6": histogram}


def holm_adjust(pvalues):
    ordered = sorted(pvalues, key=pvalues.get)
    adjusted, running = {}, 0.
    for i, key in enumerate(ordered):
        running = max(running, min(1., (len(ordered)-i)*pvalues[key]))
        adjusted[key] = running
    return adjusted


def evaluate(rows, config):
    validate_rows(rows)
    rows = sorted(rows, key=lambda row: row["date"])
    start = max(config["minimumTrainingDraws"], len(rows)-config["testDraws"])
    if start >= len(rows):
        raise ValueError("Insufficient training and test history")
    rank, source_hash = load_current_recency()
    methods = {key: [] for key in ("bayesian-cdm-adaptation", "knn", "current-recency-v2", "uniform-control")}
    trace = []
    for i in range(start, len(rows)):
        history, target = rows[:i], rows[i]
        ranked = rank(history)
        rng = random.Random(str(config["randomSeed"])+":"+target["date"])
        predictions = {
            "bayesian-cdm-adaptation": bayesian_cdm_adaptation(history, config["bayesianPriorPerNumber"]),
            "knn": knn_prediction(history, config["knnNeighbors"], config["knnTrainingPairs"]),
            "current-recency-v2": sorted(x["number"] for x in ranked[:6]),
            "uniform-control": sorted(rng.sample(range(1, 50), 6)),
        }
        scored = {}
        for key, nums in predictions.items():
            hits = len(set(nums).intersection(target["nums"]))
            methods[key].append(hits)
            scored[key] = {"nums": nums, "hits": hits}
        trace.append({"target": target["date"], "historyUntil": history[-1]["date"],
                      "actualNums": target["nums"], "methods": scored})
    summaries = {key: hit_summary(hits) for key, hits in methods.items()}
    n = len(trace)
    probabilities = [comb(6,k)*comb(43,6-k)/comb(49,6) for k in range(7)]
    rng = random.Random(config["randomSeed"])
    reference = []
    for _ in range(config["randomReferenceReplicates"]):
        sample = rng.choices(range(7), weights=probabilities, k=n)
        reference.append({"totalHits": sum(sample), "threePlus": sum(h >= 3 for h in sample)})
    pvalues = {}
    for key in summaries:
        if key == "uniform-control":
            continue
        for metric in ("totalHits", "threePlus"):
            observed = summaries[key][metric]
            pvalues[key+":"+metric] = (1+sum(r[metric] >= observed for r in reference))/(1+len(reference))
    adjusted = holm_adjust(pvalues)
    for key, summary in summaries.items():
        summary["expectedRandomHits"] = round(n*36/49, 3)
        summary["expectedRandomThreePlus"] = round(n*sum(probabilities[3:]), 3)
        if key != "uniform-control":
            summary["oneSidedMonteCarloP"] = {m: round(pvalues[key+":"+m], 5) for m in ("totalHits", "threePlus")}
            summary["holmAdjustedP"] = {m: round(adjusted[key+":"+m], 5) for m in ("totalHits", "threePlus")}
            summary["exploratorySignal"] = any(adjusted[key+":"+m] < config["familyAlpha"] for m in ("totalHits", "threePlus"))
    return {"version": 1, "config": config, "trainingDrawsBeforeFirstTest": start,
            "testStart": trace[0]["target"], "testEnd": trace[-1]["target"],
            "recencySourceSha256": source_hash, "methods": summaries,
            "hasDemonstratedPredictiveAdvantage": False,
            "limitations": ["Retrospective experiment on history already used in previous work; not independent prospective validation.",
                            "CDM is adapted to occurrence counts; not an exact reproduction of the original paper.",
                            "KNN uses one previous draw as a 49-component binary state; it is a specified implementation, not a clone of a commercial service.",
                            "Bayesian uniform-prior ranking equals historical hot-number ranking.",
                            "Holm covers only these six comparisons, not prior experiments or the wider method search.",
                            "Random reference assumes uniform independent 6/49 draws; historical data is not fully officially verified.",
                            "Only six main numbers are evaluated; no reintegro, payouts, or betting transactions."],
            "trace": trace}


def main():
    raw = (ROOT / "data/sorteos.json").read_bytes()
    config = json.loads(CONFIG.read_text())
    result = evaluate(json.loads(raw)["draws"], config)
    result["historicalDataSha256"] = hashlib.sha256(raw).hexdigest()
    trace = result.pop("trace")
    TRACE.write_text("".join(json.dumps(row, separators=(",", ":"))+"\n" for row in trace), encoding="utf-8")
    result["traceFile"] = "data/evaluacion-metodos-detalle.jsonl"
    result["activeStrategySha256"] = hashlib.sha256((ROOT / "data/reto-estrategia-v2.json").read_bytes()).hexdigest()
    DEST.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ("trace", "limitations", "config")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

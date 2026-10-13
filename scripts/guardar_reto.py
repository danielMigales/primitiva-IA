import json
import os
from datetime import datetime, timezone
from validar_reto import validate_prediction
from pathlib import Path

path = Path("data/reto-predictor.json")
existing = json.loads(path.read_text(encoding="utf-8"))
incoming = json.loads(os.environ["REGISTRO_JSON"])
records = incoming if isinstance(incoming, list) else incoming.get("predictions", [])
if not isinstance(records, list) or not records:
    raise ValueError("El JSON debe contener predicciones.")
draws = json.loads(Path("data/sorteos.json").read_text(encoding="utf-8"))["draws"]
last_draw = max(r["date"] for r in draws)
today = datetime.now(timezone.utc).date()
known = {r["target"]: r for r in existing["predictions"]}
added = 0
for record in records:
    validate_prediction(record, last_draw, today)
    target = record["target"]
    nums = record["nums"]
    created = record["created"]
    window = record["window"]
    history_until = record["historyUntil"]
    if target in known:
        if known[target]["nums"] != sorted(nums):
            raise ValueError("Ya existe otra combinación registrada para " + target)
        continue
    known[target] = {
        **record,
        "target": target,
        "nums": sorted(nums),
        "created": created,
        "window": window,
        "historyUntil": history_until,
        "githubRecordedAt": datetime.now(timezone.utc).isoformat()
    }
    added += 1
existing["predictions"] = sorted(known.values(), key=lambda r: r["target"])
path.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Predicciones nuevas: {added}; total: {len(known)}")

import json
import os
from datetime import date, datetime, timezone
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
    target = record.get("target")
    nums = record.get("nums")
    created = record.get("created")
    window = record.get("window")
    history_until = record.get("historyUntil")
    if not isinstance(target, str) or not isinstance(created, str) or not isinstance(history_until, str):
        raise ValueError("Faltan fechas obligatorias.")
    target_date = date.fromisoformat(target)
    created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
    if created_at.tzinfo is None:
        raise ValueError("Fecha de creación sin zona horaria.")
    if created_at.astimezone(timezone.utc).date() > today:
        raise ValueError("La fecha de creación está en el futuro.")
    if not (history_until < target and target > last_draw and created_at.date() <= target_date):
        raise ValueError("Solo se aceptan predicciones para sorteos aún no presentes en el histórico.")
    if not isinstance(nums, list) or len(nums) != 6 or any(type(n) is not int or not 1 <= n <= 49 for n in nums) or len(set(nums)) != 6:
        raise ValueError("Combinación inválida.")
    if type(window) is not int or window not in (5, 20, 100, 500, 1000, 99999):
        raise ValueError("Ventana histórica inválida.")
    if target in known:
        if known[target]["nums"] != sorted(nums):
            raise ValueError("Ya existe otra combinación registrada para " + target)
        continue
    known[target] = {
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

#!/usr/bin/env python3
"""Conserva el histórico y añade exclusivamente resultados oficiales verificables de SELAE."""
import datetime as dt
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

DEST = pathlib.Path(__file__).resolve().parent / "data" / "sorteos.json"
CUTOFF = dt.date(2000, 1, 1)
BASE_URL = "https://www.loteriasyapuestas.es/f/loterias/resultados/primitiva.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PrimitivaIA/1.0)", "Accept": "application/json,text/html;q=0.9,*/*;q=0.8"}

def valid(row):
    try:
        date = dt.date.fromisoformat(row["date"])
        nums = row["nums"]
        return date <= dt.date.today() and len(nums) == 6 and len(set(nums)) == 6 and all(type(n) is int and 1 <= n <= 49 for n in nums)
    except (KeyError, ValueError, TypeError):
        return False

def official(date):
    query = urllib.parse.urlencode({"game_id": "LAPR", "fecha_sorteo": date.strftime("%Y%m%d")})
    request = urllib.request.Request(BASE_URL + "?" + query, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=25) as response:
        raw = response.read(300000).decode("utf-8-sig")
    # No inferir combinaciones de HTML: solo aceptar una respuesta JSON con
    # fecha y combinación inequívocas. Ante cambios de formato, no escribir.
    try:
        obj = json.loads(raw)
    except ValueError:
        return None
    if isinstance(obj, list):
        candidates = obj
    elif isinstance(obj, dict):
        candidates = [obj]
    else:
        return None
    for item in candidates:
        if not isinstance(item, dict):
            continue
        stamp = str(item.get("fecha_sorteo", item.get("fecha", "")))
        if date.strftime("%Y%m%d") not in re.sub(r"\D", "", stamp) and date.isoformat() != stamp:
            continue
        combo = item.get("combinacion", item.get("combinacion_ganadora"))
        if isinstance(combo, str):
            parts = re.findall(r"\d+", combo)
        elif isinstance(combo, list):
            parts = combo
        else:
            continue
        if len(parts) != 6:
            continue
        try:
            nums = sorted(int(n) for n in parts)
        except (ValueError, TypeError):
            continue
        row = {"date": date.isoformat(), "nums": nums}
        # Reintegro: únicamente si SELAE devuelve un campo explícito válido.
        reintegro = item.get("reintegro")
        if type(reintegro) is int and 0 <= reintegro <= 9:
            row["reintegro"] = reintegro
        elif isinstance(reintegro, str) and re.fullmatch(r"[0-9]", reintegro.strip()):
            row["reintegro"] = int(reintegro.strip())
        if valid(row):
            return row
    return None

def main():
    if not DEST.exists():
        print("Histórico ausente: no se crea uno parcial", file=sys.stderr)
        return 1
    payload = json.loads(DEST.read_text(encoding="utf-8"))
    rows = payload.get("draws", [])
    if len(rows) < 2900 or not all(valid(r) and dt.date.fromisoformat(r["date"]) >= CUTOFF for r in rows):
        print("Histórico incompleto o inválido: actualización detenida", file=sys.stderr)
        return 1
    existing = {}
    for row in rows:
        date = row["date"]
        nums = sorted(row["nums"])
        if date in existing and existing[date]["nums"] != nums:
            print("Conflicto en histórico:", date, file=sys.stderr)
            return 1
        existing[date] = dict(row, nums=nums)
    if len(existing) != len(rows):
        print("Fechas duplicadas: revisión manual necesaria", file=sys.stderr)
        return 1
    today = dt.date.today()
    latest = dt.date.fromisoformat(max(existing))
    added = 0
    # Lunes, jueves y sábados; revisar una ventana reciente por retrasos.
    start = max(latest - dt.timedelta(days=7), today - dt.timedelta(days=35))
    for offset in range((today - start).days + 1):
        date = start + dt.timedelta(days=offset)
        if date.weekday() not in (0, 3, 5):
            continue
        try:
            row = official(date)
        except Exception as exc:
            print("SELAE no disponible para", date, str(exc)[:120], file=sys.stderr)
            continue
        if row is None:
            continue
        key = row["date"]
        if key in existing:
            if existing[key]["nums"] != row["nums"]:
                print("Conflicto con SELAE:", key, file=sys.stderr)
                return 1
        else:
            existing[key] = row
            added += 1
    if not added:
        print("Sin nuevos resultados oficiales verificables. Histórico intacto.")
        return 0
    payload["draws"] = [existing[key] for key in sorted(existing) if dt.date.fromisoformat(key) >= CUTOFF]
    payload["reintegro_coverage"] = dict(payload.get("reintegro_coverage", {}), with_reintegro=sum(isinstance(x.get("reintegro"), int) for x in payload["draws"]), total=len(payload["draws"]), partial=any("reintegro" not in x for x in payload["draws"]))
    payload["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    sources = payload.get("sources", [])
    payload["sources"] = list(dict.fromkeys(sources + ["SELAE: https://www.loteriasyapuestas.es/es/resultados/primitiva"]))
    DEST.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("Añadidos", added, "sorteos oficiales; total", len(existing))
    return 0

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Conserva el histórico y añade exclusivamente resultados oficiales verificables de SELAE."""
import datetime as dt
import hashlib
import io
import unicodedata
from pypdf import PdfReader
import json
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

DEST = pathlib.Path(__file__).resolve().parent / "data" / "sorteos.json"
CUTOFF = dt.date(2000, 1, 1)
BASE_URL = "https://www.loteriasyapuestas.es/f/loterias/documentos/La%20Primitiva/Notas%20de%20prensa/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PrimitivaIA/1.0)", "Accept": "application/pdf"}

def valid(row):
    try:
        date = dt.date.fromisoformat(row["date"])
        nums = row["nums"]
        return date <= dt.date.today() and len(nums) == 6 and len(set(nums)) == 6 and all(type(n) is int and 1 <= n <= 49 for n in nums)
    except (KeyError, ValueError, TypeError):
        return False

MONTHS = ("enero", "febrero", "marzo", "abril", "mayo", "junio",
          "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
DAYS = {0: "LUNES", 3: "JUEVES", 5: "SABADO"}


def official_urls(date):
    if date.weekday() not in DAYS:
        raise ValueError("Fecha fuera del calendario de La Primitiva")
    # SELAE uses both padded/unpadded dates and SÁBADO/SABADO in public
    # filenames. Only a missing document (404) permits the next convention.
    names = ["SÁBADO", "SABADO"] if date.weekday() == 5 else [DAYS[date.weekday()]]
    days = [f"{date.day:02d}", str(date.day)] if date.weekday() == 3 else [str(date.day), f"{date.day:02d}"]
    months = [str(date.month), f"{date.month:02d}"]
    urls = []
    for name in names:
        for day in dict.fromkeys(days):
            for month in dict.fromkeys(months):
                filename = f"NOTA_DE_PRENSA_LA_PRIMITIVA_{name}_{day}_{month}_{date.year % 100:02d}.pdf"
                urls.append(BASE_URL + urllib.parse.quote(filename))
    return list(dict.fromkeys(urls))


def official_url(date):
    return official_urls(date)[0]


def parse_official_pdf_text(text, target):
    # Parse only the dated headline and the unique winning-number block.
    # Ignore the prize table, Joker and all other numbers in the document.
    folded = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)).lower()
    marker = "la combinacion ganadora ha correspondido a los siguientes numeros:"
    if folded.count(marker) != 1 or "loteria primitiva" not in folded.split(marker)[0]:
        raise ValueError("Cabecera oficial de La Primitiva no identificada")
    header, body = folded.split(marker)
    dates = re.findall(r"(lunes|jueves|sabado)\s+dia\s+(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})", header)
    if len(dates) != 1:
        raise ValueError("Fecha del sorteo ambigua")
    weekday, day, month, year = dates[0]
    if month not in MONTHS:
        raise ValueError("Mes del sorteo desconocido")
    actual_date = dt.date(int(year), MONTHS.index(month)+1, int(day))
    if actual_date != target or DAYS.get(target.weekday(), "").lower() != weekday:
        raise ValueError("El PDF corresponde a otro sorteo")
    if "la recaudacion" not in body:
        raise ValueError("Bloque de resultados no delimitado")
    block = body.split("la recaudacion", 1)[0]
    if block.count("complementario") != 1 or block.count("reintegro") != 1:
        raise ValueError("Faltan etiquetas de complementario/reintegro")
    if not re.search(r"joker:\s*\d{7}", block):
        raise ValueError("Formato de Joker desconocido")
    block = re.sub(r"joker:\s*\d{7}", "", block)
    block = block.replace("complementario", " ").replace("reintegro", " ")
    if not re.fullmatch(r"[0-9\s\-]+", block):
        raise ValueError("Formato del bloque de números desconocido")
    numbers = [int(n) for n in re.findall(r"\d+", block)]
    if len(numbers) != 8:
        raise ValueError("No hay seis números, complementario y reintegro inequívocos")
    nums, complementario, reintegro = numbers[:6], numbers[6], numbers[7]
    row = {"date": target.isoformat(), "nums": sorted(nums), "reintegro": reintegro}
    if not valid(row) or not 1 <= complementario <= 49 or complementario in nums or not 0 <= reintegro <= 9:
        raise ValueError("Combinación oficial inválida")
    return row


def official(date):
    for url in official_urls(date):
        request = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                data = response.read(1500001)
                if urllib.parse.urlparse(response.url).hostname != "www.loteriasyapuestas.es":
                    raise ValueError("La fuente redirige fuera del dominio oficial de resultados")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                continue
            raise
        if len(data) > 1500000 or not data.startswith(b"%PDF-"):
            raise ValueError("La fuente no devolvió un PDF oficial válido")
        reader = PdfReader(io.BytesIO(data))
        if len(reader.pages) != 1:
            raise ValueError("Formato de nota oficial inesperado")
        row = parse_official_pdf_text(reader.pages[0].extract_text(extraction_mode="layout"), date)
        row.update(sourceUrl=url, sourceType="official-press-pdf", sourceSha256=hashlib.sha256(data).hexdigest())
        return row
    return None

def write_report(status, latest=None, checked=0, conflicts=None):
    report = {
        "version": 1, "checkedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": status, "latestHistoricalDate": latest,
        "officialResultsReceived": checked, "conflicts": conflicts or [],
        "sourceUrl": BASE_URL,
        "note": "Dated official SELAE press PDFs confirm the six numbers and reintegro; ambiguous documents or inaccessible sources never count as verification."
    }
    DEST.with_name("estado-actualizacion.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    if not DEST.exists():
        print("Histórico ausente: no se crea uno parcial", file=sys.stderr)
        write_report("invalid-history")
        return 1
    payload = json.loads(DEST.read_text(encoding="utf-8"))
    rows = payload.get("draws", [])
    if len(rows) < 2900 or not all(valid(r) and dt.date.fromisoformat(r["date"]) >= CUTOFF for r in rows):
        print("Histórico incompleto o inválido: actualización detenida", file=sys.stderr)
        write_report("invalid-history")
        return 1
    existing = {}
    for row in rows:
        date = row["date"]
        nums = sorted(row["nums"])
        if date in existing and existing[date]["nums"] != nums:
            print("Conflicto en histórico:", date, file=sys.stderr)
            write_report("invalid-history")
            return 1
        existing[date] = dict(row, nums=nums)
    if len(existing) != len(rows):
        print("Fechas duplicadas: revisión manual necesaria", file=sys.stderr)
        write_report("invalid-history")
        return 1
    verification_path = DEST.with_name("verificacion-sorteos.json")
    verification = json.loads(verification_path.read_text(encoding="utf-8")) if verification_path.exists() else {"version": 1, "draws": []}
    confirmed = {r["date"]: r for r in verification["draws"]}
    checked = 0
    today = dt.date.today()
    latest = dt.date.fromisoformat(max(existing))
    added = 0
    # Lunes, jueves y sábados; revisar una ventana reciente por retrasos.
    start = max(latest - dt.timedelta(days=10), today - dt.timedelta(days=35))
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
        checked += 1
        key = row["date"]
        if key in existing:
            if existing[key]["nums"] != row["nums"]:
                print("Conflicto con SELAE:", key, file=sys.stderr)
                write_report("conflict", max(existing), checked, [{"date": key, "field": "nums"}])
                return 1
            if "reintegro" in row and "reintegro" in existing[key] and row["reintegro"] != existing[key]["reintegro"]:
                print("Conflicto de reintegro con SELAE:", key, file=sys.stderr)
                write_report("conflict", max(existing), checked, [{"date": key, "field": "reintegro"}])
                return 1
        else:
            existing[key] = row
            added += 1
        confirmed[key] = dict(row, source="SELAE",
                              checkedAt=dt.datetime.now(dt.timezone.utc).isoformat(),
                              url=row.get("sourceUrl", official_url(date)))
    if checked:
        verification["draws"] = [confirmed[key] for key in sorted(confirmed)]
        verification_path.write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report("confirmed" if checked else "unavailable", max(existing), checked)
    if not added:
        print(f"Sin sorteos nuevos; cotejos oficiales: {checked}. Histórico intacto.")
        return 0
    payload["draws"] = [existing[key] for key in sorted(existing) if dt.date.fromisoformat(key) >= CUTOFF]
    payload["reintegro_coverage"] = dict(payload.get("reintegro_coverage", {}), with_reintegro=sum(isinstance(x.get("reintegro"), int) for x in payload["draws"]), total=len(payload["draws"]), partial=any("reintegro" not in x for x in payload["draws"]))
    payload["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    sources = payload.get("sources", [])
    payload["sources"] = list(dict.fromkeys(sources + ["SELAE: notas oficiales de prensa de La Primitiva"]))
    DEST.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("Añadidos", added, "sorteos oficiales; total", len(existing))
    return 0

if __name__ == "__main__":
    sys.exit(main())

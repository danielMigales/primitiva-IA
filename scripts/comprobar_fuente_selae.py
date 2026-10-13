"""Read-only probe of the official public draw search service."""
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
target = max(row["date"] for row in json.loads((ROOT / "data/sorteos.json").read_text())["draws"])
stamp = target.replace("-", "")
url = "https://www.loteriasyapuestas.es/servicios/buscadorSorteos?" + urllib.parse.urlencode({
    "game_id": "LAPR", "celebrados": "true", "fechaInicioInclusiva": stamp, "fechaFinInclusiva": stamp})
print("Official URL:", url, flush=True)
request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; PrimitivaIA/1.0)", "Accept": "application/json"})
try:
    with urllib.request.urlopen(request, timeout=25) as response:
        raw = response.read(500000).decode("utf-8-sig")
        print("Status:", response.status, "Content-Type:", response.headers.get("Content-Type"), "Final URL:", response.url)
        print("Response:", raw[:12000])
        parsed = json.loads(raw)
        if not isinstance(parsed, (list, dict)):
            raise ValueError("Unexpected JSON type")
        print("JSON_RECEIVED", flush=True)
except urllib.error.HTTPError as exc:
    print("HTTP_ERROR:", exc.code)
    print(exc.read(2000).decode("utf-8", errors="replace"))
    raise SystemExit(1)
except Exception as exc:
    print("SOURCE_UNAVAILABLE:", type(exc).__name__, str(exc)[:200])
    raise SystemExit(1)

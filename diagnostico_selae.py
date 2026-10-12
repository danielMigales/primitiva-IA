#!/usr/bin/env python3
"""Diagnóstico de acceso de GitHub Actions a páginas oficiales SELAE.
No modifica los datos ni usa servicios de terceros."""
import urllib.request
import urllib.error

URLS = [
    "https://www.loteriasyapuestas.es/es/resultados",
    "https://www.loteriasyapuestas.es/es/resultados/primitiva",
    "https://www.loteriasyapuestas.es/f/loterias/resultados/primitiva.html?game_id=LAPR&fecha_sorteo=20261010",
]
for url in URLS:
    print("\nComprobando:", url, flush=True)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            body = response.read(200000).decode("utf-8", errors="replace")
            print("HTTP:", response.status, "Tipo:", response.headers.get("Content-Type"))
            print("Contenido leído:", len(body), "caracteres")
            print("Contiene 'Primitiva':", "primitiva" in body.lower())
            print("Contiene fecha 10/10/2026:", "10/10/2026" in body)
    except urllib.error.HTTPError as e:
        print("HTTP:", e.code, e.reason)
    except Exception as e:
        print("Error:", type(e).__name__, str(e)[:160])
print("\nDiagnóstico terminado. Ningún dato ha sido modificado.")

#!/usr/bin/env python3
"""Comprueba si GitHub Actions puede acceder al resultado oficial de SELAE."""
import urllib.request
url = 'https://www.loteriasyapuestas.es/f/loterias/resultados/primitiva.html?game_id=LAPR&fecha_sorteo=20261010'
request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(request, timeout=25) as response:
    data = response.read()
    print('HTTP:', response.status)
    print('Bytes:', len(data))
    print(data[:500].decode('utf-8', errors='replace'))

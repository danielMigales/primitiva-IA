#!/usr/bin/env python3
"""Auditoría reanudable; nunca escribe el histórico ni las predicciones."""
import argparse
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import update_data as source


def fingerprint(row):
    return hashlib.sha256(json.dumps(row, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def structure(payload):
    rows = payload.get("draws", [])
    errors = []
    dates = collections.Counter(r.get("date") for r in rows)
    for row in rows:
        if not source.valid(row):
            errors.append({"date": row.get("date"), "field": "date/nums"})
        if "reintegro" in row and (type(row["reintegro"]) is not int or not 0 <= row["reintegro"] <= 9):
            errors.append({"date": row.get("date"), "field": "reintegro"})
    errors += [{"date": day, "field": "duplicate-date"} for day, n in dates.items() if n > 1]
    warnings = []
    coverage = payload.get("reintegro_coverage", {})
    actual = sum(type(r.get("reintegro")) is int and 0 <= r["reintegro"] <= 9 for r in rows)
    if coverage.get("total") != len(rows) or coverage.get("with_reintegro") != actual:
        warnings.append({"field": "reintegro_coverage", "declaredTotal": coverage.get("total"),
                         "actualTotal": len(rows), "declaredWithReintegro": coverage.get("with_reintegro"),
                         "actualWithReintegro": actual})
    return {"checked": len(rows), "errors": errors, "warnings": warnings,
            "note": "La validez interna no confirma el resultado ni que estén todos los sorteos del calendario."}


def compare(row, official):
    fields = []
    if sorted(row["nums"]) != official["nums"]:
        fields.append("nums")
    if "reintegro" in row and row["reintegro"] != official["reintegro"]:
        fields.append("reintegro")
    return fields


def trusted_proof(proof, row):
    return (proof.get("source") == "SELAE" and proof.get("sourceType") == "official-press-pdf"
            and proof.get("url", "").startswith(source.BASE_URL)
            and len(proof.get("sourceSha256", "")) == 64
            and source.valid(proof) and type(proof.get("reintegro")) is int
            and 0 <= proof["reintegro"] <= 9 and not compare(row, proof)
            and isinstance(proof.get("checkedAt"), str))


def audit(root=ROOT, limit=20, delay=0.5, fetch=source.official, dates=None, max_seconds=600):
    history = root / "data/sorteos.json"
    raw = history.read_bytes()
    payload = json.loads(raw)
    rows = payload.get("draws", [])
    internal = structure(payload)
    report_path = root / "data/auditoria-historico.json"
    old = json.loads(report_path.read_text()) if report_path.exists() else {}
    records = {r["date"]: r for r in old.get("draws", [])}
    proof_path = root / "data/verificacion-sorteos.json"
    verification = json.loads(proof_path.read_text()) if proof_path.exists() else {"version": 1, "draws": []}
    proofs = {r["date"]: r for r in verification["draws"]}
    kept = {}
    for row in rows:
        key = row["date"]
        prior = records.get(key, {})
        if prior.get("historyRowSha256") == fingerprint(row):
            kept[key] = prior
        if kept.get(key, {}).get("status") != "conflict" and trusted_proof(proofs.get(key, {}), row):
            kept[key] = dict(date=key, historyRowSha256=fingerprint(row),
                             status="matched" if "reintegro" in row else "numbers-only",
                             checkedAt=proofs[key]["checkedAt"], official=proofs[key])
    records = kept
    attempts = 0
    stopped = None
    started = time.monotonic()
    # Fail closed for malformed/duplicate records; do not make network requests.
    if not internal["errors"]:
        for row in sorted(rows, key=lambda r: r["date"], reverse=True):
            key = row["date"]
            if dates is not None and key not in dates:
                continue
            if dates is None and records.get(key, {}).get("status") in ("matched", "numbers-only", "conflict", "document-not-found"):
                continue
            if attempts >= limit or time.monotonic() - started >= max_seconds:
                break
            stamp = dt.datetime.now(dt.timezone.utc).isoformat()
            entry = dict(date=key, historyRowSha256=fingerprint(row), checkedAt=stamp)
            attempts += 1
            try:
                official = fetch(dt.date.fromisoformat(key))
                if official is None:
                    entry.update(status="document-not-found", attemptedUrls=source.official_urls(dt.date.fromisoformat(key)))
                else:
                    fields = compare(row, official)
                    entry.update(status="conflict" if fields else ("matched" if "reintegro" in row else "numbers-only"),
                                 official=official, conflictingFields=fields)
                    if not fields:
                        proofs[key] = dict(official, source="SELAE", checkedAt=stamp, url=official["sourceUrl"])
                    else:
                        proofs.pop(key, None)
            except Exception as exc:
                entry.update(status="source-error", error=type(exc).__name__ + ": " + str(exc)[:180])
                stopped = key
            records[key] = entry
            print(key, entry["status"], flush=True)
            if stopped:
                break  # No repeated attempts after access/format/network failures.
            if delay:
                time.sleep(delay)
    counts = collections.Counter(r["status"] for r in records.values())
    report = dict(version=1, checkedAt=dt.datetime.now(dt.timezone.utc).isoformat(),
                  historySha256=hashlib.sha256(raw).hexdigest(), total=len(rows), structural=internal,
                  summary={**dict(counts), "pending": len(rows)-len(records)},
                  attemptsThisRun=attempts, stoppedAt=stopped,
                  status="invalid-history" if internal["errors"] else ("source-error" if stopped else "in-progress" if len(records)<len(rows) else "reviewed"),
                  fullyVerified=not internal["errors"] and counts["matched"] == len(rows),
                  note="404 significa documento no localizado con las convenciones conocidas, no resultado falso. Conflictos y errores nunca se convierten en cotejos. El histórico se conserva intacto.",
                  draws=[records[k] for k in sorted(records)])
    # Guard against a concurrent local history edit before publishing proofs.
    if history.read_bytes() != raw:
        raise RuntimeError("El histórico cambió durante la auditoría; no se guardan cotejos")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    verification["draws"] = [proofs[k] for k in sorted(proofs)]
    proof_path.write_text(json.dumps(verification, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"total": report["total"], "summary": report["summary"], "fullyVerified": report["fullyVerified"]}), flush=True)
    return 1 if internal["errors"] or stopped or counts["conflict"] else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--max-seconds", type=int, default=600)
    parser.add_argument("--date", action="append", help="Revisar expresamente una fecha del histórico; se puede repetir")
    args = parser.parse_args()
    if not 0 <= args.limit <= 200:
        parser.error("--limit debe estar entre 0 y 200")
    if not 1 <= args.max_seconds <= 7200:
        parser.error("--max-seconds debe estar entre 1 y 7200")
    if args.date:
        known = {r["date"] for r in json.loads((ROOT / "data/sorteos.json").read_text())["draws"]}
        if any(day not in known for day in args.date):
            parser.error("Las fechas deben existir en el histórico")
    sys.exit(audit(limit=args.limit, dates=set(args.date) if args.date else None, max_seconds=args.max_seconds))

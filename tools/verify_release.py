#!/usr/bin/env python3
"""Las seis compuertas de publicación, en una sola orden.

`release-validate.yml` las corre paso a paso en cada PR. El refresco diario
necesita exactamente el mismo veredicto antes de comprometer nada. English
freshness and native-language completeness are separate operational truths:
missing ES/ZH translations are allowed only when both locale sets agree and the
stable native Story routes explicitly declare translation pending.

Salida 0 solo si las seis pasan.
"""
from __future__ import annotations
import hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LOCALES = ("es-419", "zh-Hans")
LOCALE_SLUG = {"es-419": "es", "zh-Hans": "zh-hans"}


def paso(nombre, fn):
    try:
        detalle = fn()
    except Exception as exc:
        print(f"FALLA  {nombre}: {exc}", file=sys.stderr)
        return False
    print(f"ok     {nombre}{f': {detalle}' if detalle else ''}")
    return True


def corre(*args):
    r = subprocess.run([sys.executable, *args], cwd=RAIZ, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise RuntimeError((r.stderr or r.stdout or "").strip()[-1500:])
    return None


def compilar():
    return corre("-m", "py_compile", "tools/apply_final_release.py", "tools/apply_curated_i18n.py")


def overlay():
    return corre("tools/build_final_release.py", "--check")


def recibo():
    return corre("tools/build_ready_receipt.py", "--check")


def ensamblar():
    pub = RAIZ / "publish"
    if pub.exists(): shutil.rmtree(pub)
    shutil.copytree(RAIZ / "site", pub)
    corre("tools/apply_final_release.py", "publish")
    h = json.loads((RAIZ / "release-overlay/final/manifest.json").read_text(encoding="utf-8"))["index_sha256"]
    corre("tools/apply_curated_i18n.py", "publish", h)
    return None


def identidad():
    root = RAIZ / "publish"
    frozen = json.loads((RAIZ / "release-overlay/final/manifest.json").read_text(encoding="utf-8"))
    i18n = json.loads((root / "data/i18n/manifest.json").read_text(encoding="utf-8"))
    texto = (root / "index.html").read_text(encoding="utf-8")
    digest = hashlib.sha256((root / "index.html").read_bytes()).hexdigest()
    m = re.search(r'<script id="fcmo-data" type="application/json">(.*?)</script>', texto, re.S)
    assert m, "el index publicado no trae el corpus canonico fcmo-data"
    registros = json.loads(m.group(1)).get("records") or []
    ids = {r["id"] for r in registros}
    assert registros, "el corpus canonico esta vacio"
    assert len(ids) == len(registros), "hay ids duplicados en el corpus canonico"
    assert i18n["canonical_index_sha256"] == frozen["index_sha256"], "el pack apunta a otro index congelado"
    assert digest == i18n["localized_index_sha256"], "el index publicado no es el que el pack declara"
    assert i18n["supported_locales"] == ["en", *LOCALES], "los idiomas soportados cambiaron"
    assert i18n["canonical_record_count"] == len(registros), "el pack cuenta otros registros"

    locale_ids = {}
    for loc in LOCALES:
        ui = json.loads((root / "data/i18n" / loc / "ui.json").read_text(encoding="utf-8"))
        assert ui["canonical_record_count"] == len(registros), f"{loc}: cuenta canonica distinta"
        trad = {}
        for part in sorted((root / "data/i18n" / loc).glob("part-*.json")):
            trad.update(json.loads(part.read_text(encoding="utf-8"))["records"])
        locale_ids[loc] = set(trad)
        sobran = sorted(set(trad) - ids)
        assert not sobran, f"{loc}: traducciones fuera del corpus {sobran[:5]}"
        for rid, rec in trad.items():
            vacios = [k for k in ("title", "summary", "why_it_matters") if not rec.get(k, "").strip()]
            assert not vacios, f"{loc}/{rid}: {vacios} sin traducir"
    assert locale_ids[LOCALES[0]] == locale_ids[LOCALES[1]], "ES/ZH tienen backlog distinto"
    pending = ids - locale_ids[LOCALES[0]]
    assert i18n.get("translated_record_count") == len(ids) - len(pending), "manifest traduce otra cantidad"
    assert i18n.get("pending_translation_count") == len(pending), "manifest reporta otro backlog"
    expected_state = "COMPLETE" if not pending else "DEGRADED_TRANSLATION_BACKLOG"
    assert i18n.get("translation_state") == expected_state, "manifest reporta otro estado de traduccion"
    for rid in sorted(pending):
        for loc in LOCALES:
            page = root / "news" / LOCALE_SLUG[loc] / f"{rid}.html"
            assert page.is_file(), f"{loc}/{rid}: falta ruta estable pending"
            pending_html = page.read_text(encoding="utf-8")
            assert 'data-translation-status="pending"' in pending_html, f"{loc}/{rid}: ruta no declara traduccion pendiente"
            assert f"/news/en/{rid}.html" in pending_html, f"{loc}/{rid}: falta enlace a ingles canonico"

    assert {p.stem for p in (root / "data/briefs").glob("FCMO-*.json")} == ids, "los briefs no cuadran"
    assert {p.stem for p in (root / "developments").glob("FCMO-*.html")} == ids, "las paginas no cuadran"
    assert len(list((root / "editions").glob("*.html"))) >= 3, "faltan ediciones"
    assert (root / "build-manifest.json").is_file(), "falta build-manifest.json"
    return f"{len(registros)} registros / {len(pending)} traducciones pendientes / {digest[:12]}"


def falla_cerrado():
    """Missing translation is allowed; false or out-of-corpus translation is not."""
    from tools.apply_curated_i18n import validate_curated_i18n
    reg = RAIZ / "regression"
    if reg.exists(): shutil.rmtree(reg)
    shutil.copytree(RAIZ / "site", reg)
    corre("tools/apply_final_release.py", "regression")
    # Corrupt one existing translated core field by making it identical to canonical
    # English. The validator must still fail closed against counterfeit translation.
    index_text = (reg / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<script id="fcmo-data" type="application/json">(.*?)</script>', index_text, re.S)
    canonical = {r["id"]: r for r in json.loads(m.group(1))["records"]}
    target_part = None; target_id = None
    for part in sorted((reg / "data/i18n/es-419").glob("part-*.json")):
        doc = json.loads(part.read_text(encoding="utf-8")); rows = doc.get("records") or {}
        if rows:
            target_part = part; target_id = next(iter(rows)); doc["records"][target_id]["title"] = canonical[target_id]["title"]
            part.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            break
    assert target_part and target_id, "regresion necesita al menos una traduccion existente"
    try:
        validate_curated_i18n(reg)
    except ValueError as exc:
        assert "unchanged canonical English" in str(exc), str(exc)[:500]
    else:
        raise AssertionError("el validador acepto una falsa traduccion inglesa")
    finally:
        shutil.rmtree(reg, ignore_errors=True)
    return "backlog permitido; falsa traduccion rechazada"


def main() -> int:
    sys.path.insert(0, str(RAIZ))
    compuertas = (("compilar herramientas", compilar), ("overlay contra su fuente", overlay),
                  ("recibo contra el arbol", recibo), ("ensamblar candidato", ensamblar),
                  ("identidad e idiomas", identidad), ("falla cerrado", falla_cerrado))
    ok = [paso(n, f) for n, f in compuertas]
    if all(ok):
        print(f"\nlas {len(ok)} compuertas pasan"); return 0
    print(f"\n{ok.count(False)} de {len(ok)} compuertas fallan", file=sys.stderr); return 1


if __name__ == "__main__": raise SystemExit(main())

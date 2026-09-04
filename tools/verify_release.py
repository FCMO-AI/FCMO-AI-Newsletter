#!/usr/bin/env python3
"""Las seis compuertas de publicación, en una sola orden.

`release-validate.yml` las corre paso a paso en cada PR. El refresco diario
necesita exactamente el mismo veredicto antes de comprometer nada, y repetir
seis bloques de YAML es la forma segura de que un día dejen de coincidir.

Salida 0 solo si las seis pasan.
"""
from __future__ import annotations
import hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LOCALES = ("es-419", "zh-Hans")


def paso(nombre, fn):
    try:
        detalle = fn()
    except Exception as exc:  # noqa: BLE001 - el veredicto es el codigo de salida
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
    if pub.exists():
        shutil.rmtree(pub)
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
    for loc in LOCALES:
        ui = json.loads((root / "data/i18n" / loc / "ui.json").read_text(encoding="utf-8"))
        assert ui["canonical_record_count"] == len(registros), f"{loc}: cuenta distinta"
        trad = {}
        for part in sorted((root / "data/i18n" / loc).glob("part-*.json")):
            trad.update(json.loads(part.read_text(encoding="utf-8"))["records"])
        faltan, sobran = sorted(ids - set(trad)), sorted(set(trad) - ids)
        assert not faltan and not sobran, f"{loc}: faltan {faltan[:5]} sobran {sobran[:5]}"
        for rid, rec in trad.items():
            vacios = [k for k in ("title", "summary", "why_it_matters") if not rec.get(k, "").strip()]
            assert not vacios, f"{loc}/{rid}: {vacios} sin traducir"
    assert {p.stem for p in (root / "data/briefs").glob("FCMO-*.json")} == ids, "los briefs no cuadran"
    assert {p.stem for p in (root / "developments").glob("FCMO-*.html")} == ids, "las paginas no cuadran"
    assert len(list((root / "editions").glob("*.html"))) >= 3, "faltan ediciones"
    assert (root / "build-manifest.json").is_file(), "falta build-manifest.json"
    return f"{len(registros)} registros / 3 idiomas / {digest[:12]}"


def falla_cerrado():
    from tools.apply_curated_i18n import validate_curated_i18n
    reg = RAIZ / "regression"
    if reg.exists():
        shutil.rmtree(reg)
    shutil.copytree(RAIZ / "site", reg)
    corre("tools/apply_final_release.py", "regression")
    idx = reg / "index.html"
    texto = idx.read_text(encoding="utf-8")
    m = re.search(r'(<script id="fcmo-data" type="application/json">)(.*?)(</script>)', texto, re.S)
    datos = json.loads(m.group(2))
    semilla = dict(datos["records"][0])
    semilla.update({"id": "FCMO-FFFFFFFFFFFF",
                    "title": "Synthetic untranslated publication-gate regression story",
                    "summary": "Fixture only.", "why_it_matters": "Fixture only."})
    datos["records"].append(semilla)
    nuevo = m.group(1) + json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + m.group(3)
    idx.write_text(texto[:m.start()] + nuevo + texto[m.end():], encoding="utf-8")
    try:
        validate_curated_i18n(reg)
    except ValueError as exc:
        assert "record IDs do not exactly match canonical corpus" in str(exc), str(exc)[:300]
        assert "FCMO-FFFFFFFFFFFF" in str(exc), str(exc)[:300]
    else:
        raise AssertionError("el validador acepto una historia sin traducir")
    finally:
        shutil.rmtree(reg, ignore_errors=True)
    return "una historia sin traducir se rechaza"


def main() -> int:
    sys.path.insert(0, str(RAIZ))
    compuertas = (("compilar herramientas", compilar), ("overlay contra su fuente", overlay),
                  ("recibo contra el arbol", recibo), ("ensamblar candidato", ensamblar),
                  ("identidad e idiomas", identidad), ("falla cerrado", falla_cerrado))
    ok = [paso(n, f) for n, f in compuertas]
    if all(ok):
        print(f"\nlas {len(ok)} compuertas pasan")
        return 0
    print(f"\n{ok.count(False)} de {len(ok)} compuertas fallan", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

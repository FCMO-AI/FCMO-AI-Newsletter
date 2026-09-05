#!/usr/bin/env python3
"""Ejercita el refresco diario con una historia nueva y ediciones ARB airlocked.

La pregunta sigue siendo la misma del oraculo original: **si manana ARB entrega
una historia nueva, sale publicada de punta a punta?** La diferencia arquitectonica
es deliberada: el test ya no inventa un traductor downstream. Simula exactamente
la nueva frontera de responsabilidad: el corpus trae la historia inglesa y los
deltas editoriales ES/ZH preparados upstream; Newsletter solo ingiere, valida,
compila y publica.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CORPUS = RAIZ / "_fixtures" / "corpus-2026-09-01"
NUEVA = "FCMO-0C0DE0000001"
EXCLUIR = {".git", "publish", "regression", "__pycache__", ".pytest_cache"}
IGNORAR = ("publish/", "regression/", "__pycache__/", ".pytest_cache/")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verificar_generador import con_historia_sintetica


def fila(corpus: Path, ident: str) -> dict:
    for linea in (corpus / "data/developments.jsonl").read_text(encoding="utf-8").splitlines():
        if linea.strip():
            row = json.loads(linea)
            if row.get("id") == ident:
                return row
    raise ValueError(f"{ident} no existe en el corpus sintetico")


def overlay_sintetico(row: dict, locale: str) -> dict:
    """Crea texto de prueba distinto del ingles sin alterar tokens verificables.

    No pretende evaluar calidad linguistica: esa responsabilidad es del agente ARB.
    Conserva literalmente el texto fuente y agrega una clausula nativa larga; asi
    cualquier numero/URL/ID del fixture permanece identico mientras el gate puede
    demostrar que no esta aceptando una copia byte-identica del ingles.
    """
    if locale == "es-419":
        sufijo = " — edición editorial en español para validar el flujo autónomo completo."
    else:
        sufijo = " — 这是用于验证自主三语发布流程的简体中文编辑说明，并确保所有数字、链接、标识和证据边界保持不变。"
    return {
        "title": str(row.get("title") or "") + sufijo,
        "summary": str(row.get("summary") or "") + sufijo,
        "why_it_matters": str(row.get("why_it_matters") or "") + sufijo,
    }


def inyecta_locales(corpus: Path) -> None:
    row = fila(corpus, NUEVA)
    for locale in ("es-419", "zh-Hans"):
        path = corpus / "data" / "locales" / locale / "records.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "schema": "fcmo-airlocked-locale-delta-v1",
            "locale": locale,
            "canonical_locale": "en",
            "records": {NUEVA: overlay_sintetico(row, locale)},
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def corre(cwd: Path, nombre: str, args: list[str]) -> bool:
    proc = subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    if proc.returncode:
        print(f"el refresco se rompe en «{nombre}» (salida {proc.returncode})", file=sys.stderr)
        print((proc.stderr or proc.stdout or "").strip()[-3000:], file=sys.stderr)
        return False
    print(f"ok  {nombre}")
    return True


def huellas(raiz: Path) -> dict[str, float]:
    return {p.relative_to(raiz).as_posix(): p.stat().st_mtime_ns
            for p in raiz.rglob("*") if p.is_file()}


def cambiados(antes: dict[str, float], despues: dict[str, float]) -> list[str]:
    movidos = [r for r in set(antes) | set(despues) if antes.get(r) != despues.get(r)]
    return [r for r in movidos if not any(r.startswith(x) or f"/{x}" in r for x in IGNORAR)]


def rutas_del_commit() -> list[str]:
    texto = (RAIZ / ".github/workflows/daily-refresh.yml").read_text(encoding="utf-8")
    linea = re.search(r"git add -A -- (.+)", texto)
    if not linea:
        raise SystemExit("daily-refresh.yml no trae un `git add -A --` que leer")
    return linea.group(1).split()


def cubierto(ruta: str, rutas: list[str]) -> bool:
    return any(ruta == r or ruta.startswith(r.rstrip("/") + "/") for r in rutas)


def ignorados_por_git(rutas: list[str]) -> set[str]:
    if not rutas:
        return set()
    proc = subprocess.run(["git", "check-ignore", "--stdin"], cwd=RAIZ,
                          input="\n".join(rutas).encode("utf-8"), capture_output=True)
    return {line.strip() for line in proc.stdout.decode("utf-8", "replace").splitlines() if line.strip()}


def main() -> int:
    if not CORPUS.is_dir():
        print(f"falta el corpus {CORPUS.relative_to(RAIZ)}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="fcmo-refresco-") as tmp:
        banco = Path(tmp) / "repo"
        shutil.copytree(RAIZ, banco,
                        ignore=lambda _d, nombres: [n for n in nombres if n in EXCLUIR])
        corpus = Path(tmp) / "corpus-mas-una"
        con_historia_sintetica(CORPUS, corpus, NUEVA)
        inyecta_locales(corpus)
        antes = huellas(banco)

        pasos = (
            ("ingesta", ["tools/ingest_corpus.py", "--corpus", str(corpus), "--out", "release-src"]),
            ("locales airlocked", ["tools/sync_airlocked_locales.py", "--corpus", str(corpus)]),
            ("reconciliacion locale", ["tools/reconcile_locale_overlays.py", "--site", "release-src"]),
            ("integridad tres idiomas", ["tools/validate_localizations.py", "--site", "release-src"]),
            ("visual desk offline", ["tools/visual_desk.py", "--release-src", "release-src", "--site", "site", "--offline"]),
            ("story layer", ["tools/build_newsroom_surfaces.py", "--release-src", "release-src", "--site", "site"]),
            ("frontends", ["tools/build_editorial_frontends.py", "--site", "site"]),
            ("frontends final", ["tools/finalize_editorial_frontends.py", "--site", "site"]),
            ("overlay", ["tools/build_final_release.py"]),
            ("recibo", ["tools/build_ready_receipt.py"]),
            ("compuertas", ["tools/verify_release.py"]),
        )
        for nombre, args in pasos:
            if not corre(banco, nombre, args):
                return 1

        # Footnote: the workflow has a closed git-add boundary. Any generated file
        # outside it would make a locally green refresh fail to persist its own truth.
        movidos = cambiados(antes, huellas(banco))
        ignorados = ignorados_por_git(movidos)
        permitidas = rutas_del_commit()
        sin_comitear = sorted(r for r in movidos
                              if r not in ignorados and not cubierto(r, permitidas))
        if sin_comitear:
            print("el refresco escribe archivos que su commit no recoge:", file=sys.stderr)
            for ruta in sin_comitear[:20]:
                print("  -", ruta, file=sys.stderr)
            return 1

        pub = banco / "publish"
        if not pub.is_dir():
            print("las compuertas no dejaron candidato publish/", file=sys.stderr)
            return 1
        fallos: list[str] = []
        html = (pub / "index.html").read_text(encoding="utf-8")
        match = re.search(r'<script id="fcmo-data" type="application/json">(.*?)</script>', html, re.S)
        records = json.loads(match.group(1))["records"] if match else []
        if NUEVA not in {row["id"] for row in records}:
            fallos.append("la historia nueva no llego al corpus publicado")
        for rel in (
            f"developments/{NUEVA}.html", f"data/briefs/{NUEVA}.json",
            f"news/en/{NUEVA}.html", f"news/es/{NUEVA}.html", f"news/zh-hans/{NUEVA}.html",
        ):
            if not (pub / rel).is_file():
                fallos.append(f"falta {rel}")
        for locale in ("es-419", "zh-Hans"):
            native: dict = {}
            for part in sorted((pub / "data/i18n" / locale).glob("part-*.json")):
                native.update(json.loads(part.read_text(encoding="utf-8"))["records"])
            if NUEVA not in native:
                fallos.append(f"{locale}: la historia nueva no tiene edicion publicada")
        for rel in ("archive.html", "search.html", "topics.html", "organizations.html", "methodology.html", "status.html"):
            page = pub / rel
            if not page.is_file() or NUEVA not in page.read_text(encoding="utf-8", errors="replace") and rel == "archive.html":
                if rel == "archive.html":
                    fallos.append("archive.html no descubre la historia nueva")
                elif not page.is_file():
                    fallos.append(f"falta frontend {rel}")

        if fallos:
            print("el refresco corre pero no publica completamente la historia nueva", file=sys.stderr)
            for fallo in fallos:
                print("  -", fallo, file=sys.stderr)
            return 1

    print(f"\nrefresco OK: {len(records)} historias; nueva incluida en EN/ES/ZH y discovery")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

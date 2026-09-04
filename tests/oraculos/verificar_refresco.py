#!/usr/bin/env python3
"""El refresco diario, entero, sobre una copia limpia del repo.

Es la unica pregunta que importa de verdad: **si manana ARB entrega una historia
nueva, ¿sale publicada?** Las comprobaciones por pieza pueden estar todas en
verde y la respuesta seguir siendo no, porque el fallo vive en las costuras: una
cuenta anclada a mano en un manifiesto, un hash que nadie recalcula, un valor de
taxonomia que ningun pack traduce.

Corre lo mismo que `.github/workflows/daily-refresh.yml`, en el mismo orden, con
el motor `stub` en lugar de la credencial de Anthropic, sobre el corpus completo
de 23 historias. Verde aqui significa que la tuberia acepta contenido nuevo de
punta a punta; no dice nada sobre la calidad de la traduccion, que es cosa del
motor real.
"""
from __future__ import annotations
import json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CORPUS = RAIZ / "_fixtures" / "corpus-2026-09-01"
NUEVA = "FCMO-8AB23060CBF3"
EXCLUIR = {".git", "publish", "regression", "__pycache__", ".pytest_cache"}

PASOS = (
    ("ingesta", ["tools/ingest_corpus.py", "--corpus", "{corpus}", "--out", "release-src"]),
    ("traduccion", ["tools/translate_records.py", "--site", "release-src", "--engine", "stub", "--apply"]),
    ("overlay", ["tools/build_final_release.py"]),
    ("recibo", ["tools/build_ready_receipt.py"]),
    ("compuertas", ["tools/verify_release.py"]),
)


def copia_limpia(destino: Path) -> None:
    shutil.copytree(RAIZ, destino,
                    ignore=lambda _d, nombres: [n for n in nombres if n in EXCLUIR])


def main() -> int:
    if not CORPUS.is_dir():
        print(f"falta el corpus {CORPUS.relative_to(RAIZ)}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="fcmo-refresco-") as tmp:
        banco = Path(tmp) / "repo"
        copia_limpia(banco)

        for nombre, orden in PASOS:
            args = [a.format(corpus=str(CORPUS)) for a in orden]
            proc = subprocess.run([sys.executable, *args], cwd=banco,
                                  capture_output=True, text=True, encoding="utf-8", errors="replace")
            if proc.returncode:
                print(f"el refresco se rompe en «{nombre}» (salida {proc.returncode})", file=sys.stderr)
                print((proc.stderr or proc.stdout or "").strip()[-2500:], file=sys.stderr)
                return 1
            print(f"ok  {nombre}")

        # Y ademas: la historia nueva tiene que estar realmente publicada, en los
        # tres idiomas. Que la tuberia no reviente no es lo mismo que que sirva.
        pub = banco / "publish"
        if not pub.is_dir():
            print("las compuertas no dejaron el candidato en publish/", file=sys.stderr)
            return 1
        fallos: list[str] = []
        html = (pub / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<script id="fcmo-data" type="application/json">(.*?)</script>', html, re.S)
        recs = json.loads(m.group(1))["records"] if m else []
        if NUEVA not in {r["id"] for r in recs}:
            fallos.append(f"la historia nueva no esta en el sitio publicado ({len(recs)} registros)")
        for rel in (f"developments/{NUEVA}.html", f"data/briefs/{NUEVA}.json"):
            if not (pub / rel).is_file():
                fallos.append(f"falta {rel} en el sitio publicado")
        for loc in ("es-419", "zh-Hans"):
            trad: dict = {}
            for part in sorted((pub / "data/i18n" / loc).glob("part-*.json")):
                trad.update(json.loads(part.read_text(encoding="utf-8"))["records"])
            if NUEVA not in trad:
                fallos.append(f"{loc}: la historia nueva no tiene traduccion publicada")

        if fallos:
            print("el refresco corre pero no publica la historia nueva", file=sys.stderr)
            for f in fallos:
                print("  -", f, file=sys.stderr)
            return 1

    print(f"\nrefresco OK: {len(recs)} historias publicadas, la nueva incluida, en tres idiomas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

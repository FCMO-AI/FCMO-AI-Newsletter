#!/usr/bin/env python3
"""Comprueba que FCMO-8AB23060CBF3 quedo traducido de verdad en los dos idiomas.

La pregunta no es "hay algo escrito" sino "es una traduccion". Dos trampas que
este oraculo cierra: dejar el ingles tal cual (copiar es lo mas barato) y dejar
los marcadores del motor `stub`, que rellenan la estructura sin traducir nada.

La forma la decide la herramienta, no el traductor: se regenera con `--engine
stub` sobre una copia limpia y se exige que la entrada publicada tenga
exactamente la misma estructura de claves y longitudes de lista.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
IDENT = "FCMO-8AB23060CBF3"
IDIOMAS = ("es-419", "zh-Hans")
TAXONOMIA = ("model_release", "peer_review_missing")


def registro(i18n: Path, locale: str) -> dict:
    for parte in sorted((i18n / locale).glob("part-*.json")):
        datos = json.loads(parte.read_text(encoding="utf-8"))
        if IDENT in datos.get("records", {}):
            return datos["records"][IDENT]
    raise AssertionError(f"{locale}: {IDENT} no aparece en ningun part-*.json")


def forma(valor):
    if isinstance(valor, dict):
        return {clave: forma(sub) for clave, sub in sorted(valor.items())}
    if isinstance(valor, list):
        return [forma(sub) for sub in valor]
    return type(valor).__name__


def hojas(valor, ruta="") -> list[tuple[str, str]]:
    if isinstance(valor, dict):
        return [par for c, s in valor.items() for par in hojas(s, f"{ruta}.{c}")]
    if isinstance(valor, list):
        return [par for i, s in enumerate(valor) for par in hojas(s, f"{ruta}[{i}]")]
    if isinstance(valor, str):
        return [(ruta, valor)]
    return []


def es_espanol(texto: str) -> bool:
    bajo = f" {texto.lower()} "
    if any(unicodedata.combining(c) or c in "\u00f1\u00bf\u00a1" for c in unicodedata.normalize("NFD", texto)):
        return True
    return any(p in bajo for p in (" que ", " para ", " los ", " las ", " del ", " con ", " una "))


def es_chino(texto: str) -> bool:
    cjk = sum(1 for c in texto if "\u4e00" <= c <= "\u9fff")
    return cjk >= max(4, len(texto) // 12)


COMPROBAR = {"es-419": es_espanol, "zh-Hans": es_chino}


def main() -> int:
    i18n = RAIZ / "site" / "data" / "i18n"
    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp) / "repo"
        shutil.copytree(RAIZ, copia, ignore=shutil.ignore_patterns(".git", "publish", "regression", "__pycache__"))
        for locale in IDIOMAS:
            for parte in sorted((copia / "site/data/i18n" / locale).glob("part-*.json")):
                datos = json.loads(parte.read_text(encoding="utf-8"))
                if datos.get("records", {}).pop(IDENT, None) is not None:
                    parte.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        hecho = subprocess.run(
            [sys.executable, "tools/translate_records.py", "--apply", "--engine", "stub"],
            cwd=copia, capture_output=True, text=True,
        )
        if hecho.returncode != 0:
            print("no pude regenerar la forma de referencia:\n" + hecho.stderr)
            return 1
        referencia = {loc: registro(copia / "site/data/i18n", loc) for loc in IDIOMAS}

    ingles = json.loads((RAIZ / "release-src/data/briefs" / f"{IDENT}.json").read_text(encoding="utf-8"))
    fallos: list[str] = []

    for locale in IDIOMAS:
        try:
            publicado = registro(i18n, locale)
        except AssertionError as fallo:
            fallos.append(str(fallo))
            continue
        if forma(publicado) != forma(referencia[locale]):
            fallos.append(f"{locale}: la estructura no coincide con la que genera la herramienta")
            continue
        idioma_ok = COMPROBAR[locale]
        for ruta, texto in hojas(publicado):
            if "stub]" in texto:
                fallos.append(f"{locale}{ruta}: quedo un marcador del motor stub")
            elif not texto.strip():
                fallos.append(f"{locale}{ruta}: vacio")
            elif len(texto) > 24 and not idioma_ok(texto):
                fallos.append(f"{locale}{ruta}: no parece {locale} -> {texto[:70]}")
        for campo in ("title", "summary", "why_it_matters"):
            if publicado.get(campo) == ingles.get(campo):
                fallos.append(f"{locale}.{campo}: identico al ingles")

        catalogo = json.loads((i18n / locale / "ui.json").read_text(encoding="utf-8"))["ui"]
        for valor in TAXONOMIA:
            traducido = catalogo.get(valor)
            if not traducido:
                fallos.append(f"{locale}: falta la taxonomia '{valor}' en ui.json")
            elif traducido == valor or "stub]" in traducido:
                fallos.append(f"{locale}: la taxonomia '{valor}' sigue sin traducir")

    compuertas = subprocess.run([sys.executable, "tools/verify_release.py"], cwd=RAIZ, capture_output=True, text=True)
    if compuertas.returncode != 0:
        fallos.append("las compuertas de publicacion no pasan:\n" + (compuertas.stdout + compuertas.stderr)[-2000:])

    if fallos:
        print("\n".join(f"- {f}" for f in fallos))
        return 1
    print(f"traduccion de {IDENT} completa en {', '.join(IDIOMAS)}; las 6 compuertas pasan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

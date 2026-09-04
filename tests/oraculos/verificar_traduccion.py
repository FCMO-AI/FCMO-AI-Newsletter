#!/usr/bin/env python3
"""Cada historia publicada esta traducida de verdad en cada idioma curado.

La pregunta no es "hay algo escrito" sino "es una traduccion". Tres trampas que
este oraculo cierra: dejar el ingles tal cual -copiar es lo mas barato-, dejar
los marcadores del motor `stub`, que rellenan la estructura sin traducir nada, y
dejar una historia fuera del pack.

No se anclan identificadores: el universo lo dicta el corpus canonico del sitio,
asi que el oraculo sigue midiendo lo correcto cuando entren historias nuevas.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
IDIOMAS = ("es-419", "zh-Hans")

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from tools.apply_curated_i18n import _taxonomy_values


def registros_canonicos() -> dict[str, dict]:
    texto = (RAIZ / "release-src" / "index.html").read_text(encoding="utf-8")
    bloque = re.search(r'<script id="fcmo-data" type="application/json">(.*?)</script>', texto, re.S)
    if not bloque:
        raise SystemExit("release-src/index.html no trae el corpus canonico fcmo-data")
    return {fila["id"]: fila for fila in json.loads(bloque.group(1))["records"]}


def curados_por_id(i18n: Path, locale: str) -> dict[str, dict]:
    curados: dict[str, dict] = {}
    for parte in sorted((i18n / locale).glob("part-*.json")):
        curados.update(json.loads(parte.read_text(encoding="utf-8")).get("records", {}))
    return curados


def valores_de_taxonomia(canonicos: dict[str, dict]) -> list[str]:
    return sorted(_taxonomy_values(canonicos))


def fuente_de(canonicos: dict[str, dict], ident: str, ruta: str):
    """El valor ingles que corresponde a una hoja del pack curado."""
    actual = canonicos.get(ident)
    for tramo in re.findall(r"\.([^.\[\]]+)|\[(\d+)\]", ruta):
        clave, indice = tramo
        try:
            actual = actual[clave] if clave else actual[int(indice)]
        except (KeyError, IndexError, TypeError):
            return ""
    return actual if isinstance(actual, str) else ""


def hojas(valor, ruta="") -> list[tuple[str, str]]:
    if isinstance(valor, dict):
        return [par for c, s in valor.items() for par in hojas(s, f"{ruta}.{c}")]
    if isinstance(valor, list):
        return [par for i, s in enumerate(valor) for par in hojas(s, f"{ruta}[{i}]")]
    if isinstance(valor, str):
        return [(ruta, valor)]
    return []


def es_espanol(texto: str) -> bool:
    if any(unicodedata.combining(c) or c in "\u00f1\u00bf\u00a1"
           for c in unicodedata.normalize("NFD", texto)):
        return True
    bajo = f" {texto.lower()} "
    return any(p in bajo for p in (
        " que ", " para ", " los ", " las ", " del ", " con ", " una ", " de ",
        " el ", " la ", " en ", " y ", " un ", " por ", " se ", " no ", " es ",
        " al ", " lo ", " su ", " sus ", " sin ", " entre ", " sobre "))


def es_chino(texto: str) -> bool:
    cjk = sum(1 for c in texto if "\u4e00" <= c <= "\u9fff")
    return cjk >= max(4, len(texto) // 12)


COMPROBAR = {"es-419": es_espanol, "zh-Hans": es_chino}


def main() -> int:
    # La consola de Windows es cp1252 y el informe trae chino.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    i18n = RAIZ / "site" / "data" / "i18n"
    canonicos = registros_canonicos()
    fallos: list[str] = []

    for locale in IDIOMAS:
        curados = curados_por_id(i18n, locale)
        faltan = sorted(set(canonicos) - set(curados))
        if faltan:
            fallos.append(f"{locale}: {len(faltan)} historias sin traduccion curada: "
                          + ", ".join(faltan[:6]))
        idioma_ok = COMPROBAR[locale]
        for ident, entrada in sorted(curados.items()):
            fuente = canonicos.get(ident) or {}
            for ruta, texto in hojas(entrada):
                if "stub]" in texto:
                    fallos.append(f"{locale} {ident}{ruta}: quedo un marcador del motor stub")
                elif not texto.strip() and str(fuente_de(canonicos, ident, ruta)).strip():
                    fallos.append(f"{locale} {ident}{ruta}: vacio, y el ingles no lo esta")
                elif len(texto) > 24 and not idioma_ok(texto):
                    fallos.append(f"{locale} {ident}{ruta}: no parece {locale} -> {texto[:70]}")
            for campo in ("title", "summary", "why_it_matters"):
                if campo in entrada and entrada[campo] == fuente.get(campo):
                    fallos.append(f"{locale} {ident}.{campo}: identico al ingles")

        catalogo = json.loads((i18n / locale / "ui.json").read_text(encoding="utf-8"))["ui"]
        for valor in valores_de_taxonomia(canonicos):
            traducido = catalogo.get(valor)
            if not traducido:
                fallos.append(f"{locale}: falta la taxonomia '{valor}' en ui.json")
            elif "stub]" in traducido:
                fallos.append(f"{locale}: la taxonomia '{valor}' sigue con marcador")

    compuertas = subprocess.run([sys.executable, "tools/verify_release.py"],
                                cwd=RAIZ, capture_output=True, text=True)
    if compuertas.returncode != 0:
        fallos.append("las compuertas de publicacion no pasan:\n"
                      + (compuertas.stdout + compuertas.stderr)[-2000:])

    if fallos:
        print("\n".join(f"- {f}" for f in fallos))
        return 1
    print(f"{len(canonicos)} historias traducidas en {', '.join(IDIOMAS)}; "
          "las 6 compuertas pasan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

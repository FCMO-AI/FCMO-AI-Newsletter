#!/usr/bin/env python3
"""Validate the production localization contract without demanding fake synchronicity.

English is canonical and may advance before native prose. Existing ES/ZH overlays
must still be real, non-stub, source-bound translations; missing Story overlays are
measured debt rendered as explicit pending pages by the production pipeline. UI
catalogues may fall back to canonical taxonomy identifiers instead of inventing a
translation for every newly discovered technical term.
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


def registros_canonicos() -> dict[str, dict]:
    texto = (RAIZ / "release-src" / "index.html").read_text(encoding="utf-8")
    bloque = re.search(r'<script id="fcmo-data" type="application/json">(.*?)</script>', texto, re.S)
    if not bloque:
        raise SystemExit("release-src/index.html no trae el corpus canonico fcmo-data")
    return {fila["id"]: fila for fila in json.loads(bloque.group(1))["records"]}


def curados_por_id(i18n: Path, locale: str) -> dict[str, dict]:
    curados: dict[str, dict] = {}
    for parte in sorted((i18n / locale).glob("part-*.json")):
        doc = json.loads(parte.read_text(encoding="utf-8"))
        if doc.get("schema") != "fcmo-curated-locale-part-v1" or doc.get("locale") != locale:
            raise ValueError(f"{parte}: metadata de locale invalida")
        overlap = set(curados) & set(doc.get("records") or {})
        if overlap:
            raise ValueError(f"{locale}: IDs duplicados entre partes: {sorted(overlap)[:6]}")
        curados.update(doc.get("records") or {})
    return curados


def fuente_de(canonicos: dict[str, dict], ident: str, ruta: str):
    actual = canonicos.get(ident)
    for tramo in re.findall(r"\.([^.[\]]+)|\[(\d+)\]", ruta):
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
    if any(unicodedata.combining(c) or c in "ñ¿¡" for c in unicodedata.normalize("NFD", texto)):
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
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    i18n = RAIZ / "site" / "data" / "i18n"
    canonicos = registros_canonicos()
    fallos: list[str] = []
    sets: dict[str, set[str]] = {}

    for locale in IDIOMAS:
        try:
            curados = curados_por_id(i18n, locale)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            fallos.append(str(exc)); continue
        sets[locale] = set(curados)
        extras = sorted(set(curados) - set(canonicos))
        if extras:
            fallos.append(f"{locale}: overlays para IDs fuera del corpus: {', '.join(extras[:6])}")
        idioma_ok = COMPROBAR[locale]
        for ident, entrada in sorted(curados.items()):
            fuente = canonicos.get(ident) or {}
            for ruta, texto in hojas(entrada):
                if "stub]" in texto:
                    fallos.append(f"{locale} {ident}{ruta}: quedo un marcador stub")
                elif not texto.strip() and str(fuente_de(canonicos, ident, ruta)).strip():
                    fallos.append(f"{locale} {ident}{ruta}: vacio frente a fuente no vacia")
                elif len(texto) > 24 and not idioma_ok(texto):
                    # URLs, model IDs and proper nouns can legitimately remain canonical.
                    if not re.search(r"https?://|^[A-Za-z0-9_.+:/-]+$", texto):
                        fallos.append(f"{locale} {ident}{ruta}: no parece {locale} -> {texto[:70]}")
            for campo in ("title", "summary", "why_it_matters"):
                if campo in entrada and entrada[campo] == fuente.get(campo):
                    fallos.append(f"{locale} {ident}.{campo}: identico al ingles")

        ui = i18n / locale / "ui.json"
        if not ui.is_file():
            fallos.append(f"{locale}: falta ui.json")
        else:
            catalogo = json.loads(ui.read_text(encoding="utf-8")).get("ui") or {}
            if any("stub]" in str(value) for value in catalogo.values()):
                fallos.append(f"{locale}: ui.json contiene marcador stub")

    # Current production requires synchronized *incoming* locale deltas. Historical
    # curated coverage may legitimately differ while debt is being retired, so the
    # stronger symmetry proof lives in newswire_bridge_partial_locales.py and its tests.
    partial = subprocess.run(
        [sys.executable, "tools/validate_localizations_partial.py", "--site", "release-src"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if partial.returncode:
        fallos.append("la compuerta parcial de locales no pasa:\n" + (partial.stdout + partial.stderr)[-2500:])

    gates = subprocess.run([sys.executable, "tools/verify_release.py"], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
    if gates.returncode:
        fallos.append("las compuertas de publicacion no pasan:\n" + (gates.stdout + gates.stderr)[-2500:])

    if fallos:
        print("\n".join(f"- {f}" for f in fallos))
        return 1
    localized = {locale: len(sets.get(locale, set())) for locale in IDIOMAS}
    pending = {locale: len(set(canonicos) - sets.get(locale, set())) for locale in IDIOMAS}
    print(f"localizacion de produccion OK: historias={len(canonicos)} curadas={localized} pendientes={pending}; sin prose inventada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

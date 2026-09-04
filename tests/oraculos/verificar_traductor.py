#!/usr/bin/env python3
"""El traductor tiene que fallar cerrado y llenar exactamente lo que falta.

Tres preguntas, ninguna de ellas contestable por el test que escriba el autor:

1. Sin credencial, ¿se detiene en vez de publicar un sitio a medio traducir?
2. ¿Sabe qué registros le faltan, comparado con lo que calculo yo aparte?
3. Con un motor de relleno determinista, ¿restituye de verdad lo que falta, con
   la misma forma de campos que las entradas que ya estaban, sin tocar el resto?
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TOOL = RAIZ / "tools" / "translate_records.py"
SITIO = RAIZ / "release-src"
I18N = RAIZ / "site" / "data" / "i18n"
LOCALES = ("es-419", "zh-Hans")


def corre(args, entorno=None, cwd=RAIZ):
    env = {**os.environ, **(entorno or {})}
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return subprocess.run([sys.executable, str(TOOL), *args], cwd=cwd, env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def ids_canonicos() -> set[str]:
    t = (SITIO / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<script id="fcmo-data" type="application/json">(.*?)</script>', t, re.S)
    return {r["id"] for r in json.loads(m.group(1))["records"]}


def ids_traducidos(raiz: Path, locale: str) -> set[str]:
    vistos: set[str] = set()
    for part in sorted((raiz / locale).glob("part-*.json")):
        vistos |= set(json.loads(part.read_text(encoding="utf-8"))["records"])
    return vistos


def main() -> int:
    if not TOOL.is_file():
        print(f"falta {TOOL.relative_to(RAIZ)}", file=sys.stderr)
        return 1
    fallos = []

    # 1. Sin credencial y con motor real: se detiene, con codigo propio y mensaje que la nombra.
    r = corre(["--site", str(SITIO), "--engine", "anthropic", "--apply"],
              {"ANTHROPIC_API_KEY": ""})
    if r.returncode != 2:
        fallos.append(f"sin credencial salio {r.returncode}, se esperaba 2")
    if "ANTHROPIC_API_KEY" not in (r.stderr + r.stdout):
        fallos.append("sin credencial no nombra ANTHROPIC_API_KEY")

    # 2. Sabe que le falta. Hoy no falta ninguno, asi que retiro tres a proposito
    #    sobre una copia: un oraculo que no puede ponerse en rojo no prueba nada.
    canonicos = sorted(ids_canonicos())
    retirados = set(canonicos[:3])
    with tempfile.TemporaryDirectory(prefix="fcmo-tr-falta-") as tmp:
        copia = Path(tmp) / "i18n"
        shutil.copytree(I18N, copia)
        for loc in LOCALES:
            for part in sorted((copia / loc).glob("part-*.json")):
                doc = json.loads(part.read_text(encoding="utf-8"))
                if not any(r in doc["records"] for r in retirados):
                    continue
                doc["records"] = {k: v for k, v in doc["records"].items() if k not in retirados}
                part.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8", newline="\n")
        r = corre(["--site", str(SITIO), "--i18n-dir", str(copia), "--dry-run", "--engine", "stub"])
        if r.returncode != 0:
            fallos.append(f"--dry-run salio {r.returncode}: {(r.stderr or r.stdout)[-400:]}")
        else:
            for rid in sorted(retirados):
                if rid not in r.stdout:
                    fallos.append(f"--dry-run no nombra el retirado {rid}")
            for rid in canonicos[3:]:
                if rid in r.stdout:
                    fallos.append(f"--dry-run nombra {rid}, que si esta traducido")

    # 3. Restituye lo que falta. Parte de una copia mutilada a proposito: sobre
    #    un pack ya completo, una herramienta que no escribe nada pasaria igual.
    with tempfile.TemporaryDirectory(prefix="fcmo-tr-") as tmp:
        copia = Path(tmp) / "i18n"
        shutil.copytree(I18N, copia)
        antes = {}   # (locale, id) -> entrada original, para los que NO retiro
        for loc in LOCALES:
            for part in sorted((copia / loc).glob("part-*.json")):
                doc = json.loads(part.read_text(encoding="utf-8"))
                for k, v in doc["records"].items():
                    if k not in retirados:
                        antes[(loc, k)] = v
                if not any(r in doc["records"] for r in retirados):
                    continue
                doc["records"] = {k: v for k, v in doc["records"].items() if k not in retirados}
                part.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8", newline="\n")
        for loc in LOCALES:
            ui_path = copia / loc / "ui.json"
            ui_doc = json.loads(ui_path.read_text(encoding="utf-8"))
            ui_doc["canonical_record_count"] = 999
            ui_path.write_text(json.dumps(ui_doc, ensure_ascii=False, indent=2) + chr(10),
                               encoding="utf-8", newline=chr(10))
        for loc in LOCALES:
            hueco = retirados - (ids_canonicos() - ids_traducidos(copia, loc))
            if hueco:
                fallos.append(f"{loc}: la mutilacion no dejo hueco en {sorted(hueco)}")

        r = corre(["--site", str(SITIO), "--i18n-dir", str(copia), "--engine", "stub", "--apply"])
        if r.returncode != 0:
            fallos.append(f"--apply con stub salio {r.returncode}: {(r.stderr or r.stdout)[-400:]}")
        else:
            for loc in LOCALES:
                falta = ids_canonicos() - ids_traducidos(copia, loc)
                if falta:
                    fallos.append(f"{loc}: quedaron {len(falta)} sin entrada tras --apply: {sorted(falta)[:3]}")
                    continue
                despues = {}
                for part in sorted((copia / loc).glob("part-*.json")):
                    despues.update(json.loads(part.read_text(encoding="utf-8"))["records"])
                # Lo restituido tiene la forma de lo que ya habia, no un esqueleto.
                forma = {frozenset(v) for k, v in antes.items() if k[0] == loc}
                for rid in sorted(retirados):
                    ent = despues[rid]
                    if frozenset(ent) not in forma:
                        fallos.append(f"{loc}/{rid}: campos {sorted(ent)} no coinciden con ninguna entrada existente")
                    vacios = [k for k in ("title", "summary", "why_it_matters")
                              if not str(ent.get(k, "")).strip()]
                    if vacios:
                        fallos.append(f"{loc}/{rid}: {vacios} vacios tras --apply")
                # Y no toco nada de lo que no le faltaba.
                tocados = [k for (l, k), v in antes.items() if l == loc and despues.get(k) != v]
                if tocados:
                    fallos.append(f"{loc}: reescribio {len(tocados)} entradas que ya estaban: {sorted(tocados)[:3]}")
            # De ui.json le corresponden tres cosas: las dos que la compuerta de
            # publicacion compara contra el corpus, y anadir al catalogo los
            # valores de taxonomia que falten. Nada mas, y del catalogo solo
            # anadir: reescribir una entrada existente seria retraducir.
            SUYAS = {"canonical_record_count", "canonical_source_sha256", "ui"}
            for loc in LOCALES:
                antes_ui = json.loads((I18N / loc / "ui.json").read_text(encoding="utf-8"))
                ahora_ui = json.loads((copia / loc / "ui.json").read_text(encoding="utf-8"))
                if ahora_ui.get("canonical_record_count") != len(canonicos):
                    fallos.append(f"{loc}: ui.json quedo en canonical_record_count="
                                  f"{ahora_ui.get('canonical_record_count')!r}, se esperaba {len(canonicos)}")
                otros = [k for k in set(antes_ui) | set(ahora_ui)
                         if k not in SUYAS and antes_ui.get(k) != ahora_ui.get(k)]
                if otros:
                    fallos.append(f"{loc}: el traductor toco {len(otros)} claves de ui.json "
                                  f"que no le corresponden: {sorted(otros)[:5]}")
                cat_antes, cat_ahora = antes_ui.get("ui") or {}, ahora_ui.get("ui") or {}
                pisadas = [k for k, v in cat_antes.items() if cat_ahora.get(k) != v]
                if pisadas:
                    fallos.append(f"{loc}: reescribio {len(pisadas)} entradas del catalogo que ya "
                                  f"estaban traducidas: {sorted(pisadas)[:5]}")

    if fallos:
        print("traductor NO conforme", file=sys.stderr)
        for f in fallos:
            print("  -", f, file=sys.stderr)
        return 1
    print("traductor OK: falla cerrado sin credencial, detecta lo que falta y llena los packs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

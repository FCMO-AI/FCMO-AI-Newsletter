#!/usr/bin/env python3
"""El generador tiene que hacer crecer el sitio, no reimprimir el de ayer.

`release-src/index.html` son 500 KB de render disenado a mano que el corpus de
ARB no produce ni contiene: la esclusa entrega datos y sus propias paginas, no
ese armazon. Asi que el generador **parte de `release-src/` y lo actualiza**;
leerlo es legitimo. Lo que no es legitimo es copiarlo.

Dos preguntas, y la segunda es la que importa:

A. Idempotencia. Con el corpus recortado a las mismas 22 historias que hay hoy
   en `release-src/`, la salida tiene que ser identica byte a byte: actualizar
   sin novedades no cambia nada.
B. Crecimiento en historias. Con el corpus completo -23 historias- la nueva
   tiene que aparecer en todas las superficies derivadas, con su dossier y su
   pagina armada como las otras, y las 22 viejas quedar intactas.
C. Crecimiento en ediciones. El sitio publica una edicion diaria, y es una
   superficie aparte: se puede incorporar una historia nueva y seguir sin
   publicar la edicion del dia.

A sola la pasa un `cp -a`, y de hecho la paso. B es la que dice si el refresco
diario refresca.
"""
from __future__ import annotations
import hashlib, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CORPUS_23 = RAIZ / "_fixtures" / "corpus-2026-09-01"
BASE = RAIZ / "release-src"
GENERADOR = RAIZ / "tools" / "ingest_corpus.py"
NUEVA = "FCMO-8AB23060CBF3"

# Donde tiene que asomar una historia nueva. Si alguna de estas superficies la
# ignora, hay un lector del sitio que nunca se entera de que existe.
SUPERFICIES = (
    "data/search.json", "data/search.jsonl", "data/developments.json",
    "data/developments.jsonl", "data/topics.json", "data/organizations.json",
    "data/media.json", "data/site-manifest.json", "llms.txt", "llms-full.txt",
    "agent.json", "feed.json", "feed.xml", "sitemap.xml",
)


def recorta(origen: Path, destino: Path, ident: str) -> None:
    """El corpus de 23 historias, menos una: el estado que produjo `release-src/`.

    Se deriva en vez de guardarse. Un segundo corpus en git seria 1.4 MB de casi
    lo mismo, y ademas un artefacto retocado a mano cuya relacion con el
    original habria que creerse. Asi la relacion es esta funcion.

    Las paginas estaticas de ARB -`index.html`, `topics.html`,
    `organizations.html`- se copian tal cual y siguen mencionando la historia
    recortada: no puedo re-renderizarlas sin la tuberia de ARB, y este generador
    no las consume. Si algun dia las consume, la comprobacion A se pondra en
    rojo, que es lo correcto.
    """
    shutil.copytree(origen, destino)

    for rel in ("data/developments.jsonl", "data/relationships.jsonl"):
        ruta = destino / rel
        filas = [l for l in ruta.read_text(encoding="utf-8").splitlines()
                 if l.strip() and ident not in l]
        ruta.write_text("\n".join(filas) + "\n", encoding="utf-8", newline="\n")

    ruta = destino / "data/search.json"
    crudo = ruta.read_text(encoding="utf-8")
    filas = [r for r in json.loads(crudo) if r.get("id") != ident]
    sangria = 2 if crudo.startswith("[\n  ") else None
    ruta.write_text(json.dumps(filas, ensure_ascii=False, indent=sangria)
                    + ("\n" if crudo.endswith("\n") else ""), encoding="utf-8", newline="\n")

    ruta = destino / "feed.json"
    doc = json.loads(ruta.read_text(encoding="utf-8"))
    doc["items"] = [i for i in doc["items"] if ident not in json.dumps(i)]
    ruta.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")

    ruta = destino / "feed.xml"
    bloques = re.split(r"(?=<entry>|<item>)", ruta.read_text(encoding="utf-8"))
    ruta.write_text("".join(b for b in bloques if ident not in b),
                    encoding="utf-8", newline="\n")

    ruta = destino / "build-manifest.json"

    def limpia(o):
        if isinstance(o, list):
            return [limpia(x) for x in o if ident not in json.dumps(x)]
        if isinstance(o, dict):
            return {k: limpia(v) for k, v in o.items() if ident not in k}
        return o

    ruta.write_text(json.dumps(limpia(json.loads(ruta.read_text(encoding="utf-8"))),
                               ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def arbol(raiz: Path) -> dict[str, str]:
    return {p.relative_to(raiz).as_posix(): sha(p) for p in sorted(raiz.rglob("*")) if p.is_file()}


def genera(corpus: Path, salida: Path) -> str:
    proc = subprocess.run(
        [sys.executable, str(GENERADOR), "--corpus", str(corpus), "--out", str(salida)],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode:
        return f"salio {proc.returncode}: {(proc.stderr or proc.stdout or '').strip()[-1200:]}"
    return "" if salida.is_dir() else f"no escribio {salida}"


def canonico(raiz: Path) -> dict:
    t = (raiz / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<script id="fcmo-data" type="application/json">(.*?)</script>', t, re.S)
    if not m:
        raise ValueError("el index generado no trae el corpus canonico fcmo-data")
    return json.loads(m.group(1))


def clases(html: str) -> set[str]:
    return set(re.findall(r'class="([^"]+)"', html))


def fila_fuente(corpus: Path, ident: str) -> dict | None:
    for linea in (corpus / "data" / "developments.jsonl").read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            continue
        fila = json.loads(linea)
        if fila.get("id") == ident:
            return fila
    return None


def main() -> int:
    for ruta, que in ((GENERADOR, "el generador"), (CORPUS_23, "el corpus completo"),
                      (BASE, "la base release-src")):
        if not ruta.exists():
            print(f"falta {que}: {ruta.relative_to(RAIZ)}", file=sys.stderr)
            return 1
    fallos: list[str] = []
    base = arbol(BASE)

    with tempfile.TemporaryDirectory(prefix="fcmo-gen-") as tmp:
        # A. Sin novedades, no cambia nada.
        corpus_22 = Path(tmp) / "corpus-22"
        recorta(CORPUS_23, corpus_22, NUEVA)
        s22 = Path(tmp) / "salida-22"
        err = genera(corpus_22, s22)
        if err:
            fallos.append(f"A: el generador {err}")
        else:
            obt = arbol(s22)
            grupos = (("faltan", sorted(set(base) - set(obt))),
                      ("sobran", sorted(set(obt) - set(base))),
                      ("difieren", sorted(k for k in set(obt) & set(base) if obt[k] != base[k])))
            for etiqueta, filas in grupos:
                if filas:
                    extra = f" ... y {len(filas) - 12} mas" if len(filas) > 12 else ""
                    fallos.append(f"A: {etiqueta} ({len(filas)}): {', '.join(filas[:12])}{extra}")

        # B. Con una historia nueva, el sitio crece.
        s23 = Path(tmp) / "salida-23"
        err = genera(CORPUS_23, s23)
        if err:
            fallos.append(f"B: el generador {err}")
        else:
            recs: list[dict] = []
            datos: dict = {}
            try:
                datos = canonico(s23)
                recs = datos["records"]
            except Exception as exc:
                fallos.append(f"B: {exc}")

            ids = [r["id"] for r in recs]
            if len(ids) != 23:
                fallos.append(f"B: el corpus canonico trae {len(ids)} registros, se esperaban 23")

            if NUEVA not in ids:
                fallos.append(f"B: {NUEVA} no entro al corpus canonico")
            else:
                # Contra la fuente, no contra si mismo: la fila cruda del corpus manda.
                fuente = fila_fuente(CORPUS_23, NUEVA) or {}
                nuevo = next(r for r in recs if r["id"] == NUEVA)
                viejo = next(r for r in recs if r["id"] != NUEVA)
                if set(nuevo) != set(viejo):
                    fallos.append(f"B: el registro nuevo tiene otros campos; sobran "
                                  f"{sorted(set(nuevo) - set(viejo))}, "
                                  f"faltan {sorted(set(viejo) - set(nuevo))}")
                discrepan = sorted(k for k, v in fuente.items() if k in nuevo and nuevo[k] != v)
                if discrepan:
                    fallos.append(f"B: el registro nuevo no respeta la fuente en {discrepan}")
                if NUEVA not in (datos.get("briefs") or {}):
                    fallos.append("B: la historia nueva no tiene entrada en fcmo-data.briefs")

            for rel in (f"data/briefs/{NUEVA}.json", f"developments/{NUEVA}.html"):
                if not (s23 / rel).is_file():
                    fallos.append(f"B: falta {rel}")

            pag = s23 / f"developments/{NUEVA}.html"
            if pag.is_file():
                otra = next(p for p in sorted((s23 / "developments").glob("FCMO-*.html"))
                            if p.name != pag.name)
                falta = clases(otra.read_text(encoding="utf-8")) - clases(pag.read_text(encoding="utf-8"))
                # Alguna clase depende del contenido; un hueco grande es otra cosa.
                if len(falta) > 6:
                    fallos.append(f"B: la pagina nueva no esta armada como las otras; le faltan "
                                  f"{len(falta)} clases, p.ej. {sorted(falta)[:6]}")

            ciegas = [rel for rel in SUPERFICIES
                      if not (s23 / rel).is_file()
                      or NUEVA not in (s23 / rel).read_text(encoding="utf-8")]
            if ciegas:
                fallos.append(f"B: {len(ciegas)} superficies ignoran la historia nueva: "
                              + ", ".join(ciegas))

            obt = arbol(s23)
            congeladas = ("data/briefs/", "developments/", "editions/", "data/editions/")
            movidas = [k for k in base if k.startswith(congeladas) and obt.get(k) != base[k]]
            if movidas:
                fallos.append(f"B: {len(movidas)} superficies de las 22 viejas cambiaron: "
                              + ", ".join(sorted(movidas)[:8]))

        # C. Las ediciones diarias tambien crecen. El sitio publica una por dia,
        #    y son una superficie aparte de las historias: un generador podria
        #    incorporar historias nuevas y seguir sin publicar la edicion de hoy.
        corpus_ed = Path(tmp) / "corpus-edicion"
        shutil.copytree(CORPUS_23, corpus_ed)
        base_ed = sorted((corpus_ed / "editions").glob("*.html"))[-1]
        nueva_ed = base_ed.with_name("2026-09-04.html")
        nueva_ed.write_text(base_ed.read_text(encoding="utf-8").replace(base_ed.stem, nueva_ed.stem),
                            encoding="utf-8", newline=chr(10))
        sed = Path(tmp) / "salida-edicion"
        err = genera(corpus_ed, sed)
        if err:
            fallos.append(f"C: el generador {err}")
        else:
            for rel in (f"editions/{nueva_ed.stem}.html", f"data/editions/{nueva_ed.stem}.json"):
                if not (sed / rel).is_file():
                    fallos.append(f"C: la edicion nueva no produjo {rel}")
            for rel in ("sitemap.xml", "index.html"):
                if nueva_ed.stem not in (sed / rel).read_text(encoding="utf-8"):
                    fallos.append(f"C: {rel} no enumera la edicion nueva")

    if fallos:
        print("el generador no cumple", file=sys.stderr)
        for f in fallos:
            print("  -", f, file=sys.stderr)
        return 1
    print(f"generador OK: idempotente sobre {len(base)} archivos; una historia nueva entra "
          f"en las {len(SUPERFICIES)} superficies sin mover las viejas, y una edicion nueva "
          f"se publica y se enumera")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

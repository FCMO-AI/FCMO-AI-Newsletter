#!/usr/bin/env python3
"""El generador tiene que hacer crecer el sitio, no reimprimir el de ayer.

`release-src/index.html` son 500 KB de render disenado a mano que el corpus de
ARB no produce ni contiene: la esclusa entrega datos y sus propias paginas, no
ese armazon. Asi que el generador **parte de `release-src/` y lo actualiza**;
leerlo es legitimo. Lo que no es legitimo es copiarlo.

Dos preguntas, y la segunda es la que importa:

A. Punto fijo. Aplicar el generador dos veces seguidas sobre el mismo corpus
   tiene que dar lo mismo que aplicarlo una: actualizar sin novedades no cambia
   nada. Se mide sobre un clon, no contra el repo, para que no caduque.
   No es una formalidad: una superficie que solo enumere "lo que llego hoy"
   pasa el crecimiento y falla aqui, porque manana pierde lo de ayer.
B. Crecimiento en historias. Se inyecta en el corpus una historia que
   `release-src/` no contiene y tiene que aparecer en todas las superficies
   derivadas, con su dossier y su pagina armada como las otras, y las que ya
   estaban quedar intactas. La historia se sintetiza en vez de tomarse del
   fixture: cada vez que una historia real se publica deja de ser nueva, y un
   oraculo anclado a un identificador concreto caduca con ella.
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
NUEVA = "FCMO-0C0DE0000001"   # no existe en el corpus: la inyecta el oraculo

# Dos tipos de superficie, y confundirlos lleva a pedir cosas incompatibles.
#
# ENUMERAN lista todas las historias del sitio: si una falta aqui, hay un lector
# que nunca se entera de que existe, hoy y siempre.
ENUMERAN = (
    "data/search.json", "data/search.jsonl", "data/developments.json",
    "data/developments.jsonl", "data/topics.json", "data/organizations.json",
    "data/media.json", "llms.txt", "llms-full.txt",
    "feed.json", "feed.xml", "sitemap.xml",
)

# ANUNCIAN dice que llego en esta corrida. `agent.json` es un contrato de
# descubrimiento -endpoints, esquemas, ejemplos- y no lleva catalogo de
# historias; `site-manifest.json` lo embebe. Su unica mencion a una historia es
# el aviso de recien llegada, asi que aqui lo correcto es lo contrario: tiene
# que nombrarla el dia que entra y dejar de nombrarla al siguiente.
ANUNCIAN = ("agent.json", "data/site-manifest.json")

SUPERFICIES = ENUMERAN + ANUNCIAN


def con_historia_sintetica(origen: Path, destino: Path, ident: str) -> None:
    """El corpus mas una historia que `release-src/` no puede contener.

    El generador solo lee `data/developments.jsonl`, `data/relationships.jsonl`
    y `editions/*.html`; una fila de mas en la primera es una historia nueva
    completa a sus ojos. Se clona la ultima fila real para que todos los campos
    sean plausibles y se le cambia la identidad.
    """
    shutil.copytree(origen, destino)
    ruta = destino / "data/developments.jsonl"
    filas = [l for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]
    clon = json.loads(filas[-1])
    crudo = filas[-1].replace(clon["id"], ident)
    fila = json.loads(crudo)
    fila["title"] = "Historia sintetica de control para el oraculo del generador"
    ruta.write_text("\n".join(filas + [json.dumps(fila, ensure_ascii=False)]) + "\n",
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
        # A. Punto fijo con una historia nueva de por medio: se ingiere dos
        #    veces el mismo corpus, en sitio y sobre un clon, que es como corre
        #    el refresco diario. La primera pasada la incorpora; la segunda ya
        #    la encuentra en su propia base. Si alguna superficie enumera solo
        #    "lo que llego hoy", la segunda pasada la pierde -manana el sitio
        #    olvida la historia de ayer- y ninguna comparacion contra el repo
        #    lo veria, porque las dos partes traerian el mismo olvido.
        corpus_mas = Path(tmp) / "corpus-mas-una"
        con_historia_sintetica(CORPUS_23, corpus_mas, NUEVA)
        clon = Path(tmp) / "clon"
        shutil.copytree(RAIZ, clon, ignore=shutil.ignore_patterns(
            ".git", "publish", "regression", "__pycache__", "_audit"))
        # La primera pasada anuncia la llegada y la segunda ya no tiene nada
        # que anunciar: el punto fijo esta entre la segunda y la tercera, no
        # entre la primera y la segunda. Compararlas seria pedirle al generador
        # que mintiera sobre lo que acaba de llegar.
        pasadas: dict[str, dict[str, str]] = {}
        for vuelta in ("primera", "segunda", "tercera"):
            proc = subprocess.run(
                [sys.executable, "tools/ingest_corpus.py",
                 "--corpus", str(corpus_mas), "--out", "release-src"],
                cwd=clon, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if proc.returncode:
                fallos.append(f"A: la {vuelta} pasada salio {proc.returncode}: "
                              + (proc.stderr or proc.stdout or "").strip()[-800:])
                break
            pasadas[vuelta] = arbol(clon / "release-src")
        if len(pasadas) == 3:
            segunda, tercera = pasadas["segunda"], pasadas["tercera"]
            movidas = sorted(k for k in set(segunda) | set(tercera)
                             if segunda.get(k) != tercera.get(k))
            if movidas:
                extra = f" ... y {len(movidas) - 12} mas" if len(movidas) > 12 else ""
                fallos.append(f"A: la tercera pasada sobre el mismo corpus movio "
                              f"{len(movidas)} archivos: {', '.join(movidas[:12])}{extra}")
            # Lo que se anuncia como recien llegado se recalcula cada corrida.
            # Si el generador lo hereda de la base en vez de reescribirlo, la
            # comparacion byte a byte no lo ve -las dos pasadas traen el mismo
            # valor rancio- y el sitio anuncia manana la historia de ayer.
            ciegas = [rel for rel in ENUMERAN
                      if not (clon / "release-src" / rel).is_file()
                      or NUEVA not in (clon / "release-src" / rel).read_text(encoding="utf-8")]
            if ciegas:
                fallos.append(f"A: tras repetir la ingesta, {len(ciegas)} superficies han "
                              f"olvidado la historia: " + ", ".join(ciegas))

            # Y al reves para las que anuncian: lo que se anuncia como recien
            # llegado se recalcula cada corrida. Si el generador lo hereda de su
            # propia salida, la comparacion byte a byte no lo ve -las dos
            # pasadas traen el mismo valor rancio- y el sitio anuncia manana la
            # historia de ayer.
            rancias = [rel for rel in ANUNCIAN
                       if NUEVA in (clon / "release-src" / rel).read_text(encoding="utf-8")]
            if rancias:
                fallos.append(f"A: {', '.join(rancias)} sigue anunciando la historia como "
                              f"recien llegada, y en esta pasada no llego ninguna")

        # A2. Lo publicado es lo que el generador produce hoy. Es la unica
        #     comprobacion que depende del arbol del repo, y la arregla
        #     regenerar `release-src/`, no tocar la herramienta.
        s22 = Path(tmp) / "salida-igual"
        err = genera(CORPUS_23, s22)
        if err:
            fallos.append(f"A2: el generador {err}")
        else:
            obt = arbol(s22)
            grupos = (("faltan", sorted(set(base) - set(obt))),
                      ("sobran", sorted(set(obt) - set(base))),
                      ("difieren", sorted(k for k in set(obt) & set(base) if obt[k] != base[k])))
            for etiqueta, filas in grupos:
                if filas:
                    extra = f" ... y {len(filas) - 12} mas" if len(filas) > 12 else ""
                    fallos.append(f"A2: {etiqueta} ({len(filas)}): {', '.join(filas[:12])}{extra}")

        # B. Con una historia nueva, el sitio crece.
        s23 = Path(tmp) / "salida-mas-una"
        err = genera(corpus_mas, s23)
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
            esperados = len(arbol(BASE / "data" / "briefs")) + 1
            if len(ids) != esperados:
                fallos.append(f"B: el corpus canonico trae {len(ids)} registros, "
                              f"se esperaban {esperados}")

            if NUEVA not in ids:
                fallos.append(f"B: {NUEVA} no entro al corpus canonico")
            else:
                # Contra la fuente, no contra si mismo: la fila cruda del corpus manda.
                fuente = fila_fuente(corpus_mas, NUEVA) or {}
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

            # La pagina de una historia es un salto a la ruta de la SPA, y el
            # idioma viaja en la query. Un salto que no la arrastre deja al
            # lector en la portada sin `?lang`, que entonces resuelve por el
            # idioma del navegador: eliges ingles, pulsas una historia, y el
            # sitio te contesta en otro idioma.
            salto = s23 / f"developments/{NUEVA}.html"
            if salto.is_file() and "location.search" not in salto.read_text(encoding="utf-8"):
                fallos.append("B: la pagina de la historia salta a la SPA sin conservar la "
                              "query, asi que pierde el idioma elegido")

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
                fallos.append(f"B: {len(movidas)} superficies de las historias ya publicadas cambiaron: "
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

"""Los oraculos del refresco diario, expuestos a la suite del repo.

Viven aqui y no en `_audit/` por una razon concreta: `_audit/` esta en
`.gitignore`, asi que nada de lo que hay dentro llega a CI. Un mecanismo que
solo se comprueba en la maquina de quien lo escribio se rompe en silencio.

Son lentos -cada uno arma el sitio entero una o dos veces-, y aun asi caben en
la validacion de un PR: es la unica forma de que un cambio en las herramientas
no rompa el refresco sin que nadie se entere hasta la manana siguiente.
"""
from __future__ import annotations
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORACULOS = Path(__file__).resolve().parent / "oraculos"


def corre(nombre: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(ORACULOS / nombre)], cwd=RAIZ,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class RefrescoDiario(unittest.TestCase):
    def afirma(self, nombre: str) -> None:
        r = corre(nombre)
        if r.returncode:
            self.fail(f"{nombre} salio {r.returncode}\n"
                      + (r.stdout or "") + "\n" + (r.stderr or ""))

    def test_generador_deriva_y_crece(self) -> None:
        # release-src is now a composed newsroom product: ingest owns the
        # canonical substrate while public-research/media are downstream layers.
        # The adapter preserves the original strong ingest oracle and tests the
        # composition boundary explicitly instead of weakening either layer.
        self.afirma("verificar_generador_newsroom.py")

    def test_todo_lo_publicado_tiene_ediciones_nativas(self) -> None:
        # Footnote: this oracle is deliberately provider-free. It checks that the
        # committed locale packs are complete and actually language-specific;
        # prose generation belongs upstream to the ARB publication agent.
        self.afirma("verificar_traduccion.py")

    def test_refresco_entero_publica_la_historia_nueva(self) -> None:
        self.afirma("verificar_refresco.py")


if __name__ == "__main__":
    unittest.main()

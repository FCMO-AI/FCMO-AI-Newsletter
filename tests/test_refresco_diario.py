"""Oraculos del refresco autonomo expuestos a la suite del repositorio.

Viven aqui y no en `_audit/` porque CI debe ejercerlos en cada cambio relevante.
Los tests distinguen tres propiedades: fixed-point del generador contra el corpus
actual, integridad honesta de locales parciales y una historia sintetica publicada
de punta a punta con el mismo contrato de localizacion que usa produccion.
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
            self.fail(f"{nombre} salio {r.returncode}\n" + (r.stdout or "") + "\n" + (r.stderr or ""))

    def test_generador_deriva_y_crece(self) -> None:
        self.afirma("verificar_generador_newsroom.py")

    def test_locales_publicados_son_honestos_y_deuda_es_explicita(self) -> None:
        self.afirma("verificar_traduccion.py")

    def test_refresco_entero_publica_la_historia_nueva(self) -> None:
        self.afirma("verificar_refresco_produccion.py")


if __name__ == "__main__":
    unittest.main()

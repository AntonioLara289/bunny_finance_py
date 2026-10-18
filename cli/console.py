"""Salida por consola: tablas, mensajes de estado y confirmaciones.

No importa Qt ni numpy, para que ``-nogui`` arranque rapido.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Sequence

from colorama import Fore, Style, init as _init_colorama

_init_colorama()

FALLOS: set[int] = set()


def preparar_consola() -> None:
    """Deja la salida en condiciones de no reventar nunca con datos del usuario.

    Si la salida va a un terminal se respeta su codificacion (en Windows suele
    ser cp1252, que cubre el espanol) y solo se relajan los errores. Si la
    salida esta redirigida a un archivo o a otro proceso se usa UTF-8, que es
    lo que espera quien consume el texto.
    """
    for flujo in (sys.stdout, sys.stderr):
        try:
            if flujo.isatty():
                flujo.reconfigure(errors="replace")
            else:
                flujo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):  # pragma: no cover
            pass


class Consola:
    def __init__(self, color: bool | None = None) -> None:
        self.color = self._detectar_color() if color is None else color

    @staticmethod
    def _detectar_color() -> bool:
        if os.environ.get("NO_COLOR"):
            return False
        if os.environ.get("FORCE_COLOR"):
            return True
        return bool(getattr(sys.stdout, "isatty", lambda: False)())

    # -- nucleo ----------------------------------------------------------- #
    def escribir(self, texto: str = "") -> None:
        print(texto)

    def _pintar(self, texto: str, *estilos: str) -> None:
        if not self.color:
            self.escribir(texto)
            return
        self.escribir("".join(estilos) + texto + Style.RESET_ALL)

    def titulo(self, texto: str) -> None:
        self._pintar(texto, Fore.CYAN, Style.BRIGHT)

    def ok(self, texto: str) -> None:
        self._pintar(f"OK   {texto}", Fore.GREEN)

    def aviso(self, texto: str) -> None:
        self._pintar(f"AVISO {texto}", Fore.YELLOW)

    def error(self, texto: str) -> None:
        self._pintar(f"ERROR {texto}", Fore.RED)

    def info(self, texto: str) -> None:
        self._pintar(texto, Fore.CYAN)

    def vacio(self, texto: str = "(sin resultados)") -> None:
        self._pintar(texto, Fore.YELLOW)

    def fallo(self, comando: str, codigo: int = 1) -> None:
        """Anota que un comando devolvio error, para el codigo de salida."""
        FALLOS.add(codigo)

    # -- tablas ----------------------------------------------------------- #
    @staticmethod
    def _soporta_unicode() -> bool:
        codificacion = getattr(sys.stdout, "encoding", None) or "ascii"
        try:
            "│─┌┐└┘".encode(codificacion)
        except (UnicodeEncodeError, LookupError):
            return False
        return True

    def tabla(self, cabeceras: Sequence[str], filas: Sequence[Sequence[Any]]) -> None:
        if not filas:
            self.vacio()
            return

        try:
            from prettytable import PrettyTable
        except ImportError:  # pragma: no cover - prettytable es dependencia fijada
            self._tabla_simple(cabeceras, filas)
            return

        tabla = PrettyTable()
        tabla.field_names = list(cabeceras)
        tabla.add_rows([[("" if v is None else str(v)) for v in fila] for fila in filas])
        tabla.align = "l"
        tabla.border = True

        # En una consola cp1252 los caracteres de caja se verian como "?",
        # asi que en ese caso se usa el estilo ASCII de siempre.
        if self._soporta_unicode():
            from prettytable import SINGLE_BORDER

            tabla.set_style(SINGLE_BORDER)
        else:
            from prettytable import DEFAULT

            tabla.set_style(DEFAULT)

        if self.color:
            from prettytable import MARKDOWN

            tabla.set_style(MARKDOWN)
            tabla.header = True

        self.escribir(str(tabla))

    def _tabla_simple(self, cabeceras: Sequence[str], filas: Sequence[Sequence[Any]]) -> None:
        columnas = [[str(cabeceras[i])] + [str(fila[i]) for fila in filas] for i in range(len(cabeceras))]
        anchos = [max(len(line) for line in columna) for columna in columnas]
        separador = "-+-".join("-" * ancho for ancho in anchos)
        self.escribir(" | ".join(cabeceras).ljust(sum(anchos) + 3 * len(anchos) - 1))
        self.escribir(separador)
        for indice in range(len(filas)):
            self.escribir(
                " | ".join(
                    str(filas[fila][columna]).ljust(anchos[columna])
                    for columna in range(len(cabeceras))
                )
            )

    # -- interaccion ------------------------------------------------------ #
    def confirmar(self, pregunta: str, por_defecto: bool = False) -> bool:
        marca = "S/n" if por_defecto else "s/N"
        while True:
            try:
                respuesta = input(f"{pregunta} [{marca}] ").strip().lower()
            except EOFError:
                return por_defecto
            if not respuesta:
                return por_defecto
            if respuesta in ("s", "si", "y", "yes", "1"):
                return True
            if respuesta in ("n", "no", "0"):
                return False
            self.aviso("Responde s o n.")

    def limpiar_pantalla(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")


def codigo_salida() -> int:
    return 1 if FALLOS else 0

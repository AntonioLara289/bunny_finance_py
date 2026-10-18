"""Arranque de la consola de Bunny Finance.

    py main.py -nogui                  -> REPL interactivo
    py main.py -nogui <comando> [...]  -> un comando y salir
    py main.py -nogui --listar         -> catalogo de comandos

El codigo de salida es 0 si todo fue bien y 1 si algun comando fallo, para que
se pueda encadenar en scripts.
"""

from __future__ import annotations

import shlex
import sys

from core.services import Core, ErrorServicio
from cli.commands import Invocacion, buscar, buscar_parecido, listar_comandos, separar_opciones
from cli.console import Consola, preparar_consola

VERSION = "1.0"

_CORE: Core | None = None


def nucleo() -> Core:
    """Instancia unica de :class:`Core`, creando el esquema si falta."""
    global _CORE
    if _CORE is None:
        _CORE = Core()
        _CORE.asegurar_esquema()
    return _CORE


def _crear_consola() -> Consola:
    preparar_consola()
    return Consola()


def _un_comando(argumentos: list[str], consola: Consola) -> int:
    comando = buscar(argumentos[0])
    if comando is None:
        consola.error(f"Comando desconocido: {argumentos[0]}")
        parecidos = buscar_parecido(argumentos[0])
        if parecidos:
            consola.aviso("Quizas quisiste decir: " + ", ".join(c.nombre for c in parecidos))
        else:
            consola.aviso("Usa 'ayuda' para ver la lista de comandos.")
        return 1

    posicionales, opciones = separar_opciones(argumentos[1:])
    invocacion = Invocacion(
        core=nucleo(),
        consola=consola,
        comando=comando,
        pos=posicionales,
        opc=opciones,
    )

    try:
        return int(comando.ejecutar(invocacion) or 0)
    except ErrorServicio as exc:
        consola.error(exc.mensaje)
        if comando.detalle:
            consola.escribir(f"  Uso: {comando.uso}")
        return exc.codigo
    except KeyboardInterrupt:
        consola.escribir("^C")
        return 130
    except Exception as exc:  # noqa: BLE001 - la consola no debe morir nunca
        consola.error(f"Fallo inesperado en '{comando.nombre}': {exc}")
        if "--depurar" in opciones:
            import traceback

            traceback.print_exc()
        else:
            consola.escribir("  Añade --depurar para ver la traza completa.")
        return 1


def main(argumentos: list[str] | None = None) -> int:
    """Punto de entrada desde ``main.py``, con las banderas globales ya filtradas."""
    from cli.repl import bienvenida_sin_interaccion

    if argumentos is None:
        argumentos = sys.argv[1:]

    consola = _crear_consola()

    if not argumentos:
        return bienvenida_sin_interaccion(nucleo(), consola, VERSION)

    if argumentos[0] in ("--listar", "-l", "--comandos"):
        listar_comandos(consola)
        return 0

    try:
        return _un_comando(shlex.split(" ".join(shlex.quote(a) for a in argumentos)), consola)
    except ValueError as exc:
        consola.error(f"Comandos mal formados: {exc}")
        return 1

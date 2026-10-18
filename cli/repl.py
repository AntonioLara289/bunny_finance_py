"""Bucle interactivo de la consola.

    py main.py -nogui

Permite encadenar comandos sin reabrir el proceso: el estado se mantiene
entre invocaciones. Ctrl+C cancela la linea actual; Ctrl+D o 'salir' termina.
"""

from __future__ import annotations

import shlex
import sys

from cli.commands import (
    ORDEN,
    Invocacion,
    buscar,
    buscar_parecido,
    listar_comandos,
    separar_opciones,
)
from cli.console import Consola
from core.services import ErrorServicio

PROMPT = "bunny> "

COMANDOS_SALIDA = {"salir", "exit", "quit"}

GRUPOS_CON_VALORES = {
    "asistir": "personas",
    "faltar": "personas",
    "desasistir": "personas",
    "sesion": "sesiones",
    "asistencia": "sesiones",
    "resumen": "sesiones",
    "exportar": "sesiones",
    "sesion-editar": "sesiones",
    "sesion-borrar": "sesiones",
    "limpiar-asistencias": "sesiones",
    "persona": "ids_personas",
    "persona-borrar": "ids_personas",
    "persona-nombre": "nombres_personas",
    "rostro": "ids_rostros",
    "rostro-borrar": "ids_rostros",
    "rostro-renombrar": "ids_rostros",
    "ajuste": "ajustes",
}

OPCIONES_CONOCIDAS = (
    "salida",
    "estatus",
    "conservar-asistencias",
    "solo-persona",
    "depurar",
)


def _cargar_readline() -> object | None:
    """Readline da historial y completador, pero no viene en Windows.

    Se intenta el modulo estandar y, si no, pyreadline3 (opcional). Sin ninguno
    de los dos el REPL funciona igual, solo que sin historial con flechas.
    """
    try:
        import readline  # type: ignore[import-not-found]

        return readline
    except ImportError:
        pass
    try:
        import pyreadline3 as pyreadline  # type: ignore[import-not-found]

        return pyreadline
    except ImportError:
        return None


class Completer:
    """Completa nombres de comandos y valores frecuentes del dominio."""

    def __init__(self, core: object) -> None:
        self.core = core
        nombres = {c.nombre for c in ORDEN}
        alias = {a for c in ORDEN for a in c.alias}
        self.nombres = sorted(nombres)
        self.todos = sorted(nombres | alias)

    def _valores(self, tipo: str) -> list[str]:
        personas = self.core.personas  # type: ignore[attr-defined]
        rostros = self.core.rostros  # type: ignore[attr-defined]
        sesiones = self.core.sesiones  # type: ignore[attr-defined]
        ajustes = self.core.ajustes  # type: ignore[attr-defined]

        if tipo == "personas":
            return [p.nombre for p in personas.listar()] + [
                str(r.id) for r in rostros.listar()
            ]
        if tipo == "nombres_personas":
            return [p.nombre for p in personas.listar()]
        if tipo == "ids_personas":
            return [str(p.id) for p in personas.listar()]
        if tipo == "ids_rostros":
            return [str(r.id) for r in rostros.listar()]
        if tipo == "sesiones":
            valores = [s.nombre for s in sesiones.listar()]
            valores += [str(s.id) for s in sesiones.listar()]
            return valores + ["activa", "todas"]
        if tipo == "ajustes":
            return list(ajustes.claves())
        return []

    def candidatos(self, texto: str) -> list[str]:
        texto = texto.lstrip()
        if not texto:
            return self.nombres

        partes = texto.split()
        if len(partes) == 1:
            return [n for n in self.todos if n.startswith(partes[0])]

        if partes[-1].startswith("--"):
            return [
                "--" + o for o in OPCIONES_CONOCIDAS if ("--" + o).startswith(partes[-1])
            ]

        comando = buscar(partes[0])
        if comando is None:
            return []

        tipo = GRUPOS_CON_VALORES.get(comando.nombre)
        if tipo is None:
            return []

        ultimo = partes[-1]
        return [v for v in self._valores(tipo) if v.lower().startswith(ultimo.lower())]

    def completar(self, texto: str, estado: int) -> str | None:
        try:
            candidatos = self.candidatos(texto)
        except Exception:
            return None
        if not candidatos:
            return None
        return candidatos[min(estado, len(candidatos) - 1)]


def banner(consola: Consola, version: str) -> None:
    from core.paths import BASE_DIR

    try:
        interactivo = sys.stdin.isatty()
    except (AttributeError, ValueError):  # pragma: no cover
        interactivo = False

    consola.titulo(f"Bunny Finance {version} - modo consola")
    consola.escribir(f"  Proyecto: {BASE_DIR}")
    consola.escribir(f"  Python  : {sys.version.split()[0]}")
    if not interactivo:
        consola.escribir("  Entrada: canalizada, se ejecutara linea a linea")
    consola.escribir()
    consola.escribir("Escribe 'ayuda' para ver los comandos, 'salir' para terminar.")
    consola.escribir()


def ejecutar_linea(linea: str, core: object, consola: Consola) -> int | None:
    """Ejecuta una linea de la consola.

    Devuelve None si no havia nada que hacer y un entero con el codigo de
    salida del comando (0 correcto, 1 error).
    """
    # posix=True para que los nombres entrecomillados se partan por espacios.
    # Las rutas de Windows con espacios tambien van entrecomilladas.
    try:
        argumentos = shlex.split(linea)
    except ValueError as exc:
        consola.error(f"No se pudo interpretar la linea: {exc}")
        return 1

    argumentos = [a for a in argumentos if a]
    if not argumentos:
        return None

    nombre = argumentos[0].lower()
    if nombre in COMANDOS_SALIDA:
        return 0

    comando = buscar(nombre)
    if comando is None:
        consola.error(f"Comando desconocido: {argumentos[0]}")
        parecidos = buscar_parecido(nombre)
        if parecidos:
            consola.aviso("Quizas quisiste decir: " + ", ".join(c.nombre for c in parecidos))
        else:
            consola.aviso("Escribe 'ayuda' para ver la lista de comandos.")
        return 1

    posicionales, opciones = separar_opciones(argumentos[1:])
    invocacion = Invocacion(
        core=core,
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
    except Exception as exc:  # noqa: BLE001 - la consola no debe morir nunca
        consola.error(f"Fallo inesperado en '{comando.nombre}': {exc}")
        if "--depurar" in opciones:
            import traceback

            traceback.print_exc()
        else:
            consola.escribir(
                "  Usa 'ayuda " + comando.nombre + "' para ver el uso, "
                "o '--depurar' para ver la traza."
            )
        return 1


def _es_interactivo() -> bool:
    try:
        return sys.stdin.isatty()
    except (AttributeError, ValueError):  # pragma: no cover
        return False


def bucle(core: object, consola: Consola, version: str = "1.0") -> int:
    banner(consola, version)

    readline = _cargar_readline()
    if readline is None:
        consola.aviso(
            "Sin modulo readline: no habra historial con las flechas. "
            "Opcional: pip install pyreadline3"
        )
    else:
        try:
            readline.set_completer(Completer(core).completar)  # type: ignore[attr-defined]
            readline.set_completer_delims(" \t\n")  # type: ignore[attr-defined]
            readline.parse_and_bind("tab: complete")  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover
            pass

    codigo = 0
    while True:
        try:
            linea = input(PROMPT)
        except EOFError:
            consola.escribir()
            break
        except KeyboardInterrupt:
            consola.escribir("^C")
            continue

        if linea.strip().lower() in COMANDOS_SALIDA:
            consola.info("Hasta luego.")
            break

        try:
            resultado = ejecutar_linea(linea, core, consola)
        except KeyboardInterrupt:
            consola.escribir("^C")
            continue

        if resultado:
            codigo = resultado

    return codigo


def bienvenida_sin_interaccion(core: object, consola: Consola, version: str = "1.0") -> int:
    """Si la entrada es un terminal abre el REPL; si no, ejecuta linea a linea."""
    if _es_interactivo():
        return bucle(core, consola, version)

    banner(consola, version)
    codigo = 0
    for linea in sys.stdin:
        if linea.strip().lower() in COMANDOS_SALIDA:
            break
        resultado = ejecutar_linea(linea, core, consola)
        if resultado:
            codigo = resultado
    return codigo


__all__ = [
    "bucle",
    "ejecutar_linea",
    "bienvenida_sin_interaccion",
    "listar_comandos",
]

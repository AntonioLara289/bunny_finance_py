# main.py
import argparse
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# PySide6 y los widgets se importan dentro de main(), no aqui: en modo -nogui
# no hacen falta y el arranque de la consola es mucho mas rapido.


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=(
            "Bunny Finance - sistema de reconocimiento facial para control "
            "de asistencia financiera."
        ),
        epilog=(
            "Sin -nogui se abre la interfaz grafica. Con -nogui se controla "
            "todo desde la terminal."
        ),
    )
    grupo = parser.add_argument_group("consola")
    grupo.add_argument(
        "-nogui",
        "--nogui",
        dest="nogui",
        action="store_true",
        help="arranca la consola en vez de la interfaz grafica",
    )
    grupo.add_argument(
        "--listar",
        "-l",
        dest="listar",
        action="store_true",
        help="con -nogui, muestra el catalogo de comandos y sale",
    )
    return parser


def resolve_theme_path(theme_path: str, default_theme: str) -> str:
    """Convierte la ruta relativa de un tema en una ruta absoluta y existente.

    Evita depender del directorio de trabajo actual y cae al tema por defecto
    si el archivo guardado ya no esta en disco.
    """
    if not theme_path:
        return os.path.join(BASE_DIR, default_theme)

    candidate = theme_path if os.path.isabs(theme_path) else os.path.join(BASE_DIR, theme_path)
    if os.path.isfile(candidate):
        return candidate

    return os.path.join(BASE_DIR, default_theme)


def load_stylesheet(app, theme_path: str, default_theme: str) -> bool:
    """Aplica la hoja de estilos del tema indicado. Devuelve True si se aplico."""
    full_path = resolve_theme_path(theme_path, default_theme)

    if not os.path.isfile(full_path):
        print(f"[STYLE] No se encontro la hoja de estilo: {full_path}")
        return False

    try:
        with open(full_path, "r", encoding="utf-8") as fh:
            qss = fh.read().strip()
    except OSError as exc:
        print(f"[STYLE] No se pudo leer la hoja de estilo: {exc}")
        return False

    if not qss:
        print(f"[STYLE] La hoja de estilo esta vacia: {full_path}")
        return False

    app.setStyleSheet(qss)
    return True


def ejecutar_consola(argumentos: list[str]) -> int:
    """Modo terminal: REPL, o un unico comando si se paso alguno.

    No se crea QApplication ni se importa nada de Qt, asi que arranca al
    instante y funciona en una maquina sin pantalla.
    """
    if not BASE_DIR or BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)

    from cli.__main__ import main as consola_main

    return consola_main(argumentos)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    parser = construir_parser()
    opciones, resto = parser.parse_known_args(argv)

    if opciones.listar:
        return ejecutar_consola(["--listar"])

    if opciones.nogui:
        return ejecutar_consola(resto)

    if resto:
        print(f"[AVISO] Opcion desconocida, se ignora: {' '.join(resto)}")

    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from ui.app_settings import AppSettings, DEFAULT_THEME
    from ui.main_window import MainWindow

    app = QApplication([sys.argv[0]] + resto)
    app.setApplicationName("Bunny Finance")
    app.setApplicationDisplayName("Bunny Finance")
    app.setOrganizationName("BunnyFinance")

    settings = AppSettings()
    if not load_stylesheet(app, settings.theme_path, DEFAULT_THEME):
        load_stylesheet(app, DEFAULT_THEME, DEFAULT_THEME)

    def apply_style(path: str) -> None:
        load_stylesheet(app, path, DEFAULT_THEME)

    window = MainWindow(load_stylesheet_callback=apply_style)

    icon_path = os.path.join(BASE_DIR, "icon.png")
    if os.path.isfile(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    window.showMaximized()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

# main.py
import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.app_settings import AppSettings, DEFAULT_THEME
from ui.main_window import MainWindow

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def resolve_theme_path(theme_path: str) -> str:
    """Convierte la ruta relativa de un tema en una ruta absoluta y existente.

    Evita depender del directorio de trabajo actual y cae al tema por defecto
    si el archivo guardado ya no esta en disco.
    """
    if not theme_path:
        return os.path.join(BASE_DIR, DEFAULT_THEME)

    candidate = theme_path if os.path.isabs(theme_path) else os.path.join(BASE_DIR, theme_path)
    if os.path.isfile(candidate):
        return candidate

    return os.path.join(BASE_DIR, DEFAULT_THEME)


def load_stylesheet(app: QApplication, theme_path: str) -> bool:
    """Aplica la hoja de estilos del tema indicado. Devuelve True si se aplico."""
    full_path = resolve_theme_path(theme_path)

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


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Bunny Finance")
    app.setApplicationDisplayName("Bunny Finance")
    app.setOrganizationName("BunnyFinance")

    settings = AppSettings()
    if not load_stylesheet(app, settings.theme_path):
        load_stylesheet(app, DEFAULT_THEME)

    def apply_style(path: str) -> None:
        load_stylesheet(app, path)

    window = MainWindow(load_stylesheet_callback=apply_style)

    icon_path = os.path.join(BASE_DIR, "icon.png")
    if os.path.isfile(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    window.showMaximized()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

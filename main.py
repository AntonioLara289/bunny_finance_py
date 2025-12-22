# main.py
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from ui.main_window import MainWindow


def load_stylesheet(app: QApplication, filename: str) -> None:
    """Carga un archivo .qss y lo aplica a la aplicación."""
    import traceback

    try:
        # Mostrar la ruta absoluta para checar que el path sea correcto
        full_path = os.path.abspath(filename)
        print(f"[STYLE] Cargando stylesheet: {filename} -> {full_path}")

        if not os.path.exists(full_path):
            print(f"[WARN] No se encontró la hoja de estilo: {full_path}")
            return

        with open(full_path, "r", encoding="utf-8") as f:
            qss = f.read()

        if not qss.strip():
            print(f"[WARN] La hoja de estilo está vacía: {full_path}")
            return

        app.setStyleSheet(qss)
        print(f"[STYLE] Stylesheet aplicado correctamente: {full_path}")

    except Exception as e:
        print("[ERROR] Falló al cargar stylesheet:", e)
        traceback.print_exc()


def main() -> int:
    app = QApplication(sys.argv)

    # Estilo inicial
    load_stylesheet(app, "styles/aerofrost.qss")

    def apply_style(path: str) -> None:
        load_stylesheet(app, path)

    window = MainWindow(load_stylesheet_callback=apply_style)
    window.setWindowIcon(QIcon("icon.png"))
    window.showMaximized()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QAction
from ui.main_window import MainWindow
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QLabel,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QApplication,
    QCheckBox,
    QLabel,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QWidgetAction

)
import dlib

# Style loader
def load_stylesheet(app, filename):
    with open(filename, "r") as f:
        app.setStyleSheet(f.read())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_stylesheet(app, "styles/style.qss")

    window = MainWindow()
    
    window.setStatusBar(QStatusBar(window))

    menu = window.menuBar()

    file_menu = menu.addMenu("Opciones")

    window.BotonEscaneo(file_menu)
    window.BotonRegistro(file_menu)
    window.BotonConsultas(file_menu)
    window.BotonAsistencia(file_menu)
    window.BotonSalir(file_menu)

    style_menu = menu.addMenu("Estilos")
    #window.BotonAero(stlye_menu)
    #window.BotonAeroDark(stlye_menu)
    buttonAero = QAction("Aero", window)
    buttonAero.setStatusTip("Estilo Frutiger Aero")
    style_menu.addAction(buttonAero)
    buttonAero.triggered.connect(lambda: load_stylesheet(app, "styles/style.qss"))

    buttonAeroDark = QAction("Aero Dark", window)
    buttonAeroDark.setStatusTip("Estilo Frutiger Aero Dark")
    style_menu.addAction(buttonAeroDark)
    buttonAeroDark.triggered.connect(lambda: load_stylesheet(app, "styles/frutigerdark.qss"))

    about_menu = menu.addMenu("Acerca")

    window.resize(800, 600)
    window.showMaximized()
    window.show()

    sys.exit(app.exec())
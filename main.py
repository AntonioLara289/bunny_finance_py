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
from ui.animated_menu import AnimatedMenu

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

    # Opciones
    file_menu = AnimatedMenu("Opciones", window)
    menu.addMenu(file_menu)

    window.BotonAsistencia(file_menu)
    window.BotonEscaneo(file_menu)
    window.BotonRegistro(file_menu)
    window.BotonConsultas(file_menu)
    window.BotonSalir(file_menu)

    # Estilos
    style_menu = AnimatedMenu("Estilos", window)
    menu.addMenu(style_menu)

    buttonAero = QAction("Aero", window)
    buttonAero.setStatusTip("Estilo Frutiger Aero")
    style_menu.addAction(buttonAero)
    buttonAero.triggered.connect(lambda: load_stylesheet(app, "styles/style.qss"))

    buttonAeroDark = QAction("Aero Dark", window)
    buttonAeroDark.setStatusTip("Estilo Frutiger Aero Dark")
    style_menu.addAction(buttonAeroDark)
    buttonAeroDark.triggered.connect(lambda: load_stylesheet(app, "styles/frutigerdark.qss"))

    buttonAeroGreen = QAction("Aero Green", window)
    buttonAeroGreen.setStatusTip("Estilo Frutiger Aero verde")
    style_menu.addAction(buttonAeroGreen)
    buttonAeroGreen.triggered.connect(lambda: load_stylesheet(app, "styles/aerogreen.qss"))

    buttonAeroSunset = QAction("Aero Sunset", window)
    buttonAeroSunset.setStatusTip("Estilo Frutiger Aero sunset")
    style_menu.addAction(buttonAeroSunset)
    buttonAeroSunset.triggered.connect(lambda: load_stylesheet(app, "styles/aerosunset.qss"))

    buttonAeroFrost = QAction("Aero Frost", window)
    buttonAeroFrost.setStatusTip("Estilo Frutiger Aero Frost")
    style_menu.addAction(buttonAeroFrost)
    buttonAeroFrost.triggered.connect(lambda: load_stylesheet(app, "styles/aerofrost.qss"))

    buttonAeroOrganic = QAction("Aero Organic", window)
    buttonAeroOrganic.setStatusTip("Estilo Frutiger Aero Organic")
    style_menu.addAction(buttonAeroOrganic)
    buttonAeroOrganic.triggered.connect(lambda: load_stylesheet(app, "styles/aeroorganic.qss"))

    # Acerca
    about_menu = AnimatedMenu("Acerca", window)
    menu.addMenu(about_menu)

    window.resize(800, 600)
    window.showMaximized()
    window.show()

    sys.exit(app.exec())
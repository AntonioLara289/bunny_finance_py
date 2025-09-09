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

    button_action = QAction("Your button", window)
    button_action.setStatusTip("This is your button")
    
    window.setStatusBar(QStatusBar(window))

    menu = window.menuBar()

    file_menu = menu.addMenu("Opciones")
    file_menu.addAction(button_action)

    ##Acciones de los botones
    button_action.triggered.connect(window.toolbar_button_clicked)

    window.BotonEscaneo(file_menu)
    window.BotonRegistro(file_menu)
    window.BotonConsultas(file_menu)
    window.BotonSalir(file_menu)

    about_menu = menu.addMenu("Acerca")

    window.resize(800, 600)
    window.showMaximized()
    window.show()

    sys.exit(app.exec())
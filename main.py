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

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MainWindow()
    
    #Este es el antiguio toolbar
    # toolbar = QToolBar("My main toolbar")
    # window.addToolBar(toolbar)
    # window.setCentralWidget(window.stack)

    button_action = QAction("Your button", window)
    button_action.setStatusTip("This is your button")
    # toolbar.addAction(button_action)
    
    window.setStatusBar(QStatusBar(window))

    menu = window.menuBar()

    file_menu = menu.addMenu("Opciones")
    file_menu.addAction(button_action)

    ##Acciones de los botones
    button_action.triggered.connect(window.toolbar_button_clicked)

    buton_escaneo_rostro = window.inicializarBotonEscaneo(file_menu)
    buton_historial_registro = window.inicializarBotonRegistro(file_menu)

    window.resize(800, 600)
    window.showMaximized()
    window.show()
    # print("main.")

    sys.exit(app.exec())


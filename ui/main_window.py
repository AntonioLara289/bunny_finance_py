import sys
import random
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QLabel,
    QMainWindow,
    QStatusBar,
    QToolBar,
)
from PySide6.QtCore import Qt
from database.db_manager import DBManager
from ui.camera import CameraWidget
from ui.calculo import Calculo
from ui.escaneoRostro import EscanerRostro
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QLabel,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QWidgetAction
)


try:
    import cv2
    import face_recognition
    import mediapipe as mp

    print("OpenCV importado correctamente")
    print("face_recognition importado correctamente")
    print("MediaPipe importado correctamente")

    # Probar versiones (opcional)
    print("OpenCV versión:", cv2.__version__)
    print("MediaPipe versión:", mp.__version__)
    
    # Prueba mínima de funcionalidad
    mp_face_detection = mp.solutions.face_detection
    face_detector = mp_face_detection.FaceDetection()
    print("MediaPipe FaceDetection inicializado correctamente")

except ImportError as e:
    print("Error de importación:", e)
except Exception as e:
    print("Otro error:", e)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.stack = QtWidgets.QStackedWidget()
        label = QLabel("Hello!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setCentralWidget(label)

        toolbar = QToolBar("My main toolbar")
        self.addToolBar(toolbar)
        self.setCentralWidget(self.stack)

        button_action = QAction("Your button", self)
        button_action.setStatusTip("This is your button")
        button_action.triggered.connect(self.toolbar_button_clicked)
        toolbar.addAction(button_action)

        self.escaneoRostro = EscanerRostro()

        self.escaneoRostro.showMaximized()
        self.escaneoRostro.show()

        # self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир"]

        # self.button = QtWidgets.QPushButton("Click me!")
        # self.text = QtWidgets.QLabel("Hello World", alignment=QtCore.Qt.AlignCenter)
        # self.modal_button = QtWidgets.QPushButton("Iniciar Escaneo")
        # self.camera_switch = QtWidgets.QPushButton("Iniciar Escaneo")

        # self.layout = QtWidgets.QVBoxLayout(self)
        # # self.layout.addWidget(self.slider)
        # self.layout.addWidget(self.text)
        # self.layout.addWidget(self.button)
        # self.layout.addWidget(self.modal_button)
        # # self.layout.addWidget(self.switchCamera)

        # self.button.clicked.connect(self.magic)
        # self.modal_button.clicked.connect(self.mostrar_camara)
        # self.modal_button.clicked.connect(self.show_modal)
        # self.calculo()
        
        # self.switchCamera.clicked.connect(CameraWidget.switchCamera())


    def toolbar_button_clicked(self, s):
            print("click", s)

    def show_modal(self):
        pass
        # modal = QtWidgets.QDialog(self)
        # modal.setWindowTitle("Modal Dialog")
        # modal_layout = QtWidgets.QVBoxLayout(modal)
        # modal_label = QtWidgets.QLabel("This is a modal dialog", alignment=QtCore.Qt.AlignCenter)
        # close_button = QtWidgets.QPushButton("Close")
        # close_button.clicked.connect(modal.accept)
 
        # modal_layout.addWidget(modal_label)
        # modal_layout.addWidget(close_button)

        # modal.exec()

    @QtCore.Slot()

    def magic(self):
        self.text.setText(random.choice(self.hello))

    def mostrar_camara(self):
        self.cam_window = CameraWidget(self)
        modal = QtWidgets.QDialog(self)
        modal.setWindowTitle("Modal Dialog")
        modal_layout = QtWidgets.QVBoxLayout(modal)
        modal_label = QtWidgets.QLabel("This is a modal dialog", alignment=QtCore.Qt.AlignCenter)
        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(modal.accept)

        modal_layout.addWidget(modal_label)
        modal_layout.addWidget(close_button)

        modal.exec()

    def calculo(self):
        self.calculo_obj = Calculo()
        self.calculo_obj.signalCalculo.connect(self.recibir_calculo)
        self.calculo_obj.enviarCalculo()

    def recibir_calculo(self, valor):
        print("El cálculo recibido desde cámara es:", valor)
        # Aquí ya puedes guardarlo en una variable, mostrarlo en un QLabel, etc.
        self.text.setText(f"Cálculo: {valor}")
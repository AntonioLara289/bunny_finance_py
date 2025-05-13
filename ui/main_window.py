import sys
import random
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import Qt
from database.db_manager import DBManager
from ui.camera import CameraWidget

try:
    import cv2
    import face_recognition
    import mediapipe as mp

    print("✅ OpenCV importado correctamente")
    print("✅ face_recognition importado correctamente")
    print("✅ MediaPipe importado correctamente")

    # Probar versiones (opcional)
    print("OpenCV versión:", cv2.__version__)
    print("MediaPipe versión:", mp.__version__)
    
    # Prueba mínima de funcionalidad
    mp_face_detection = mp.solutions.face_detection
    face_detector = mp_face_detection.FaceDetection()
    print("✅ MediaPipe FaceDetection inicializado correctamente")

except ImportError as e:
    print("❌ Error de importación:", e)
except Exception as e:
    print("❌ Otro error:", e)


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир"]

        self.button = QtWidgets.QPushButton("Click me!")
        self.text = QtWidgets.QLabel("Hello World", alignment=QtCore.Qt.AlignCenter)
        self.modal_button = QtWidgets.QPushButton("Open Modal")

        self.layout = QtWidgets.QVBoxLayout(self)
        # self.layout.addWidget(self.slider)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.modal_button)

        self.button.clicked.connect(self.magic)
        self.modal_button.clicked.connect(self.mostrar_camara)

        self.db = DBManager()
        self.data = self.db.getBalances()

        if self.data:

            for fila in self.data:

                id_balance, balance, created_at = fila

                id = QtWidgets.QLabel(str(id_balance), alignment = QtCore.Qt.AlignCenter)

                # self.layout.addWidget(id)
                print(fila)

        else:

            print("No hay datos de balance")

        # print(self.data)

    def show_modal(self):
        modal = QtWidgets.QDialog(self)
        modal.setWindowTitle("Modal Dialog")
        modal_layout = QtWidgets.QVBoxLayout(modal)
        modal_label = QtWidgets.QLabel("This is a modal dialog", alignment=QtCore.Qt.AlignCenter)
        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(modal.accept)

        modal_layout.addWidget(modal_label)
        modal_layout.addWidget(close_button)

        modal.exec()

    @QtCore.Slot()
    def magic(self):
        self.text.setText(random.choice(self.hello))

    def mostrar_camara(self):
        self.cam_window = CameraWidget(self)
        self.cam_window.setWindowTitle("Cámara")
        self.cam_window.resize(640, 480)
        self.cam_window.show()
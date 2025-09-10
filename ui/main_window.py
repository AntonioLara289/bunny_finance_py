import sys
import random
from PySide6 import QtCore, QtWidgets
# from PySide6.QtCore import (
#     QSize, 
#     Qt
# )
from PySide6.QtGui import (
    QAction, 
    # QIcon,
    # QKeySequence,
    # QGuiApplication
)
# from PySide6.QtWidgets import (
#     QApplication,
#     QCheckBox,
#     QLabel,
#     QMainWindow,
#     QStatusBar,
#     QToolBar,
#     QApplication,
#     QCheckBox,
#     QLabel,
#     QMainWindow,
#     QStatusBar,
#     QToolBar,
#     QWidgetAction,
#     QScrollArea
# )
# from PySide6.QtCore import Qt
# from database.db_manager import DBManager
from ui.camera import CameraWidget
from ui.calculo import Calculo
from ui.escaneoRostro import EscanerRostro
from ui.Historial import Historial
try:
    # import cv2
    # import face_recognition
    import mediapipe as mp

    print("OpenCV importado correctamente")
    print("face_recognition importado correctamente")
    print("MediaPipe importado correctamente")

    # Probar versiones (opcional)
    # print("OpenCV versión:", cv2.__version__)
    # print("MediaPipe versión:", mp.__version__)
    
    # Prueba mínima de funcionalidad
    # mp_face_detection = mp.solutions.face_detection
    # face_detector = mp_face_detection.FaceDetection()
    print("MediaPipe FaceDetection inicializado correctamente")

except ImportError as e:
    print("Error de importación:", e)
except Exception as e:
    print("Otro error:", e)

class MainWindow(QtWidgets.QMainWindow):

    titulo_ventana = "Bunny Detect"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.titulo_ventana) # Set the initial window title
        self.setGeometry(100, 100, 400, 300) # (x, y, width, height)

        # StackedWidget como central
        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)


        # self.pantallaEscaneoRostro = EscanerRostro()
        self.pantallaMostrandose = EscanerRostro()

        # ******************************************************************************************************
        #Se tiene que conectar con la función onDestroy, desde ahora, todas las clases adicionales (pantallas)
        # deben tener la función onDestroy (aunque no tenga nada por realizar al cerrarse).
        
        # Verificar el objeto EscanerRostro para un ejemplo claro
        # ******************************************************************************************************
        self.pantallaMostrandose.destroyed.connect(self.pantallaMostrandose.onDestroy)

        # Agregar pantallas
        self.stack.addWidget(self.pantallaMostrandose)

        # Mostrar esa pantalla
        self.stack.setCurrentWidget(self.pantallaMostrandose)
        
        # self.setMaximumHeight(self.medidas_pantalla.height()) 

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

    def mostrarVistaHistorial(self):

        #Esto hace que la camara se libere en caso de que la pantalla anterior sea la de escaneo
        self.destroyActual()

        print("Mostrando la vista de historial")
        # Agregar pantallas
        self.pantallaMostrandose = Historial()
        self.stack.addWidget(self.pantallaMostrandose)

        # Mostrar esa pantalla
        self.stack.setCurrentWidget(self.pantallaMostrandose)


    def mostrarVistaEscaneo(self):

        self.destroyActual()

        print("Mostrando la vista de escaneo")
        # Agregar pantallas
        self.pantallaMostrandose = EscanerRostro()
        
        self.stack.addWidget(self.pantallaMostrandose)

        # Mostrar esa pantalla
        self.stack.setCurrentWidget(self.pantallaMostrandose)

    def inicializarBotonEscaneo(window, file_menu):
        button_escaneo_rostro = QAction("Escaneo De Rostro", window)
        button_escaneo_rostro.setStatusTip("Escaneo de rostro con cámara")
        
        # lo agregas al menú o toolbar
        file_menu.addAction(button_escaneo_rostro)

        # conectas la acción
        button_escaneo_rostro.triggered.connect(lambda: window.mostrarVistaEscaneo())
        return button_escaneo_rostro


    def inicializarBotonRegistro(window, file_menu):
        button_historial_registro = QAction("Historial de registro", window)
        button_historial_registro.setStatusTip("Historial de las detecciones")
        
        # lo agregas al menú o toolbar
        file_menu.addAction(button_historial_registro)

        # conectas la acción
        button_historial_registro.triggered.connect(lambda: window.mostrarVistaHistorial())
        return button_historial_registro


    def destroyActual(self):

        #Esto hace que la camara se libere en caso de que la pantalla anterior sea la de escaneo
        
        self.pantallaMostrandose.close()
        # self.stack.removeWidget(self.pantallaMostrandose)
        self.pantallaMostrandose.deleteLater()
        self.pantallaMostrandose = None
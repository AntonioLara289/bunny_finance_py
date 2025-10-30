import sys
import random
from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QAction
from ui.consultas import Consultas
from ui.asistencia import AsistenciaPantalla
from ui.camera import CameraWidget
from ui.calculo import Calculo
from ui.escaneoRostro import EscanerRostro
from ui.Historial import Historial

try:
    import mediapipe as mp
    print("OpenCV importado correctamente")
    print("face_recognition importado correctamente")
    print("MediaPipe importado correctamente")
    print("MediaPipe FaceDetection inicializado correctamente")
except ImportError as e:
    print("Error de importación:", e)
except Exception as e:
    print("Otro error:", e)


class MainWindow(QtWidgets.QMainWindow):

    titulo_ventana = "Bunny Detect"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.titulo_ventana)
        self.setGeometry(100, 100, 400, 300)

        # StackedWidget como central
        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        # Pantalla inicial
        self.pantallaMostrandose = EscanerRostro()
        self.stack.addWidget(self.pantallaMostrandose)
        self.stack.setCurrentWidget(self.pantallaMostrandose)

        # Conectar destroyed si existe onDestroy
        if hasattr(self.pantallaMostrandose, "onDestroy"):
            self.pantallaMostrandose.destroyed.connect(self.pantallaMostrandose.onDestroy)

    # ANIMACIÓN ENTRE VISTAS
    def animate_switch(self, new_widget):
        current = self.stack.currentWidget()
        new_widget.setGeometry(self.stack.geometry())

        self.stack.addWidget(new_widget)

        # --- Animación deslizante ---
        anim_slide = QtCore.QPropertyAnimation(new_widget, b"geometry")
        anim_slide.setDuration(300)
        anim_slide.setStartValue(self.stack.geometry().adjusted(self.width(), 0, self.width(), 0))
        anim_slide.setEndValue(self.stack.geometry())
        anim_slide.setEasingCurve(QtCore.QEasingCurve.OutCubic)

        # --- Animación de opacidad (fade) ---
        effect = QtWidgets.QGraphicsOpacityEffect(new_widget)
        new_widget.setGraphicsEffect(effect)
        anim_fade = QtCore.QPropertyAnimation(effect, b"opacity")
        anim_fade.setDuration(300)
        anim_fade.setStartValue(0)
        anim_fade.setEndValue(1)
        anim_fade.setEasingCurve(QtCore.QEasingCurve.OutCubic)

        # Iniciar ambas
        anim_slide.start()
        anim_fade.start()

        # Mantener referencias para que no se destruyan al terminar
        self._anim_slide = anim_slide
        self._anim_fade = anim_fade

        self.stack.setCurrentWidget(new_widget)

    # FUNCIONES DE CAMBIO DE VISTAS
    def mostrarVistaEscaneo(self):
        self.destroyActual()
        print("Mostrando la vista de escaneo")
        self.pantallaMostrandose = EscanerRostro()
        self.animate_switch(self.pantallaMostrandose)

    def mostrarVistaHistorial(self):
        self.destroyActual()
        print("Mostrando la vista de historial")
        self.pantallaMostrandose = Historial()
        self.animate_switch(self.pantallaMostrandose)

    def mostrarVistaConsultas(self):
        self.destroyActual()
        print("Mostrando vista Consultas")
        self.pantallaMostrandose = Consultas()
        self.animate_switch(self.pantallaMostrandose)

    def mostrarVistaAsistencia(self):
        self.destroyActual()
        print("Mostrando vista Asistencia")
        self.pantallaMostrandose = AsistenciaPantalla()
        self.animate_switch(self.pantallaMostrandose)

    def destroyActual(self):
        if self.pantallaMostrandose:
            try:
                self.pantallaMostrandose.close()
                self.pantallaMostrandose.deleteLater()
            except Exception:
                pass
        self.pantallaMostrandose = None

    def salir(self):
        self.destroyActual()
        QtWidgets.QApplication.quit()

    # FUNCIONES DE CÁLCULO Y MODAL
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

    # BOTONES DEL MENÚ
    def BotonEscaneo(window, file_menu):
        action = QAction("Registro de rostro", window)
        action.setStatusTip("Escaneo de rostro con cámara")
        file_menu.addAction(action)
        action.triggered.connect(lambda: window.mostrarVistaEscaneo())
        return action

    def BotonRegistro(window, file_menu):
        file_menu.addSeparator()
        action = QAction("Historial", window)
        action.setStatusTip("Historial de las detecciones")
        file_menu.addAction(action)
        action.triggered.connect(lambda: window.mostrarVistaHistorial())
        return action

    def BotonConsultas(window, file_menu):
        action = QAction("Consultas", window)
        action.setStatusTip("Consulta del registro de personas y estatus")
        file_menu.addAction(action)
        action.triggered.connect(lambda: window.mostrarVistaConsultas())
        return action

    def BotonAsistencia(window, file_menu):
        action = QAction("Asistencia", window)
        action.setStatusTip("Pantalla de toma de asistencia")
        file_menu.addAction(action)
        action.triggered.connect(lambda: window.mostrarVistaAsistencia())
        return action

    def BotonSalir(window, file_menu):
        file_menu.addSeparator()
        action = QAction("Salir", window)
        action.setStatusTip("Salir de aplicación")
        file_menu.addAction(action)
        action.triggered.connect(lambda: window.salir())
        return action

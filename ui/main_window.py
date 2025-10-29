import sys
import random
from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import (
    QAction
)
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
        3
    def mostrarVistaConsultas(self):
        #Esto hace que la camara se libere en caso de que la pantalla anterior sea la de escaneo
        self.destroyActual()
        
        print("Mostrando vista Consultas")
        # Agregar pantallas
        self.pantallaMostrandose = Consultas()
        self.stack.addWidget(self.pantallaMostrandose)

        # Mostrar esa pantalla
        self.stack.setCurrentWidget(self.pantallaMostrandose)

    def mostrarVistaAsistencia(self):
         #Esto hace que la camara se libere en caso de que la pantalla anterior sea la de escaneo
        self.pantallaMostrandose.destroy()
            
        print("Mostrando vista Asistencia")
        # Agregar pantallas
        self.pantalla = AsistenciaPantalla()
        self.stack.addWidget(self.pantalla)

        # Mostrar esa pantalla
        self.stack.setCurrentWidget(self.pantalla)
            
    def mostrarVistaEscaneo(self):

        self.destroyActual()

        print("Mostrando la vista de escaneo")
        # Agregar pantallas
        self.pantallaMostrandose = EscanerRostro()
        
        self.stack.addWidget(self.pantallaMostrandose)

        # Mostrar esa pantalla
        self.stack.setCurrentWidget(self.pantallaMostrandose)

    def salir(self):
        self.pantallaMostrandose.destroy()
        QtWidgets.QApplication.quit()

    # Botones para interfaz
    def BotonEscaneo(window, file_menu):
        button_escaneo_rostro = QAction("Registro de rostro", window)
        button_escaneo_rostro.setStatusTip("Escaneo de rostro con cámara")
        
        # lo agregas al menú o toolbar
        file_menu.addAction(button_escaneo_rostro)

        # conectas la acción
        button_escaneo_rostro.triggered.connect(lambda: window.mostrarVistaEscaneo())
        return button_escaneo_rostro

    def BotonRegistro(window, file_menu):
        file_menu.addSeparator()
        button_historial_registro = QAction("Historial", window)
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

    def BotonConsultas(window, file_menu):
        button_consulta_personas = QAction("Consultas", window)
        button_consulta_personas.setStatusTip("Consulta del registro de personas y estatus")
        
        # lo agregas al menú o toolbar
        file_menu.addAction(button_consulta_personas)

        # conectas la acción
        button_consulta_personas.triggered.connect(lambda: window.mostrarVistaConsultas())
        return button_consulta_personas

    def BotonAsistencia(window, file_menu):
        butoon_asistencia = QAction("Asistencia", window)
        butoon_asistencia.setStatusTip("Pantalla de toma e asistencia")
        
        # lo agregas al menú o toolbar
        file_menu.addAction(butoon_asistencia)

        # conectas la acción
        butoon_asistencia.triggered.connect(lambda: window.mostrarVistaAsistencia())
        return butoon_asistencia

    def BotonSalir(window, file_menu):
        file_menu.addSeparator()
        button_salir = QAction("Salir", window)
        button_salir.setStatusTip("Salir de aplicacion")
        
        # lo agregas al menú o toolbar
        file_menu.addAction(button_salir)

        # conectas la acción
        button_salir.triggered.connect(lambda: window.salir())
        return button_salir
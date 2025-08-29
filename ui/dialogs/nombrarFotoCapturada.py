from PySide6 import QtWidgets
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton
) 
from PySide6.QtCore import Qt
import os
import cv2
from database.db_manager import DBManager
import face_recognition
import json

class NombrarFotoCapturada(QDialog):

    def __init__(self, parent = None, data = None, imagen = None, encodigns = None):

        super(NombrarFotoCapturada, self).__init__(parent)

        self.setWindowTitle("Nombre la foto capturada")

        self.data = data
        self.imagen = imagen
        self.encodings = encodigns
        
        self.dbManager = DBManager()

        self.directorio_customizado = "src/img/personas"
        
        # self.setWindowFlags(self.windowFlags() | Qt.WindowStayOnTopHint)

        ##ALWAYS ON TOP
        self.setModal(True)

        # self.exec()
        self.layout = QtWidgets.QVBoxLayout()

        self.label_imagen = QLabel(self)
        self.nombre_imagen = QLineEdit(self)
        self.boton_guardar_foto = self.botonGuardarFoto()
        self.boton_cancelar_guardado = self.botonCancelarGuardado()

        self.nombre_imagen.setPlaceholderText("Introduzca el nombre de la foto")
        # self.nombre_imagen.textChanged.connect(lambda text: print(f"El texto cambio {text}"))

        # self.layout.addWidget(self.imagen)
        # self.layout.addWidget(self.boton_cancelar_guardado)
        # self.layout.addWidget(self.nombre_imagen)

        self.layout = QtWidgets.QVBoxLayout()

        # Foto
        self.layout.addWidget(self.label_imagen)

        # Input
        self.layout.addWidget(self.nombre_imagen)

        # Botones en horizontal
        botones_layout = QtWidgets.QHBoxLayout()
        botones_layout.addWidget(self.boton_guardar_foto)
        botones_layout.addWidget(self.boton_cancelar_guardado)

        self.layout.addLayout(botones_layout)

        self.setLayout(self.layout)

        self.resize(self.data.size().width(), self.data.size().height() + 200)
        
        self.checkData()

    # def deshabilitarBoton(self):
    #     if self.nombre_imagen.text()

    def checkData(self):

        if self.data is not None:
            self.label_imagen.setPixmap(self.data)
            print('true')
        else:
            print('false')
            self.close()

    def botonGuardarFoto(self):
        boton_guardar_foto = QPushButton("Guardar foto")
        boton_guardar_foto.setStatusTip("Guarda la foto que se esta mostrando")
        
        # conectas la acción
        boton_guardar_foto.clicked.connect(self.guardaFoto)  # <-- Aquí el fix
                                                            #no utilizar el parentesis '()' ya que activa la función
        return boton_guardar_foto

    def botonCancelarGuardado(self):
        boton_cancelar_guardado = QPushButton("Cancelar")
        boton_cancelar_guardado.setStatusTip("No se guardará la fotografía")
        
        # conectas la acción
        boton_cancelar_guardado.clicked.connect(self.cancelarGuardado)  # <-- Aquí el fix
                                                            #no utilizar el parentesis '()' ya que activa la función
        return boton_cancelar_guardado

    def cancelarGuardado(self):
        self.reject()

    def guardaFoto(self):

        self.boton_guardar_foto.setEnabled(False)

        print("Guardando foto")

        print('self.nombre_imagen.text(): ', self.nombre_imagen.text())
        if self.nombre_imagen.text() != "":

            if not os.path.exists(self.directorio_customizado):

                os.makedirs(self.directorio_customizado)

                print(f"Directory '{self.directorio_customizado}' created.")

            # Define the full path for saving the image
            # os.path.join handles path concatenation correctly across different operating systems
            # Suponiendo que self.encodings = face_recognition.face_encodings(frame)

            # print('self.encodings: ', self.encodings)

            print('self.encodings: ', self.encodings)
            
            if len(self.encodings) == 0:
                raise ValueError("No se detectó ninguna cara en la imagen")

            encoding_array = self.encodings        # Esto sí es NumPy array
            encoding_list = encoding_array.tolist()   # Ahora sí puedes convertir a lista
            encoding_json = json.dumps(encoding_list)

            self.dbManager.guardarPersonaData(self.nombre_imagen.text(), self.nombre_imagen.text() + '.png', encoding_json)

            output_path = os.path.join(self.directorio_customizado, self.nombre_imagen.text() + '.png')
            print('output_path: ', output_path)

            # Save the image to the specified custom directory
            cv2.imwrite(output_path, self.imagen)

            self.accept()

            print("Foto guardada")

        else:
            print("No tiene nombre")

        self.boton_guardar_foto.setEnabled(True)
        
    def cancelar(self):
        self.nombre_imagen.setText(" ") 
        self.data = None
        self.close()
from PySide6 import QtWidgets
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox
) 
from PySide6.QtCore import Qt
import os
import cv2
import numpy as np
from database.db_manager import DBManager
import face_recognition
import json

class NombrarFotoCapturada(QDialog):

    def __init__(self, 
                 parent = None, 
                 data = None, 
                 imagenes = None, 
                 encoding_frente = None, 
                 encoding_perfil_derecho = None,
                 encoding_perfil_izquierdo = None
                 ):
##
        super(NombrarFotoCapturada, self).__init__(parent)

        self.setWindowTitle("Nombre la foto capturada")

        self.data = data
        self.imagenes = imagenes
        self.encodings = {
            "encoding_frente": encoding_frente,
            "encoding_derecho": encoding_perfil_derecho,
            "encoding_izquierdo": encoding_perfil_izquierdo 
        }
        
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
        # self.nombre_imagen.textChanged.connect(lambda text: #print(f"El texto cambio {text}"))

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
            #print('true')
        else:
            #print('false')
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

        if self.nombre_imagen.text() != "":

            if not os.path.exists(self.directorio_customizado):
                os.makedirs(self.directorio_customizado)

            if len(self.encodings) == 0:
                raise ValueError("No se detectó ninguna cara en la imagen")

            encoding_frente = self.encodings["encoding_frente"]
            encoding_izq = self.encodings["encoding_izquierdo"]
            encoding_der = self.encodings["encoding_derecho"]

            encoding_promedio = np.mean([encoding_frente, encoding_izq, encoding_der], axis=0)

            personas_db = self.dbManager.getPersonas()
            
            if len(personas_db) > 0:
                encodings_db = []
                nombres_db = []
                
                for persona in personas_db:
                    encodings_db.append(json.loads(persona[3]))
                    nombres_db.append(persona[1])
                
                encodings_db = np.array(encodings_db)
                
                distancias = face_recognition.face_distance(encodings_db, encoding_promedio)
                
                if len(distancias) > 0:
                    indice_max = np.argmin(distancias)
                    distancia_minima = distancias[indice_max]
                    similitud_max = (1 - distancia_minima) * 100
                    nombre_similar = nombres_db[indice_max]
                    
                    umbral_similitud = 80.0
                    
                    if similitud_max > umbral_similitud:
                        respuesta = QMessageBox.warning(
                            self,
                            "Persona Similar Detectada",
                            f"Esta persona tiene {similitud_max:.1f}% de similitud con '{nombre_similar}'.\n\n¿Desea registrarla de todas formas?",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if respuesta == QMessageBox.No:
                            self.boton_guardar_foto.setEnabled(True)
                            return

            json_frente = json.dumps(encoding_frente.tolist())
            json_izq = json.dumps(encoding_izq.tolist())
            json_der = json.dumps(encoding_der.tolist())

            self.dbManager.guardarPersonaData(
                self.nombre_imagen.text(), 
                self.nombre_imagen.text() + '.png',
                json_frente,
                json_izq,
                json_der)

            output_path = os.path.join(self.directorio_customizado, self.nombre_imagen.text() + '.png')

            for imagen in self.imagenes:
                try:
                    cv2.imwrite(output_path, imagen)
                except TypeError:
                    print("Error al guardar:", TypeError)

            self.accept()

        self.boton_guardar_foto.setEnabled(True)
        
    def cancelar(self):
        self.nombre_imagen.setText(" ") 
        self.data = None
        self.close()
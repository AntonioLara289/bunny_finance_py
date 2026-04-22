from PySide6 import QtWidgets
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QComboBox
) 
from PySide6.QtCore import Qt
import os
import cv2
import numpy as np
from database.db_manager import DBManager
import face_recognition
import json

class CamarasDisponibles(QDialog):

    def __init__(self, parent = None, camaras_disponibles = None):

        super(CamarasDisponibles, self).__init__(parent)

        self.setWindowTitle("Seleccione una cámara")
        print('camaras_disponibles: ', camaras_disponibles)
        print("tipo de estructura:", type(camaras_disponibles))

        # self.setWindowFlags(self.windowFlags() | Qt.WindowStayOnTopHint)

        ##ALWAYS ON TOP
        self.setModal(True)

        self.comboBox = QtWidgets.QComboBox()
        # self.comboBox.addItem("Camara 1")
        # self.comboBox.addItem("Camara 2")
        # self.comboBox.addItem("Camara 3")

        for camara in camaras_disponibles:
            # print('camara: ', camara)
            self.comboBox.addItem(camara["nombre"], userData=camara["index"])

        self.comboBox.currentIndexChanged.connect(self.on_change) # Signal triggered on change

        # self.exec()
        self.layout = QtWidgets.QVBoxLayout()
        self.boton_cancelar_seleccion = self.botonCancelarSeleccion()
        self.boton_seleccionar_camara = self.botonSeleccionarCamara()

        # Botones en horizontal
        botones_layout = QtWidgets.QHBoxLayout()
        botones_layout.addWidget(self.boton_seleccionar_camara)
        botones_layout.addWidget(self.boton_cancelar_seleccion)

        self.layout.addWidget(self.comboBox)
        self.layout.addLayout(botones_layout)

        self.setLayout(self.layout)

    # def deshabilitarBoton(self):
    #     if self.nombre_imagen.text()

    def on_change(self, index):
        # Recuperamos el dato oculto usando el índice de la fila seleccionada
        camara_id = self.comboBox.itemData(index)
        
        # También podemos recuperar el nombre si lo necesitas
        nombre = self.comboBox.itemText(index)
        
        print(f"Seleccionaste: {nombre} (ID técnico: {camara_id})")
        # print(f"Current selection: {text}")

        
    def botonCancelarSeleccion(self):
        boton_cancelar_seleccion = QPushButton("Cancelar")
        boton_cancelar_seleccion.setStatusTip("No seleccionar cámara")
        
        # conectas la acción
        boton_cancelar_seleccion.clicked.connect(self.cancelarSelccionado)  # <-- Aquí el fix
                                                            #no utilizar el parentesis '()' ya que activa la función
        return boton_cancelar_seleccion

    def botonSeleccionarCamara(self):
        boton_seleccionar = QPushButton("Seleccionar")
        boton_seleccionar.setStatusTip("Seleccionar cámara")
        
        # conectas la acción
        boton_seleccionar.clicked.connect(self.seleccionarCamara)  # <-- Aquí el fix
                                                            #no utilizar el parentesis '()' ya que activa la función
        return boton_seleccionar
    
    def cancelarSelccionado(self):
        self.reject()

    def seleccionarCamara(self):
        self.accept()
    
    def getCurrentIndexCombox(self):
        return self.comboBox.currentIndex()

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
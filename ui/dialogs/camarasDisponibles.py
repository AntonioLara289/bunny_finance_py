from PySide6 import QtWidgets
from PySide6.QtWidgets import (
    QDialog,
    QPushButton,
    QComboBox
) 
class CamarasDisponibles(QDialog):

    def __init__(self, parent = None, camaras_disponibles = None):

        super(CamarasDisponibles, self).__init__(parent)

        self.setWindowTitle("Seleccione una cámara")
        # print('camaras_disponibles: ', camaras_disponibles)
        # print("tipo de estructura:", type(camaras_disponibles))
        # self.setWindowFlags(self.windowFlags() | Qt.WindowStayOnTopHint)

        ##ALWAYS ON TOP
        self.setModal(True)

        self.comboBox = QComboBox()
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

    def cancelar(self):
        self.nombre_imagen.setText(" ") 
        self.data = None
        self.close()
from PySide6 import QtWidgets
from PySide6.QtWidgets import (
    QDialog,
    QPushButton,
    QComboBox,
    QLineEdit,
    QToolBar,
    QToolButton
) 
import socket

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

        self.tipo_camara_es_ip = False

        self.ip_camara = QLineEdit(self)
        self.ip_camara.setPlaceholderText("Ejemplo: http://192.168.10.66:4747/video")
        self.ip_camara.hide()

        self.comboBox.currentIndexChanged.connect(self.on_change) # Signal triggered on change

        # self.exec()
        self.layout = QtWidgets.QVBoxLayout()
        self.boton_cancelar_seleccion = self.botonCancelarSeleccion()
        self.boton_cambiar_formulario = self.botonCambiarFormulario()
        self.boton_seleccionar_camara = self.botonSeleccionarCamara()

        # Botones en horizontal
        botones_layout = QtWidgets.QHBoxLayout()
        botones_layout.addWidget(self.boton_seleccionar_camara)
        botones_layout.addWidget(self.boton_cambiar_formulario)
        botones_layout.addWidget(self.boton_cancelar_seleccion)

        self.layout.addWidget(self.comboBox)
        self.layout.addWidget(self.ip_camara)
        self.layout.addLayout(botones_layout)

        # self.crear_menu_superior()

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

        if self.tipo_camara_es_ip:
            boton_seleccionar = QPushButton("Seleccionar cámara disponible")
            boton_seleccionar.setStatusTip("Seleccionar cámara usb/integradas")

        if not self.tipo_camara_es_ip:
            boton_seleccionar = QPushButton("Usar cámara IP")
            boton_seleccionar.setStatusTip("Utilzar cámara IP")
        
        # conectas la acción
        boton_seleccionar.clicked.connect(self.seleccionarCamara)  # <-- Aquí el fix
                                                            #no utilizar el parentesis '()' ya que activa la función
        return boton_seleccionar
    
    def botonCambiarFormulario(self):

        if self.tipo_camara_es_ip:
            boton_seleccionar = QPushButton("Mostrar cámaras disponibles")
            boton_seleccionar.setStatusTip("Seleccionar cámaras usb/integradas")

        if not self.tipo_camara_es_ip:
            boton_seleccionar = QPushButton("Utilizar cámara IP")
            boton_seleccionar.setStatusTip("Utilzar cámara IP")
        
        # conectas la acción
        boton_seleccionar.clicked.connect(self.alternarFormularioCamaras)  # <-- Aquí el fix
                                    #no utilizar el parentesis '()' ya que activa la función
        return boton_seleccionar

    def alternarFormularioCamaras(self):
        self.tipo_camara_es_ip = not self.tipo_camara_es_ip
        
        if self.tipo_camara_es_ip:
            self.comboBox.hide()
            self.ip_camara.show()
            self.boton_cambiar_formulario.setText("Mostrar cámaras locales")
            self.boton_seleccionar_camara.setText("Conectar IP")
        else:
            self.comboBox.show()
            self.ip_camara.hide()
            self.boton_cambiar_formulario.setText("Utilizar cámara IP")
            self.boton_seleccionar_camara.setText("Seleccionar cámara")

    def cancelarSelccionado(self):
        self.reject()

    def seleccionarCamara(self):
        self.accept()
    
    def getTipoCamara(self) -> bool:
        return self.tipo_camara_es_ip
    
    def getIpCamara(self) -> str:
        return self.ip_camara.text()
    
    def getCurrentIndexCombox(self):
        return self.comboBox.currentIndex()

    def cancelar(self):
        self.nombre_imagen.setText(" ") 
        self.data = None
        self.close()

    def crear_menu_superior(self):
        # Crear un botón que al hacerle clic despliegue tu AnimatedMenu
        self.btn_opciones = QToolButton(self)
        self.btn_opciones.setText("Opciones")
        self.btn_opciones.setPopupMode(QToolButton.InstantPopup)

    def verificar_conexion_ip(self, ip, puerto=80, timeout=2):
        """
        Intenta abrir una conexión al puerto de la IP.
        """
        try:
            # Intentamos conectar al puerto
            socket.create_connection((ip, puerto), timeout=timeout)
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False
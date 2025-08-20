from PySide6 import QtWidgets, QtCore

class EscanerRostro(QtWidgets.QWidget):
    
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Soy la pantalla de escaner"))
        btn = QtWidgets.QPushButton("Ir a pantalla numeros 2")
        layout.addWidget(btn)
        self.btn = btn  # lo guardamos para conectarlo fuera

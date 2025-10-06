from PySide6 import QtWidgets

class Historial(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Soy la pantalla de historial"))
        btn = QtWidgets.QPushButton("Ir a pantalla Escaneo")
        layout.addWidget(btn)
        self.btn = btn  # lo guardamos para conectarlo fuera
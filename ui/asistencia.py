from PySide6 import QtWidgets

class Asistencia(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Pantalla de Asistencia"))
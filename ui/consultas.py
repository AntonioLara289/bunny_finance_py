from PySide6 import QtWidgets, QtCore, QtGui

class Consultas(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Consultas"))

        # Tabla de consultas
        table = QtWidgets.QTableWidget(3, 2)
        table.setHorizontalHeaderLabels(["Nombre", "Muestras"])
        table.setItem(0, 0, QtWidgets.QTableWidgetItem("Moises"))
        table.setItem(0, 1, QtWidgets.QTableWidgetItem("1"))
        table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers) # Hacer tabla NO MODIFICABLE
        layout.addWidget(table)
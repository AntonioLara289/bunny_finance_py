from PySide6 import QtWidgets, QtCore
from database.db_manager import DBManager

class Consultas(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Consultas"))

        # Base de datos
        self.dbManager = DBManager() # Database instance
        self.getPersonas = self.dbManager.getPersonas()

        # Tabla de consultas
        rows = self.dbManager.getRows()
        table = QtWidgets.QTableWidget(rows, 3)
        table.setHorizontalHeaderLabels(["ID", "Nombre", "Muestras"])

        # llenar tabla
        for row_idx, persona in enumerate(self.getPersonas):
            table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(str(persona[0])))
            table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(persona[1])))
            table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem("Muestras..."))

        layout.addWidget(table)
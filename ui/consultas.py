from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QLineEdit, QTableWidget, QTableWidgetItem
from database.db_manager import DBManager

class Consultas(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Consultas"))

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Buscar por nombre...")
        layout.addWidget(self.search_box)

        # Base de datos
        self.dbManager = DBManager() # Instancia de base de datos
        self.getPersonas = self.dbManager.getPersonas() # Cantidad de ileras en la base de datos

        # Tabla de consultas
        rows = self.dbManager.getRows()
        self.table = QTableWidget(rows, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Muestras", "Fecha de registro", "Estatus"])

        # Llenar tabla
        for row_idx, persona in enumerate(self.getPersonas):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(persona[0])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(persona[1])))
            self.table.setItem(row_idx, 2, QTableWidgetItem("1"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(persona[4])))
            self.table.setItem(row_idx, 4, QTableWidgetItem("Desavtivado"))

        layout.addWidget(self.table)

        # Conectar búsqueda
        self.search_box.textChanged.connect(self.filter_table)

    def filter_table(self, text):
        """Filtrar filas de la tabla por nombre."""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)  # Nombre
            if item:
                self.table.setRowHidden(row, text.lower() not in item.text().lower()) # Mostrar solo si coincide

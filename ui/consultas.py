from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import (
    QLineEdit, QTableWidget, QTableWidgetItem, QComboBox,
    QLabel, QVBoxLayout, QHBoxLayout, QFrame, QHeaderView, QSizePolicy
)
from database.db_manager import DBManager


class Consultas(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # ===== Base layout =====
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ===== Title =====
        title = QLabel("Consultas de Personas")
        title.setObjectName("TitleLabel")
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)

        # ===== Search section =====
        search_frame = QFrame()
        search_frame.setObjectName("SectionFrame")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(15, 10, 15, 10)
        search_layout.setSpacing(10)

        search_label = QLabel("Buscar:")
        search_label.setObjectName("SectionTitle")
        search_layout.addWidget(search_label)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Buscar por nombre...")
        self.search_box.setObjectName("SearchBox")
        search_layout.addWidget(self.search_box)

        main_layout.addWidget(search_frame)

        # ===== Table section =====
        table_frame = QFrame()
        table_frame.setObjectName("SectionFrame")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(15, 15, 15, 15)
        table_layout.setSpacing(10)

        table_label = QLabel("Resultados de la base de datos")
        table_label.setObjectName("SectionTitle")
        table_layout.addWidget(table_label)

        # ===== Database connection =====
        self.dbManager = DBManager()
        self.getPersonas = self.dbManager.getPersonas()

        # ===== Table setup =====
        rows = self.dbManager.getRows()
        self.table = QTableWidget(rows, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Muestras", "Fecha de registro", "Estatus"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setObjectName("DataTable")

        # ===== Fill the table =====
        for row_idx, persona in enumerate(self.getPersonas):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(persona[0])))  # ID
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(persona[1])))  # Nombre
            self.table.setItem(row_idx, 2, QTableWidgetItem("1"))              # Muestras
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(persona[5])))  # Fecha de registro

            status_combo = QComboBox()
            status_combo.addItems(["activado", "desactivado", "pendiente"])
            status_map_reverse = {1: "activado", 0: "desactivado", 2: "pendiente"}
            status_combo.setCurrentText(status_map_reverse.get(persona[4], "desactivado"))

            status_combo.currentTextChanged.connect(lambda text, pid=persona[0]: self.update_status(pid, text))
            self.table.setCellWidget(row_idx, 4, status_combo)

        table_layout.addWidget(self.table)
        main_layout.addWidget(table_frame)

        # ===== Connect search =====
        self.search_box.textChanged.connect(self.filter_table)

    # ===== Table filter =====
    def filter_table(self, text):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)  # Nombre
            if item:
                self.table.setRowHidden(row, text.lower() not in item.text().lower())

    # ===== Update status =====
    def update_status(self, person_id, new_status):
        print(f"Actualizando ID {person_id} a {new_status}")
        self.dbManager.update_status(person_id, new_status)

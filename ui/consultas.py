from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import (
    QLineEdit, QTableWidget, QTableWidgetItem, QComboBox,
    QLabel, QVBoxLayout, QHBoxLayout, QFrame, QHeaderView, QSizePolicy
)
from database.db_manager import DBManager
from log import log

#log.push("Reconocimiento facial", "Juan identificado")
class Consultas(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setAccessibleName("ConsultasWidget")
        log.push("Vista consultas", "Abierto")
        # ===== Base layout =====
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ===== Title =====
        title = QLabel("Consultas de Personas")
        title.setObjectName("TitleLabel")
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)

        summary = QLabel(
            "Busca por nombre y cambia el estatus de cada persona sin salir de la vista."
        )
        summary.setObjectName("Hint")
        summary.setAlignment(QtCore.Qt.AlignCenter)
        summary.setWordWrap(True)
        main_layout.addWidget(summary)

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
        # Clear button
        try:
            self.search_box.setClearButtonEnabled(True)
        except Exception:
            pass
        self.search_box.setToolTip("Filtrar la tabla por nombre")
        search_layout.addWidget(self.search_box)

        main_layout.addWidget(search_frame)

        # Seccion de tabla
        table_frame = QFrame()
        table_frame.setObjectName("SectionFrame")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(15, 15, 15, 15)
        table_layout.setSpacing(10)

        table_label = QLabel("Resultados de la base de datos")
        table_label.setObjectName("SectionTitle")
        table_layout.addWidget(table_label)

        # Conexion a base de datos
        self.dbManager = DBManager()
        self.getPersonas = self.dbManager.getPersonas()

        # Columnas reales de la tabla `personas`
        # 0 id_persona | 1 nombre_persona | 2 imagen | 3 enc_izq | 4 enc_frente
        # 5 enc_der    | 6 estatus       | 7 created_at
        COL_ID, COL_NOMBRE, COL_ESTATUS, COL_FECHA = 0, 1, 6, 7

        # Setup para la tabla
        rows = len(self.getPersonas)
        self.table = QTableWidget(rows, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Muestras", "Fecha de registro", "Estatus"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(COL_ID, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setObjectName("DataTable")

        #  Llenado de la tabla
        status_map_reverse = {1: "activado", 0: "desactivado", 2: "pendiente"}
        for row_idx, persona in enumerate(self.getPersonas):
            self.table.setItem(row_idx, COL_ID, QTableWidgetItem(str(persona[COL_ID])))
            self.table.setItem(row_idx, COL_NOMBRE, QTableWidgetItem(str(persona[COL_NOMBRE])))
            self.table.setItem(row_idx, 2, QTableWidgetItem("1"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(persona[COL_FECHA])))

            status_combo = QComboBox()
            status_combo.addItems(["activado", "desactivado", "pendiente"])
            status_combo.setCurrentText(status_map_reverse.get(persona[COL_ESTATUS], "desactivado"))
            status_combo.currentTextChanged.connect(
                lambda text, pid=persona[COL_ID]: self.update_status(pid, text)
            )
            self.table.setCellWidget(row_idx, 4, status_combo)

        table_layout.addWidget(self.table)
        main_layout.addWidget(table_frame, stretch=1)

        # Conectar busqueda
        self.search_box.textChanged.connect(self.filter_table)

    # Filtrado para la tabla
    def filter_table(self, text):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)  # Nombre
            if item:
                self.table.setRowHidden(row, text.lower() not in item.text().lower())

    # Actualizar estatus
    def update_status(self, person_id, new_status):
        print(f"Actualizando ID {person_id} a {new_status}")
        self.dbManager.update_status(person_id, new_status)

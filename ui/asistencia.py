from PySide6.QtWidgets import (
    QLineEdit, QTableWidget, QTableWidgetItem, QComboBox,
    QLabel, QVBoxLayout, QFrame, QHBoxLayout, QHeaderView,
    QSizePolicy, QFileDialog, QPushButton
)
from PySide6 import QtWidgets, QtCore
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from ui.camaraReconocimientoWidget import CameraRecognitionWidget
from database.db_manager import DBManager
import json
import time
from log import log

asistencias_status = {1: "Asistió", 0: "No asistió"}

class AsistenciaPantalla(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Configuracion
        self.SIMILARITY_THRESHOLD = 60.0
        self.REQUIRED_SECONDS = 5.0

        # Variables de rendimiento
        self.UI_UPDATE_INTERVAL = 0.3  # segundos
        self.TIMER_GRACE_PERIOD = 1.0  # segundos

        # person_id -> start_time
        self.recognition_timers = {}
        self.attendance_given = set()
        self.last_ui_update = {}

        # Interfaz
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Registro de Asistencia")
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)

        # Camara
        cam_frame = QFrame()
        cam_layout = QVBoxLayout(cam_frame)

        self.dbManager = DBManager()
        self.getPersonas = self.dbManager.getPersonas()

        self.encodings = [json.loads(p[3]) for p in self.getPersonas]
        self.names = [p[1] for p in self.getPersonas]
        self.ids = [p[0] for p in self.getPersonas]

        self.camera_widget = CameraRecognitionWidget(
            encodings_db=self.encodings,
            names_db=self.names,
            ids_db=self.ids
        )
        self.camera_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        cam_layout.addWidget(self.camera_widget)

        self.camera_widget.faceRecognized.connect(self.actualizarAsistencia)
        main_layout.addWidget(cam_frame)

        # Tabla
        table_frame = QFrame()
        table_layout = QVBoxLayout(table_frame)

        table_label = QLabel("Lista de personas")
        table_layout.addWidget(table_label)

        rows = self.dbManager.getRows()
        self.table = QTableWidget(rows, 4)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Similitud", "Asistencia"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        # ID → ROW MAP (Busqueda O(1))
        self.id_to_row = {}

        for row_idx, persona in enumerate(self.getPersonas):
            persona_id = persona[0]
            self.id_to_row[persona_id] = row_idx

            self.table.setItem(row_idx, 0, QTableWidgetItem(str(persona_id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(persona[1])))
            self.table.setItem(row_idx, 2, QTableWidgetItem("0%"))

            combo = QComboBox()
            combo.addItems(["No asistió", "Asistió"])
            self.table.setCellWidget(row_idx, 3, combo)

        table_layout.addWidget(self.table)
        main_layout.addWidget(table_frame)

        # Exportacion
        export_btn = QPushButton("Exportar a Excel")
        export_btn.setMinimumHeight(40)
        export_btn.clicked.connect(
            lambda: (self.exportarExcel(), log.push("Lista exportada"))
        )
        main_layout.addWidget(export_btn, alignment=QtCore.Qt.AlignRight)

    # Logica de asistencia
    def actualizarAsistencia(self, name, id_, similarity):
        # Salida prematura
        if id_ in self.attendance_given:
            return

        now = time.time()

        # UI THROTTLE
        last_ui = self.last_ui_update.get(id_, 0)
        if now - last_ui < self.UI_UPDATE_INTERVAL:
            return
        self.last_ui_update[id_] = now

        # O(1) Busqueda
        row = self.id_to_row.get(id_)
        if row is None:
            return

        similarity_item = self.table.item(row, 2)
        similarity_item.setText(f"{similarity:.2f}%")

        # Logica
        if similarity >= self.SIMILARITY_THRESHOLD:
            if id_ not in self.recognition_timers:
                self.recognition_timers[id_] = now
            else:
                elapsed = now - self.recognition_timers[id_]
                if elapsed >= self.REQUIRED_SECONDS:
                    combo = self.table.cellWidget(row, 3)
                    if combo:
                        combo.setCurrentText("Asistió")
                        self.attendance_given.add(id_)
                        log.push(f"Asistencia registrada para {name}")
        else:
            # Prevenir spam de timers
            start = self.recognition_timers.get(id_)
            if start and now - start > self.TIMER_GRACE_PERIOD:
                del self.recognition_timers[id_]

    # Exportacion
    def exportarExcel(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar archivo Excel",
            "asistencia.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not path:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Asistencias"

        for col in range(self.table.columnCount()):
            header = self.table.horizontalHeaderItem(col).text()
            ws.cell(row=1, column=col + 1, value=header)

        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    ws.cell(row=row + 2, column=col + 1, value=item.text())
                else:
                    widget = self.table.cellWidget(row, col)
                    if isinstance(widget, QComboBox):
                        ws.cell(
                            row=row + 2,
                            column=col + 1,
                            value=widget.currentText()
                        )

        for col in range(1, self.table.columnCount() + 1):
            ws.column_dimensions[get_column_letter(col)].auto_size = True

        wb.save(path)

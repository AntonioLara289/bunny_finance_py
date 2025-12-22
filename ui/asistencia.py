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

asistencias_status = {1: "Asistió", 0: "No asistió"}

class AsistenciaPantalla(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Layout base
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Título
        title = QLabel("Registro de Asistencia")
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)

        # Sección de cámara
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

        for row_idx, persona in enumerate(self.getPersonas):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(persona[0])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(persona[1])))
            self.table.setItem(row_idx, 2, QTableWidgetItem("0%"))

            combo = QComboBox()
            combo.addItems(["No asistió", "Asistió"])
            self.table.setCellWidget(row_idx, 3, combo)

        table_layout.addWidget(self.table)
        main_layout.addWidget(table_frame)

        # Botón Exportar
        export_btn = QPushButton("Exportar a Excel")
        export_btn.setMinimumHeight(40)
        export_btn.clicked.connect(self.exportarExcel)

        main_layout.addWidget(export_btn, alignment=QtCore.Qt.AlignRight)

    # Actualizar asistencia
    def actualizarAsistencia(self, name, id_, similarity):
        similarityPercentajeAttendance = 60

        for row in range(self.table.rowCount()):
            id_item = self.table.item(row, 0)
            if id_item and int(id_item.text()) == id_:
                similarity_item = self.table.item(row, 2)

                try:
                    current_similarity = float(
                        similarity_item.text().replace('%', '')
                    )
                except:
                    current_similarity = 0.0

                if similarity > current_similarity:
                    similarity_item.setText(f"{similarity:.2f}%")

                    if similarity >= similarityPercentajeAttendance:
                        combo = self.table.cellWidget(row, 3)
                        if combo:
                            combo.setCurrentText("Asistió")
                break

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

        # Headers
        for col in range(self.table.columnCount()):
            header = self.table.horizontalHeaderItem(col).text()
            ws.cell(row=1, column=col + 1, value=header)

        # Datos
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

        # Ajustar columnas
        for col in range(1, self.table.columnCount() + 1):
            ws.column_dimensions[get_column_letter(col)].auto_size = True

        wb.save(path)

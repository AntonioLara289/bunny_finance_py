from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import (
    QLineEdit, QTableWidget, QTableWidgetItem, QComboBox,
    QLabel, QVBoxLayout
)
from ui.camaraReconocimientoWidget import CameraRecognitionWidget
from database.db_manager import DBManager
import json

asistencias_status = { 1: "Asistió", 0: "No asistió" }

class AsistenciaPantalla(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Asistencia"))

        # Base de datos
        self.dbManager = DBManager()
        self.getPersonas = self.dbManager.getPersonas()

        # Cargar encodings
        self.encodings = [json.loads(p[3]) for p in self.getPersonas]
        self.names = [p[1] for p in self.getPersonas]
        self.ids = [p[0] for p in self.getPersonas]

        # Implementacion Widget de camara
        self.camera_widget = CameraRecognitionWidget(
            encodings_db=self.encodings,
            names_db=self.names,
            ids_db=self.ids
        )
        layout.addWidget(self.camera_widget, alignment=QtCore.Qt.AlignCenter)

        # Conectar con reconocimiento
        self.camera_widget.faceRecognized.connect(self.actualizarAsistencia)

        # Tabla de personas
        rows = self.dbManager.getRows()
        self.table = QTableWidget(rows, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Similitud", "Asistencia"])

        for row_idx, persona in enumerate(self.getPersonas):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(persona[0])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(persona[1])))
            self.table.setItem(row_idx, 2, QTableWidgetItem("0%"))
            combo = QComboBox()
            combo.addItems(["No asistió", "Asistió"])
            self.table.setCellWidget(row_idx, 3, combo)

        layout.addWidget(self.table)

    # Al detectar un rostro
    def actualizarAsistencia(self, name, id_, similarity):
        for row in range(self.table.rowCount()):
            id_item = self.table.item(row, 0)
            if id_item and int(id_item.text()) == id_:
                self.table.item(row, 2).setText(f"{similarity}%")
                if similarity >= 62:
                    combo = self.table.cellWidget(row, 3)
                    combo.setCurrentText("Asistió")
                    break

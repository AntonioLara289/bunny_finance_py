from PySide6.QtWidgets import (
    QLineEdit, QTableWidget, QTableWidgetItem, QComboBox,
    QLabel, QVBoxLayout, QFrame, QHBoxLayout, QHeaderView, QSizePolicy
)
from PySide6 import QtWidgets, QtCore
from ui.camaraReconocimientoWidget import CameraRecognitionWidget
from database.db_manager import DBManager
import json

asistencias_status = {1: "Asistió", 0: "No asistió"}

class AsistenciaPantalla(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # ===== Base layout =====
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ===== Title =====
        title = QLabel("Registro de Asistencia")
        title.setObjectName("TitleLabel")
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)

        # ===== Camera section =====
        cam_frame = QFrame()
        cam_frame.setObjectName("SectionFrame")
        cam_layout = QVBoxLayout(cam_frame)
        cam_layout.setContentsMargins(15, 15, 15, 15)
        cam_layout.setSpacing(10)

        # Database setup
        self.dbManager = DBManager()
        self.getPersonas = self.dbManager.getPersonas()

        self.encodings = [json.loads(p[3]) for p in self.getPersonas]
        self.names = [p[1] for p in self.getPersonas]
        self.ids = [p[0] for p in self.getPersonas]

        # Camera widget
        self.camera_widget = CameraRecognitionWidget(
            encodings_db=self.encodings,
            names_db=self.names,
            ids_db=self.ids
        )
        self.camera_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        cam_layout.addWidget(self.camera_widget, alignment=QtCore.Qt.AlignCenter)
        self.camera_widget.personaConfirmada.connect(self.actualizarAsistencia)

        main_layout.addWidget(cam_frame)

        # ===== Table section =====
        table_frame = QFrame()
        table_frame.setObjectName("SectionFrame")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(15, 15, 15, 15)

        table_label = QLabel("Lista de personas")
        table_label.setObjectName("SectionTitle")
        table_layout.addWidget(table_label)

        rows = self.dbManager.getRows()
        self.table = QTableWidget(rows, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Similitud", "Asistencia"])
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

    # ===== Update attendance =====
    def actualizarAsistencia(self, name, id_, similarity):
        similarityPercentajeAttendance = 60
        for row in range(self.table.rowCount()):
            id_item = self.table.item(row, 0)
            if id_item and int(id_item.text()) == id_:
                similarity_item = self.table.item(row, 2)
                if similarity_item:
                    try:
                        current_similarity = float(similarity_item.text().replace('%', '').strip())
                    except ValueError:
                        current_similarity = 0.0

                    if similarity > current_similarity:
                        similarity_item.setText(f"{similarity:.2f}%")
                        if similarity >= similarityPercentajeAttendance:        # Porcentaje para ser admitida la asistencia
                            combo = self.table.cellWidget(row, 3)
                            if combo:
                                combo.setCurrentText("Asistió")
                        break

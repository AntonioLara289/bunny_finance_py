from PySide6.QtWidgets import (
    QWidget, QLineEdit, QTableWidget, QTableWidgetItem,
    QLabel, QVBoxLayout, QHBoxLayout, QHeaderView,
    QPushButton, QDialog, QApplication, QTimeEdit
)
from PySide6.QtCore import QTime, QTimer
from PySide6.QtCore import Qt
import sys


# Dialog para crear / editar sesión
class SesionDialog(QDialog):
    def __init__(self, parent=None, nombre="", hora_inicio=None, hora_fin=None):
        super().__init__(parent)

        self.setWindowTitle("Sesión")
        self.setFixedSize(420, 160)

        # Defaults
        if hora_inicio is None:
            hora_inicio = QTime(8, 0)
        if hora_fin is None:
            hora_fin = QTime(9, 0)

        # Inputs
        self.input_nombre = QLineEdit(nombre)

        self.time_inicio = QTimeEdit(hora_inicio)
        self.time_fin = QTimeEdit(hora_fin)

        self.time_inicio.setDisplayFormat("hh:mm AP")
        self.time_fin.setDisplayFormat("hh:mm AP")

        # Layouts
        fila_nombre = QHBoxLayout()
        fila_nombre.addWidget(QLabel("Nombre"))
        fila_nombre.addWidget(self.input_nombre)

        fila_tiempo = QHBoxLayout()
        fila_tiempo.addWidget(QLabel("Desde"))
        fila_tiempo.addWidget(self.time_inicio)
        fila_tiempo.addSpacing(10)
        fila_tiempo.addWidget(QLabel("Hasta"))
        fila_tiempo.addWidget(self.time_fin)

        # Botones
        btn_guardar = QPushButton("Guardar")
        btn_cancelar = QPushButton("Cancelar")

        btn_guardar.clicked.connect(self.accept)
        btn_cancelar.clicked.connect(self.reject)

        fila_botones = QHBoxLayout()
        fila_botones.addStretch()
        fila_botones.addWidget(btn_guardar)
        fila_botones.addWidget(btn_cancelar)

        # Layout principal
        layout = QVBoxLayout(self)
        layout.addLayout(fila_nombre)
        layout.addLayout(fila_tiempo)
        layout.addStretch()
        layout.addLayout(fila_botones)

    def datos(self):
        return (
            self.input_nombre.text(),
            self.time_inicio.time(),
            self.time_fin.time()
        )


# Widget principal
class Sesiones(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._cargar_sesiones_demo()

    def _actualizar_hora(self):
        self.lbl_hora.setText(QTime.currentTime().toString("hh:mm:ss AP"))

    def _setup_ui(self):
        self.setWindowTitle("Sesiones")
        self.resize(600, 400)

        layout_principal = QVBoxLayout(self)

        # Hora actual
        self.lbl_hora = QLabel()
        self.lbl_hora.setAlignment(Qt.AlignRight)
        self.lbl_hora.setStyleSheet("font-size: 14px; color: gray;")

        layout_principal.addWidget(self.lbl_hora)

        # Timer para actualizar la hora
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._actualizar_hora)
        self.timer.start(1000)

        self._actualizar_hora()  # actualizar inmediatamente

        # Botones
        layout_botones = QHBoxLayout()

        self.btn_crear = QPushButton("Crear sesión")
        self.btn_modificar = QPushButton("Modificar sesión")

        self.btn_crear.clicked.connect(self.crear_sesion)
        self.btn_modificar.clicked.connect(self.modificar_sesion)

        layout_botones.addWidget(self.btn_crear)
        layout_botones.addWidget(self.btn_modificar)
        layout_botones.addStretch()

        # Tabla
        self.tabla_sesiones = QTableWidget()
        self.tabla_sesiones.setColumnCount(2)
        self.tabla_sesiones.setHorizontalHeaderLabels([
            "Sesión", "Horario"
        ])

        self.tabla_sesiones.verticalHeader().setVisible(False)
        self.tabla_sesiones.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.tabla_sesiones.setSelectionBehavior(
            QTableWidget.SelectRows
        )
        self.tabla_sesiones.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        layout_principal.addLayout(layout_botones)
        layout_principal.addWidget(self.tabla_sesiones)

    def _cargar_sesiones_demo(self):
        sesiones = [
            ("Sesión 1", QTime(8, 0), QTime(9, 0)),
            ("Sesión 2", QTime(9, 0), QTime(10, 0)),
        ]

        self.tabla_sesiones.setRowCount(len(sesiones))

        for fila, (nombre, inicio, fin) in enumerate(sesiones):
            self.tabla_sesiones.setItem(
                fila, 0, QTableWidgetItem(nombre)
            )
            self.tabla_sesiones.setItem(
                fila, 1, QTableWidgetItem(self._formatear_horario(inicio, fin))
            )

    def _formatear_horario(self, inicio, fin):
        return f"{inicio.toString('hh:mm AP')} - {fin.toString('hh:mm AP')}"

    # Acciones
    def crear_sesion(self):
        dialog = SesionDialog(self)

        if dialog.exec():
            nombre, inicio, fin = dialog.datos()

            fila = self.tabla_sesiones.rowCount()
            self.tabla_sesiones.insertRow(fila)

            self.tabla_sesiones.setItem(
                fila, 0, QTableWidgetItem(nombre)
            )
            self.tabla_sesiones.setItem(
                fila, 1, QTableWidgetItem(self._formatear_horario(inicio, fin))
            )

    def modificar_sesion(self):
        fila = self.tabla_sesiones.currentRow()
        if fila < 0:
            return

        nombre_actual = self.tabla_sesiones.item(fila, 0).text()
        horario_actual = self.tabla_sesiones.item(fila, 1).text()

        # Parse times back (safe)
        inicio_str, fin_str = horario_actual.split(" - ")
        inicio = QTime.fromString(inicio_str, "hh:mm AP")
        fin = QTime.fromString(fin_str, "hh:mm AP")

        dialog = SesionDialog(
            self,
            nombre_actual,
            inicio,
            fin
        )

        if dialog.exec():
            nombre, inicio, fin = dialog.datos()

            self.tabla_sesiones.item(fila, 0).setText(nombre)
            self.tabla_sesiones.item(fila, 1).setText(
                self._formatear_horario(inicio, fin)
            )
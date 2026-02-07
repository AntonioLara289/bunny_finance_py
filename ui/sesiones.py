from PySide6.QtWidgets import (
    QWidget, QLineEdit, QTableWidget, QTableWidgetItem,
    QLabel, QVBoxLayout, QHBoxLayout, QHeaderView,
    QPushButton, QDialog, QTimeEdit, QStyle
)
from PySide6.QtCore import QTime
from PySide6.QtCore import Qt
from ui.top_bar import TopBar
from database.db_manager import DBManager

# Dialog para crear / editar sesión
class SesionDialog(QDialog):
    def __init__(self, parent=None, nombre="", hora_inicio=None, hora_fin=None):
        super().__init__(parent)

        self.setWindowTitle("Sesión")
        self.setFixedSize(420, 160)

        if hora_inicio is None:
            hora_inicio = QTime(8, 0)
        if hora_fin is None:
            hora_fin = QTime(9, 0)

        self.input_nombre = QLineEdit(nombre)

        self.time_inicio = QTimeEdit(hora_inicio)
        self.time_fin = QTimeEdit(hora_fin)

        self.time_inicio.setDisplayFormat("hh:mm AP")
        self.time_fin.setDisplayFormat("hh:mm AP")

        fila_nombre = QHBoxLayout()
        fila_nombre.addWidget(QLabel("Nombre"))
        fila_nombre.addWidget(self.input_nombre)

        fila_tiempo = QHBoxLayout()
        fila_tiempo.addWidget(QLabel("Desde"))
        fila_tiempo.addWidget(self.time_inicio)
        fila_tiempo.addSpacing(10)
        fila_tiempo.addWidget(QLabel("Hasta"))
        fila_tiempo.addWidget(self.time_fin)

        btn_guardar = QPushButton("Guardar")
        btn_cancelar = QPushButton("Cancelar")

        btn_guardar.clicked.connect(self.accept)
        btn_cancelar.clicked.connect(self.reject)

        fila_botones = QHBoxLayout()
        fila_botones.addStretch()
        fila_botones.addWidget(btn_guardar)
        fila_botones.addWidget(btn_cancelar)

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
        self.setAccessibleName("SesionesWidget")
        self.db = DBManager()
        self._setup_ui()
        self.row_id_map = {}

        self._cargar_sesiones_db()

    def _setup_ui(self):
        self.setWindowTitle("Sesiones")
        self.resize(600, 400)

        layout_principal = QVBoxLayout(self)

        # TOP BAR
        self.top_bar = TopBar("Sesiones")
        layout_principal.addWidget(self.top_bar)

        # Botones
        layout_botones = QHBoxLayout()

        self.btn_crear = QPushButton("Crear sesión")
        self.btn_modificar = QPushButton("Modificar sesión")
        self.btn_eliminar = QPushButton("Eliminar sesión")

        self.btn_crear.setToolTip("Crear nueva sesión")
        self.btn_modificar.setToolTip("Modificar la sesión seleccionada")
        self.btn_eliminar.setToolTip("Eliminar la sesión seleccionada")

        self.btn_crear.clicked.connect(self.crear_sesion)
        self.btn_modificar.clicked.connect(self.modificar_sesion)
        self.btn_eliminar.clicked.connect(self.eliminar_sesion)

        layout_botones.addWidget(self.btn_crear)
        layout_botones.addWidget(self.btn_modificar)
        layout_botones.addWidget(self.btn_eliminar)
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
        # Deprecated: now load from DB
        pass

    def _cargar_sesiones_db(self):
        sesiones = self.db.getSesiones()

        self.tabla_sesiones.setRowCount(len(sesiones))

        for fila, (id_sesion, nombre, inicio_str, fin_str) in enumerate(sesiones):
            self.row_id_map[fila] = id_sesion
            inicio = QTime.fromString(inicio_str, "HH:mm")
            fin = QTime.fromString(fin_str, "HH:mm")
            self.tabla_sesiones.setItem(fila, 0, QTableWidgetItem(nombre))
            self.tabla_sesiones.setItem(fila, 1, QTableWidgetItem(self._formatear_horario(inicio, fin)))

    def _formatear_horario(self, inicio, fin):
        return f"{inicio.toString('hh:mm AP')} - {fin.toString('hh:mm AP')}"

    # Acciones
    def crear_sesion(self):
        dialog = SesionDialog(self)

        if dialog.exec():
            nombre, inicio, fin = dialog.datos()

            # Guardar en DB (usar formato 24h HH:MM)
            inicio_str = inicio.toString("HH:mm")
            fin_str = fin.toString("HH:mm")
            new_id = self.db.guardarSesion(nombre, inicio_str, fin_str)

            fila = self.tabla_sesiones.rowCount()
            self.tabla_sesiones.insertRow(fila)
            self.row_id_map[fila] = new_id

            self.tabla_sesiones.setItem(fila, 0, QTableWidgetItem(nombre))
            self.tabla_sesiones.setItem(fila, 1, QTableWidgetItem(self._formatear_horario(inicio, fin)))

    def modificar_sesion(self):
        fila = self.tabla_sesiones.currentRow()
        if fila < 0:
            return

        nombre_actual = self.tabla_sesiones.item(fila, 0).text()
        horario_actual = self.tabla_sesiones.item(fila, 1).text()

        inicio_str, fin_str = horario_actual.split(" - ")
        inicio = QTime.fromString(inicio_str, "hh:mm AP")
        fin = QTime.fromString(fin_str, "hh:mm AP")

        dialog = SesionDialog(self, nombre_actual, inicio, fin)

        if dialog.exec():
            nombre, inicio, fin = dialog.datos()

            # Actualizar en DB
            id_sesion = self.row_id_map.get(fila)
            if id_sesion:
                inicio_db = inicio.toString("HH:mm")
                fin_db = fin.toString("HH:mm")
                self.db.actualizarSesion(id_sesion, nombre, inicio_db, fin_db)

            self.tabla_sesiones.item(fila, 0).setText(nombre)
            self.tabla_sesiones.item(fila, 1).setText(self._formatear_horario(inicio, fin))

    def eliminar_sesion(self):
        fila = self.tabla_sesiones.currentRow()
        if fila < 0:
            return

        # Obtener id_sesion
        id_sesion = self.row_id_map.get(fila)
        if not id_sesion:
            return

        # Eliminar de BD
        try:
            self.db.eliminarSesion(id_sesion)
        except Exception:
            return

        # Eliminar de tabla
        self.tabla_sesiones.removeRow(fila)

        # Actualizar row_id_map
        new_map = {}
        for row in range(self.tabla_sesiones.rowCount()):
            if row in self.row_id_map:
                new_map[row] = self.row_id_map[row]
            elif row + 1 in self.row_id_map:
                new_map[row] = self.row_id_map[row + 1]
        self.row_id_map = new_map

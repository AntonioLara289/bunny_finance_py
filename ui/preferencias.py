from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import Signal, QTimer
from cv2_enumerate_cameras import enumerate_cameras
from ui.top_bar import TopBar
from ui.app_settings import AppSettings
from log import log


def _crear_fila(label, widget):
    row = QtWidgets.QHBoxLayout()
    row.addWidget(QtWidgets.QLabel(label))
    row.addWidget(widget, stretch=1)
    return row


def _parse_resolution(res_str):
    parts = res_str.split("x")
    return int(parts[0]), int(parts[1])


RESOLUTIONS = ["640x480", "800x600", "960x720", "1280x720", "1920x1080"]

LANGUAGES = ["Español", "English"]


class Preferencias(QtWidgets.QWidget):
    style_changed = Signal(str)

    def __init__(self, style_callback=None):
        super().__init__()

        self.setWindowTitle("Preferencias")
        self.style_callback = style_callback
        self.settings = AppSettings()
        log.push("Vista preferencias", "Abierto")

        # Scroll area for many options
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)

        inner = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(inner)
        layout.setSpacing(14)
        layout.setContentsMargins(30, 20, 30, 20)

        self.top_bar = TopBar("Preferencias")
        layout.addWidget(self.top_bar)

        title = QtWidgets.QLabel("Preferencias de la aplicación")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # ============ APARIENCIA ============
        app_group = QtWidgets.QGroupBox("Apariencia")
        app_grid = QtWidgets.QVBoxLayout()
        app_grid.setSpacing(8)

        # Tema visual
        styles = [
            ("Estilo Frutiger Aero", "styles/style.qss"),
            ("Estilo Frutiger Aero Dark", "styles/frutigerdark.qss"),
            ("Estilo Frutiger Aero Verde", "styles/aerogreen.qss"),
            ("Estilo Frutiger Aero Sunset", "styles/aerosunset.qss"),
            ("Estilo Frutiger Aero Frost", "styles/aerofrost.qss"),
            ("Estilo Frutiger Aero Organic", "styles/aeroorganic.qss"),
        ]
        self.theme_combo = QtWidgets.QComboBox()
        for display_name, path in styles:
            self.theme_combo.addItem(display_name, userData=path)
        idx = self.theme_combo.findData(self.settings.theme_path)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        app_grid.addLayout(_crear_fila("Tema visual:", self.theme_combo))

        # Idioma
        self.lang_combo = QtWidgets.QComboBox()
        self.lang_combo.addItems(LANGUAGES)
        lang_idx = self.lang_combo.findText(self.settings.language)
        if lang_idx >= 0:
            self.lang_combo.setCurrentIndex(lang_idx)
        app_grid.addLayout(_crear_fila("Idioma:", self.lang_combo))

        app_group.setLayout(app_grid)
        layout.addWidget(app_group)

        # ============ RECONOCIMIENTO FACIAL ============
        face_group = QtWidgets.QGroupBox("Reconocimiento facial")
        face_grid = QtWidgets.QVBoxLayout()
        face_grid.setSpacing(8)

        # Similarity threshold
        self.threshold_spin = QtWidgets.QDoubleSpinBox()
        self.threshold_spin.setRange(0.0, 1.0)
        self.threshold_spin.setSingleStep(0.05)
        self.threshold_spin.setDecimals(2)
        self.threshold_spin.setValue(self.settings.similarity_threshold)
        face_grid.addLayout(_crear_fila("Umbral de similitud:", self.threshold_spin))
        hint1 = QtWidgets.QLabel("Valores más altos = más exigente (0.5 recomendado)")
        hint1.setStyleSheet("font-size: 11px; color: gray; margin-left: 20px;")
        face_grid.addWidget(hint1)

        # Confirmations needed
        self.confirm_spin = QtWidgets.QSpinBox()
        self.confirm_spin.setRange(1, 10)
        self.confirm_spin.setValue(self.settings.confirmations_needed)
        face_grid.addLayout(_crear_fila("Confirmaciones necesarias:", self.confirm_spin))
        hint2 = QtWidgets.QLabel("Cuántas detecciones seguidas para confirmar (2 recomendado)")
        hint2.setStyleSheet("font-size: 11px; color: gray; margin-left: 20px;")
        face_grid.addWidget(hint2)

        # Detection interval
        self.interval_spin = QtWidgets.QSpinBox()
        self.interval_spin.setRange(1, 30)
        self.interval_spin.setSuffix(" frames")
        self.interval_spin.setValue(self.settings.detection_interval)
        face_grid.addLayout(_crear_fila("Intervalo de detección:", self.interval_spin))
        hint3 = QtWidgets.QLabel("Procesar 1 de cada N frames (mayor = más rápido, 5 recomendado)")
        hint3.setStyleSheet("font-size: 11px; color: gray; margin-left: 20px;")
        face_grid.addWidget(hint3)

        # Camera device
        self.refresh_cam_btn = QtWidgets.QPushButton("⟳")
        self.refresh_cam_btn.setFixedSize(28, 28)
        self.refresh_cam_btn.setToolTip("Actualizar lista de cámaras")

        cam_row = QtWidgets.QHBoxLayout()
        self.cam_combo = QtWidgets.QComboBox()
        self._populate_cameras()
        cam_row.addWidget(QtWidgets.QLabel("Dispositivo de cámara:"))
        cam_row.addWidget(self.cam_combo, stretch=1)
        cam_row.addWidget(self.refresh_cam_btn)
        face_grid.addLayout(cam_row)

        self.refresh_cam_btn.clicked.connect(self._populate_cameras)

        # Camera resolution
        self.res_combo = QtWidgets.QComboBox()
        self.res_combo.addItems(RESOLUTIONS)
        res_idx = self.res_combo.findText(self.settings.camera_resolution)
        if res_idx >= 0:
            self.res_combo.setCurrentIndex(res_idx)
        face_grid.addLayout(_crear_fila("Resolución de cámara:", self.res_combo))
        hint4 = QtWidgets.QLabel("Menor resolución = más FPS (640x480 recomendado)")
        hint4.setStyleSheet("font-size: 11px; color: gray; margin-left: 20px;")
        face_grid.addWidget(hint4)

        face_group.setLayout(face_grid)
        layout.addWidget(face_group)

        # ============ ASISTENCIA ============
        att_group = QtWidgets.QGroupBox("Asistencia")
        att_grid = QtWidgets.QVBoxLayout()
        att_grid.setSpacing(8)

        self.required_secs_spin = QtWidgets.QDoubleSpinBox()
        self.required_secs_spin.setRange(0.5, 10.0)
        self.required_secs_spin.setSingleStep(0.5)
        self.required_secs_spin.setSuffix(" seg")
        self.required_secs_spin.setValue(self.settings.required_seconds)
        att_grid.addLayout(_crear_fila("Segundos requeridos:", self.required_secs_spin))
        hint5 = QtWidgets.QLabel("Tiempo que el rostro debe estar visible para marcar asistencia")
        hint5.setStyleSheet("font-size: 11px; color: gray; margin-left: 20px;")
        att_grid.addWidget(hint5)

        att_group.setLayout(att_grid)
        layout.addWidget(att_group)

        # ============ UMAP ============
        umap_group = QtWidgets.QGroupBox("Visualización UMAP")
        umap_grid = QtWidgets.QVBoxLayout()
        umap_grid.setSpacing(8)

        self.umap_neighbors_spin = QtWidgets.QSpinBox()
        self.umap_neighbors_spin.setRange(2, 50)
        self.umap_neighbors_spin.setValue(self.settings.umap_n_neighbors)
        umap_grid.addLayout(_crear_fila("Vecinos (n_neighbors):", self.umap_neighbors_spin))
        hint6 = QtWidgets.QLabel("Controla cuán local es la proyección (5-15 típico)")
        hint6.setStyleSheet("font-size: 11px; color: gray; margin-left: 20px;")
        umap_grid.addWidget(hint6)

        self.umap_mindist_spin = QtWidgets.QDoubleSpinBox()
        self.umap_mindist_spin.setRange(0.0, 0.99)
        self.umap_mindist_spin.setSingleStep(0.05)
        self.umap_mindist_spin.setDecimals(2)
        self.umap_mindist_spin.setValue(self.settings.umap_min_dist)
        umap_grid.addLayout(_crear_fila("Distancia mínima:", self.umap_mindist_spin))
        hint7 = QtWidgets.QLabel("Qué tan juntos pueden estar los puntos (0.1 recomendado)")
        hint7.setStyleSheet("font-size: 11px; color: gray; margin-left: 20px;")
        umap_grid.addWidget(hint7)

        umap_group.setLayout(umap_grid)
        layout.addWidget(umap_group)

        # ============ INFORMACIÓN ============
        info_group = QtWidgets.QGroupBox("Información del sistema")
        info_grid = QtWidgets.QVBoxLayout()
        info_grid.setSpacing(8)

        from ui.camaraInsightFaceWidget import get_ctx_id
        ctx = get_ctx_id()
        provider_label = QtWidgets.QLabel(f"Proveedor de inferencia: {'GPU (CUDA)' if ctx == 0 else 'GPU (DirectML)' if ctx == -1 else f'ctx_id={ctx}'}")
        provider_label.setStyleSheet("font-size: 12px;")
        info_grid.addWidget(provider_label)

        db_label = QtWidgets.QLabel("Base de datos: faces.db")
        db_label.setStyleSheet("font-size: 12px;")
        info_grid.addWidget(db_label)

        info_group.setLayout(info_grid)
        layout.addWidget(info_group)

        layout.addStretch(1)

        # ============ BOTONES ============
        btn_layout = QtWidgets.QHBoxLayout()
        self.save_btn = QtWidgets.QPushButton("Guardar cambios")
        self.default_btn = QtWidgets.QPushButton("Restaurar valores por defecto")
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.default_btn)
        layout.addLayout(btn_layout)

        scroll.setWidget(inner)

        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

        self.save_btn.clicked.connect(self.guardar_cambios)
        self.default_btn.clicked.connect(self.restaurar_por_defecto)

    def _populate_cameras(self):
        self.cam_combo.clear()
        camaras = []
        for camera_info in enumerate_cameras():
            camaras.append((camera_info.index, camera_info.name))
        camaras = list({c[1]: c for c in camaras}.values())
        if not camaras:
            self.cam_combo.addItem("Sin cámara detectada", userData=-1)
        else:
            for idx, name in camaras:
                self.cam_combo.addItem(f"[{idx}] {name}", userData=idx)
        saved_idx = self.settings.camera_index
        found = self.cam_combo.findData(saved_idx)
        if found >= 0:
            self.cam_combo.setCurrentIndex(found)

    def guardar_cambios(self):
        # Apariencia
        idx_t = self.theme_combo.currentIndex()
        style_path = self.theme_combo.itemData(idx_t)
        self.settings.theme_path = style_path
        self.settings.language = self.lang_combo.currentText()

        # Reconocimiento facial
        self.settings.similarity_threshold = self.threshold_spin.value()
        self.settings.confirmations_needed = self.confirm_spin.value()
        self.settings.detection_interval = self.interval_spin.value()
        self.settings.camera_index = self.cam_combo.currentData()
        self.settings.camera_resolution = self.res_combo.currentText()

        # Asistencia
        self.settings.required_seconds = self.required_secs_spin.value()

        # UMAP
        self.settings.umap_n_neighbors = self.umap_neighbors_spin.value()
        self.settings.umap_min_dist = self.umap_mindist_spin.value()

        # Apply theme
        if self.style_callback:
            self.style_callback(style_path)
        else:
            self.style_changed.emit(style_path)

        self.settings.settings_changed.emit("all")

        QtWidgets.QMessageBox.information(self, "Preferencias", "Cambios guardados correctamente.")

    def restaurar_por_defecto(self):
        self.settings.restore_defaults()

        self.theme_combo.setCurrentIndex(0)
        self.lang_combo.setCurrentIndex(0)
        self.threshold_spin.setValue(0.5)
        self.confirm_spin.setValue(2)
        self.interval_spin.setValue(5)
        first_cam = self.cam_combo.findData(0)
        if first_cam >= 0:
            self.cam_combo.setCurrentIndex(first_cam)
        res_idx = self.res_combo.findText("640x480")
        if res_idx >= 0:
            self.res_combo.setCurrentIndex(res_idx)
        self.required_secs_spin.setValue(2.0)
        self.umap_neighbors_spin.setValue(5)
        self.umap_mindist_spin.setValue(0.1)

        if self.style_callback:
            self.style_callback("styles/style.qss")
        else:
            self.style_changed.emit("styles/style.qss")

        self.settings.settings_changed.emit("all")

        QtWidgets.QMessageBox.information(self, "Preferencias", "Valores restaurados por defecto.")

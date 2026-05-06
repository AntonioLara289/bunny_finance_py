from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import Signal
from ui.top_bar import TopBar
from log import log

class Preferencias(QtWidgets.QWidget):
    style_changed = Signal(str)

    def __init__(self, style_callback=None):
        super().__init__()

        self.setWindowTitle("Preferencias")
        self.style_callback = style_callback
        log.push("Vista preferencias", "Abierto")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(30, 20, 30, 20)

        self.top_bar = TopBar("Preferencias")
        layout.addWidget(self.top_bar)

        title = QtWidgets.QLabel("Preferencias de la aplicación")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        theme_group = QtWidgets.QGroupBox("Tema visual")
        theme_layout = QtWidgets.QVBoxLayout()

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
        theme_layout.addWidget(QtWidgets.QLabel("Selecciona un tema:"))
        theme_layout.addWidget(self.theme_combo)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        lang_group = QtWidgets.QGroupBox("Idioma")
        lang_layout = QtWidgets.QHBoxLayout()
        lang_label = QtWidgets.QLabel("Selecciona el idioma:")
        self.lang_combo = QtWidgets.QComboBox()
        self.lang_combo.addItems(["Español", "Inglés"])
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)

        layout.addStretch(1)

        btn_layout = QtWidgets.QHBoxLayout()
        self.save_btn = QtWidgets.QPushButton("Guardar cambios")
        self.default_btn = QtWidgets.QPushButton("Restaurar valores por defecto")
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.default_btn)
        layout.addLayout(btn_layout)

        self.save_btn.clicked.connect(self.guardar_cambios)
        self.default_btn.clicked.connect(self.restaurar_por_defecto)

    def guardar_cambios(self):
        selected_index = self.theme_combo.currentIndex()
        style_path = self.theme_combo.itemData(selected_index)

        if self.style_callback:
            self.style_callback(style_path)
        else:
            self.style_changed.emit(style_path)

        QtWidgets.QMessageBox.information(self, "Preferencias", "Cambios guardados correctamente.")

    def restaurar_por_defecto(self):
        self.theme_combo.setCurrentIndex(0)
        self.lang_combo.setCurrentIndex(0)
        QtWidgets.QMessageBox.information(self, "Preferencias", "Valores restaurados por defecto.")
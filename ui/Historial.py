from PySide6 import QtWidgets, QtCore
from ui.top_bar import TopBar
from log import log

class Historial(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Historial")
        log.push("Vista historial", "Abierto")

        # Layout principal
        layout = QtWidgets.QVBoxLayout(self)

        # TOP BAR
        self.top_bar = TopBar("Historial")
        layout.addWidget(self.top_bar)

        # Título
        title = QtWidgets.QLabel("Historial de acciones")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        # Lista
        self.list = QtWidgets.QListWidget()
        layout.addWidget(self.list)

        self.refresh()

    def refresh(self):
        self.list.clear()
        for entry in log.all():
            text = f"[{entry['hora']}] {entry['accion']}"
            if entry.get("resultado"):
                text += f" → {entry['resultado']}"
            self.list.addItem(text)

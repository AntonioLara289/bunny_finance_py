from PySide6 import QtWidgets, QtCore
from log import log

class Historial(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Historial")

        layout = QtWidgets.QVBoxLayout(self)

        title = QtWidgets.QLabel("Historial de acciones")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        self.list = QtWidgets.QListWidget()
        layout.addWidget(self.list)
        self.refresh()

    def refresh(self):
        self.list.clear()
        for entry in log.all():
            text = f"[{entry['hora']}] {entry['accion']}"
            if entry["resultado"]:
                text += f" → {entry['resultado']}"
            self.list.addItem(text)

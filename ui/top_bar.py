from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, QTime

class TopBar(QWidget):
    def __init__(self, left_text="example text", parent=None):
        super().__init__(parent)

        self.lbl_left = QLabel(left_text)
        self.lbl_left.setStyleSheet("font-size: 14px;")

        self.lbl_hora = QLabel()
        self.lbl_hora.setAlignment(Qt.AlignRight)
        self.lbl_hora.setStyleSheet("font-size: 14px; color: gray;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.addWidget(self.lbl_left)
        layout.addStretch()
        layout.addWidget(self.lbl_hora)

        # Timer para actualizar la hora
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._actualizar_hora)
        self.timer.start(1000)

        self._actualizar_hora()

    def _actualizar_hora(self):
        self.lbl_hora.setText(QTime.currentTime().toString("hh:mm:ss AP"))

    def set_title(self, text: str):
        self.lbl_left.setText(text)

from PySide6.QtCore import Qt, QTime, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class TopBar(QWidget):
    def __init__(self, left_text="", parent=None):
        super().__init__(parent)

        self.setObjectName("TopBar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(38)

        self.lbl_left = QLabel(left_text)
        self.lbl_left.setObjectName("TopBarTitle")

        self.lbl_hora = QLabel()
        self.lbl_hora.setObjectName("TopBarClock")
        self.lbl_hora.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 6)
        layout.addWidget(self.lbl_left)
        layout.addStretch(1)
        layout.addWidget(self.lbl_hora)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._actualizar_hora)
        self.timer.start(1000)

        self._actualizar_hora()

    def _actualizar_hora(self):
        self.lbl_hora.setText(QTime.currentTime().toString("hh:mm:ss AP"))

    def set_title(self, text: str):
        self.lbl_left.setText(text)

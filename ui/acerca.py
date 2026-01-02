import sys
from PySide6 import QtCore, QtWidgets

class Acerca(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Acerca de")
        self.resize(450, 400)

        layout = QtWidgets.QVBoxLayout(self)

        # Title
        title = QtWidgets.QLabel("Bunny Detect")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # Subtitle
        subtitle = QtWidgets.QLabel("Versión 1.0.0\n© 2026 Moises Gonzalez / Emmanuel Lara")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        subtitle.setStyleSheet("color: gray;")
        layout.addWidget(subtitle)

        # Scroll area
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        container = QtWidgets.QWidget()
        scroll.setWidget(container)

        container_layout = QtWidgets.QVBoxLayout(container)

        text = QtWidgets.QLabel(
            "Esta aplicación está desarrollada en Python 3 y utiliza "
            "software de código abierto.\n\n"
            "Librerías utilizadas:\n\n"
            "• Python 3 – © Python Software Foundation (Licencia PSF)\n"
            "• PySide6 (Qt for Python) – © The Qt Company (LGPL v3)\n"
            "• MediaPipe – © Google LLC (Licencia Apache 2.0)\n"
            "• OpenCV – © OpenCV Contributors (Licencia Apache 2.0)\n"
            "• NumPy – © NumPy Developers (Licencia BSD)\n"
            "• Matplotlib – © Matplotlib Developers (Licencia PSF / BSD)\n"
            "• face_recognition – © Adam Geitgey (Licencia MIT)\n\n"
            "Aviso de privacidad:\n"
            "Esta aplicación procesa imágenes y datos faciales de forma local. "
            "No se transmiten ni almacenan datos biométricos sin el "
            "consentimiento explícito del usuario."
        )

        text.setWordWrap(True)
        text.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        container_layout.addWidget(text)
        container_layout.addStretch()
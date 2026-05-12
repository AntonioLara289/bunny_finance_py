import sys
from PySide6 import QtCore, QtWidgets

class Acerca(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Acerca de")
        self.resize(500, 500)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QtWidgets.QLabel("Bunny Finance / Bunny Detect")
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
            "• OpenCV – © OpenCV Contributors (Licencia Apache 2.0)\n"
            "• InsightFace – © InsightFace Contributors (Licencia MIT)\n"
            "• ONNX Runtime – © Microsoft Corporation (Licencia MIT)\n"
            "• ONNX – © ONNX Contributors (Licencia Apache 2.0)\n"
            "• NumPy – © NumPy Developers (Licencia BSD)\n"
            "• Matplotlib – © Matplotlib Developers (Licencia PSF / BSD)\n"
            "• UMAP – © Leland McInnes et al. (Licencia BSD)\n"
            "• scikit-learn – © INRIA / scikit-learn Developers (Licencia BSD)\n"
            "• openpyxl – © Eric Gazoni / Charlie Clark (Licencia MIT)\n\n"
            "Aviso de privacidad:\n"
            "Esta aplicación procesa imágenes y datos faciales de forma local. "
            "No se transmiten ni almacenan datos biométricos sin el "
            "consentimiento explícito del usuario.\n\n"
            "Marcas registradas:\n"
            "• Qt es una marca registrada de The Qt Company Ltd.\n"
            "• Python es una marca registrada de Python Software Foundation.\n"
            "• Microsoft, Windows y DirectML son marcas registradas de "
            "Microsoft Corporation.\n"
            "• NVIDIA y CUDA son marcas registradas de NVIDIA Corporation.\n"
            "• ONNX es una marca de la Linux Foundation.\n\n"
            "Este software se distribuye con fines académicos como trabajo "
            "de tesis. Consulte el archivo LICENSE para más información."
        )

        text.setWordWrap(True)
        text.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        container_layout.addWidget(text)
        container_layout.addStretch()
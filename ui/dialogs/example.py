from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import (
    QPushButton,
    QLabel,
    QApplication,
    QDialog
)
from PySide6.QtGui import (
    QImage,
    QPixmap,
    QGuiApplication
)
from PySide6.QtCore import (
    QTimer,
    Qt
)

class DialogExample(QDialog):
     
    def __init__(self, parent=None):
        super(DialogExample, self).__init__(parent)
        self.setWindowTitle("My Form")
        # self.setWindowFlag(Qt.WindowStaysOnTopHint)
        # self.setModal(True) # Explicitly set as modal if using show()
        # self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        # self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        # self.setWindowFlag(Qt.FramelessWindowHint, True)


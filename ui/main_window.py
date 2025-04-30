import sys
import random
from PySide6 import QtCore, QtWidgets, QtGui
from database.db_manager import DBManager

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир"]

        self.button = QtWidgets.QPushButton("Click me!")
        self.text = QtWidgets.QLabel("Hello World",
                                     alignment=QtCore.Qt.AlignCenter)
        self.modal_button = QtWidgets.QPushButton("Open Modal")

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.modal_button)

        self.button.clicked.connect(self.magic)
        self.modal_button.clicked.connect(self.show_modal)

        self.db = DBManager()
        self.db.getBalances()

    def show_modal(self):
        modal = QtWidgets.QDialog(self)
        modal.setWindowTitle("Modal Dialog")
        modal_layout = QtWidgets.QVBoxLayout(modal)
        modal_label = QtWidgets.QLabel("This is a modal dialog", alignment=QtCore.Qt.AlignCenter)
        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(modal.accept)

        modal_layout.addWidget(modal_label)
        modal_layout.addWidget(close_button)

        modal.exec()

    @QtCore.Slot()
    def magic(self):
        self.text.setText(random.choice(self.hello))

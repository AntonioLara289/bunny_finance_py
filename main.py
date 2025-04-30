import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    # window.resize(800, 600)
    window.showMaximized()  # Maximize the window
    window.show()

    sys.exit(app.exec())
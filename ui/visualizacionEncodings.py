# UMAPViewer.py
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QFrame, QComboBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import umap
import numpy as np
from database.db_manager import DBManager

class UMAPViewer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UMAP de Personas")
        self.setMinimumSize(800, 600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Titulo
        title = QLabel("Visualización UMAP de Personas")
        title.setObjectName("TitleLabel")
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)

        # Seccion de busqueda
        search_frame = QFrame()
        search_frame.setObjectName("SectionFrame")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(15, 10, 15, 10)
        search_layout.setSpacing(10)

        search_label = QLabel("Seleccionar Persona:")
        search_label.setObjectName("SectionTitle")
        search_layout.addWidget(search_label)

        self.person_combo = QComboBox()
        search_layout.addWidget(self.person_combo)

        main_layout.addWidget(search_frame)

        # Matplotlib canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

        # Base de datos
        self.dbManager = DBManager()
        self.load_persons()

        # Conectar seleccion
        self.person_combo.currentIndexChanged.connect(self.plot_umap)

    def load_persons(self):
        personas = self.dbManager.getPersonas()
        self.person_map = {f"{p[1]} (ID: {p[0]})": p[0] for p in personas}
        self.person_combo.addItems(self.person_map.keys())

    def plot_umap(self):
        person_text = self.person_combo.currentText()
        if not person_text:
            return

        person_id = self.person_map[person_text]

        # Fetch encodings from DB (replace with your actual method)
        encodings = self.dbManager.getEndingsPersona(person_id)  # returns list of np.array

        if not encodings:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.set_title("No hay datos de esta persona")
            self.canvas.draw()
            return

        X = np.array(encodings)
        reducer = umap.UMAP(n_neighbors=5, min_dist=0.3, n_components=2, random_state=42)
        embedding = reducer.fit_transform(X)

        # Plot
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.scatter(embedding[:, 0], embedding[:, 1], s=50, c='blue', alpha=0.7)
        ax.set_title(f"UMAP de {person_text}")
        ax.set_xlabel("UMAP 1")
        ax.set_ylabel("UMAP 2")
        self.canvas.draw()

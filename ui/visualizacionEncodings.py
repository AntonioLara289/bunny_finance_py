# UMAP.py
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QLabel, QVBoxLayout, QCheckBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import umap
import numpy as np
import ast
import matplotlib.cm as cm
import math

from database.db_manager import DBManager


class UMAPViewer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Ajustes iniciales de ventana
        self.setWindowTitle("UMAP Viewer")
        self.resize(900, 700)

        # Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # Titulo
        title = QLabel("Visualización UMAP de Personas")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title)

        # Descripccion de pantalla
        text = QLabel(
            "Esta ventana muestra una proyección bidimensional de los encodings faciales "
            "almacenados en el sistema utilizando el algoritmo UMAP (Uniform Manifold "
            "Approximation and Projection).\n\n"
            "La gráfica permite visualizar la similitud entre personas: los puntos que "
            "aparecen más cercanos representan rostros con características faciales "
            "similares, mientras que los puntos más alejados corresponden a individuos "
            "distintos.\n\n"
            "Cada punto representa una persona registrada en la base de datos y se le "
            "asigna un color único para facilitar su identificación visual. Esta "
            "visualización es útil para analizar la separación entre clases, detectar "
            "posibles confusiones en el reconocimiento facial y evaluar la calidad de "
            "los encodings generados por el sistema."
        )
        text.setWordWrap(True)
        text.setMaximumHeight(120)
        main_layout.addWidget(text)

        # Checkbox para muestra de nombres
        self.hover_checkbox = QCheckBox("Mostrar nombre al pasar el cursor")
        self.hover_checkbox.setChecked(True)
        main_layout.addWidget(self.hover_checkbox)

        # Canvas de Matplotlib
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas, stretch=1)

        # Base de datos y datos para muestreo
        self.dbManager = DBManager()
        self.encodings = []
        self.names = []
        self.embedding = None
        self.scatter = None
        self.annotation = None
        self._umap_drawn = False
        self.cargar_personas()

    # Mostrar
    def showEvent(self, event):
        super().showEvent(event)
        if not self._umap_drawn:
            self._umap_drawn = True
            QtCore.QTimer.singleShot(0, self.plot_umap)

    # Carga de informacion
    def cargar_personas(self):
        rows = self.dbManager.getPersonas()

        self.encodings.clear()
        self.names.clear()

        for row in rows:
            try:
                nombre = row[1]
                encoding = np.array(ast.literal_eval(row[3]), dtype=np.float32)

                if encoding.ndim != 1:
                    continue

                self.encodings.append(encoding)
                self.names.append(nombre)

            except Exception as e:
                print("Fila inválida:", e)

        print("Personas cargadas:", len(self.encodings))

    # Canvas con datos
    def plot_umap(self):
        if len(self.encodings) < 2:
            self._draw_error("No hay suficientes datos para UMAP")
            return

        X = np.vstack(self.encodings)

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        reducer = umap.UMAP(
            n_neighbors=max(2, min(5, len(X) - 1)),
            min_dist=0.1,
            n_components=2,
            random_state=42
        )

        self.embedding = reducer.fit_transform(X)

        colors = cm.get_cmap("tab20")(np.linspace(0, 1, len(X)))

        self.scatter = ax.scatter(
            self.embedding[:, 0],
            self.embedding[:, 1],
            s=120,
            alpha=0.9,
            c=colors,
            picker=True
        )

        ax.set_title("Proyección UMAP de Personas")
        ax.set_xlabel("UMAP-1")
        ax.set_ylabel("UMAP-2")

        # Anotaciones con nombres
        self.annotation = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 10),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="black", alpha=0.75),
            color="white"
        )
        self.annotation.set_visible(False)

        # Conectar con el "hover" de mouse
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)

        self.figure.tight_layout()
        self.canvas.draw()

    # Logica de "hover" de mouse
    def _on_hover(self, event):
        if not self.hover_checkbox.isChecked():
            self.annotation.set_visible(False)
            self.canvas.draw_idle()
            return

        if event.inaxes != self.scatter.axes:
            self.annotation.set_visible(False)
            self.canvas.draw_idle()
            return

        x, y = event.xdata, event.ydata

        min_dist = float("inf")
        index = None

        for i, (px, py) in enumerate(self.embedding):
            d = math.hypot(px - x, py - y)
            if d < min_dist:
                min_dist = d
                index = i

        # Threshold (ajustable)
        if min_dist < 0.3:
            self.annotation.xy = (self.embedding[index][0], self.embedding[index][1])
            self.annotation.set_text(self.names[index])
            self.annotation.set_visible(True)
        else:
            self.annotation.set_visible(False)

        self.canvas.draw_idle()

    # Pantalla de error
    def _draw_error(self, msg):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, msg, ha="center", va="center", fontsize=14)
        ax.axis("off")
        self.canvas.draw()

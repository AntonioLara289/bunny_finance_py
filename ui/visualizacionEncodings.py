# UMAPViewer.py
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QLabel, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import umap
import numpy as np
import ast
import matplotlib.cm as cm

from database.db_manager import DBManager


class UMAPViewer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # UI
        self.setWindowTitle("UMAP Viewer")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Visualización UMAP de Personas")
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumSize(600, 400)
        main_layout.addWidget(self.canvas)

        # Datos
        self.dbManager = DBManager()
        self.encodings = []

        self.cargar_personas()

        # Control to draw only once
        self._umap_drawn = False

    # Mostar umap
    def showEvent(self, event):
        super().showEvent(event)

        if self._umap_drawn:
            return

        self._umap_drawn = True
        print("UMAPViewer visible, drawing UMAP...")
        QtCore.QTimer.singleShot(0, self.plot_umap)

    # Cargar encodings desde base de datos
    def cargar_personas(self):
        raw_encodings = self.dbManager.getEncodings()
        self.encodings.clear()

        print("Cargando encodings de la base de datos...")

        for i, row in enumerate(raw_encodings):
            try:
                if isinstance(row, str):
                    encoding = ast.literal_eval(row)
                else:
                    encoding = row

                encoding = np.array(encoding, dtype=np.float32)

                if encoding.ndim != 1:
                    print(f"Fila {i} forma invalida:", encoding.shape)
                    continue

                self.encodings.append(encoding)
                print(f"Fila {i}: {encoding.shape}")

            except Exception as e:
                print(f"Fila fallida {i}:", e)

        print("Total de encodings invalidos:", len(self.encodings))

    # Plot UMAP, dar colores unicos a cada persona
    def plot_umap(self):
        print("Plotting UMAP...")

        if len(self.encodings) < 2:
            print("Encodings insuficientes")
            self._draw_error("No hay suficientes encodings para muestreo")
            return

        X = np.vstack(self.encodings)
        print("UMAP input shape:", X.shape)

        # For very small datasets, just plot directly
        if len(X) <= 5:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            colors = cm.tab10(np.arange(len(X)))  # different color per point
            ax.scatter(X[:, 0], X[:, 1], s=120, alpha=0.9, c=colors)
            ax.set_title("Pocos encodings, muestreo ampliado")
            self.figure.tight_layout()
            self.canvas.draw()
            print("pocos datos, graficando datos expandidos")
            return

        # Run UMAP
        reducer = umap.UMAP(
            n_neighbors=max(2, min(5, len(X) - 1)),
            min_dist=0.1,
            n_components=2,
            random_state=42
        )

        embedding = reducer.fit_transform(X)

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Assign a unique color per person
        colors = cm.get_cmap("tab20")(np.linspace(0, 1, len(self.encodings)))

        ax.scatter(
            embedding[:, 0],
            embedding[:, 1],
            s=120,
            alpha=0.9,
            c=colors
        )

        ax.set_title("UMAP proyeccion de personas")
        ax.set_xlabel("UMAP-1")
        ax.set_ylabel("UMAP-2")
        self.figure.tight_layout()
        self.canvas.draw()
        print("UMAP dibujado")

    # Muestra de errores
    def _draw_error(self, msg):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, msg, ha="center", va="center", fontsize=14)
        ax.axis("off")
        self.canvas.draw()

from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QLabel, QVBoxLayout, QCheckBox, QPushButton, QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import umap
import numpy as np
import matplotlib.cm as cm
import math
from ui.app_settings import AppSettings, is_light_theme

class UMAPViewer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Ajustes iniciales de ventana
        self.setWindowTitle("UMAP Viewer")
        self.resize(900, 700)
        self.setMinimumSize(700, 500)
        self.setAccessibleName("UMAPViewer")

        # Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # Header with title + refresh
        title = QLabel("Visualización UMAP de Personas")
        title.setObjectName("PageTitle")
        title.setAlignment(QtCore.Qt.AlignLeft)

        refresh_btn = QPushButton("⟳")
        refresh_btn.setProperty("variant", "ghost")
        refresh_btn.setToolTip("Recalcular la proyección UMAP")
        refresh_btn.setFixedSize(30, 30)
        refresh_btn.setAccessibleName("RefreshUMAP")
        refresh_btn.clicked.connect(self._on_refresh)

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch()
        header.addWidget(refresh_btn)
        main_layout.addLayout(header)

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
        text.setObjectName("Hint")
        text.setWordWrap(True)
        text.setMaximumHeight(120)
        main_layout.addWidget(text)

        # Checkbox para muestra de nombres
        self.hover_checkbox = QCheckBox("Mostrar nombre al pasar el cursor")
        self.hover_checkbox.setChecked(True)
        main_layout.addWidget(self.hover_checkbox)

        # Canvas de Matplotlib
        self.settings = AppSettings()
        self.figure = Figure()
        self._apply_chart_theme()
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas, stretch=1)

        # Datos para la proyeccion
        self.encodings = []
        self.names = []
        self.embedding = None
        self.scatter = None
        self.annotation = None
        self._umap_drawn = False
        self.cargar_personas()

    def _chart_colors(self):
        """Colores del lienzo segun el tema activo."""
        if is_light_theme(self.settings.theme_path):
            return "#ffffff", "#1f2a33", "#c7d3dd", "#4a5b68"
        return "#101c24", "#d9f2fb", "#2b4b5c", "#9db8ca"

    def _apply_chart_theme(self):
        """Matplotlib no lee el QSS, asi que se=configura con la paleta del tema."""
        bg, text, grid, muted = self._chart_colors()
        try:
            self.figure.patch.set_facecolor(bg)
            self.figure.set_edgecolor(bg)
        except Exception:
            pass
        self._chart_bg = bg
        self._chart_text = text
        self._chart_grid = grid
        self._chart_muted = muted

    def _on_refresh(self):
        """Refresh UMAP data and redraw."""
        try:
            self._apply_chart_theme()
            self.cargar_personas()
            self.plot_umap()
        except Exception as e:
            print("[UMAP] Error al refrescar:", e)

    # Mostrar
    def showEvent(self, event):
        super().showEvent(event)
        if not self._umap_drawn:
            self._umap_drawn = True
            QtCore.QTimer.singleShot(0, self.plot_umap)

    # Carga de informacion
    def cargar_personas(self):
        self.encodings.clear()
        self.names.clear()

        try:
            # Misma base de datos que el resto de la aplicacion.
            from database.db_manager import DBManager

            for nombre, emb in DBManager().getPersonasConEmbeddings():
                self.encodings.append(emb)
                self.names.append(nombre)
        except Exception as e:
            print("[UMAP] Error al cargar datos:", e)

        print("Personas cargadas:", len(self.encodings))

    # Canvas con datos
    def plot_umap(self):
        if len(self.encodings) < 2:
            self._draw_error("No hay suficientes datos para UMAP")
            return

        X = np.vstack(self.encodings)

        self.figure.clear()
        self._apply_chart_theme()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor(self._chart_bg)

        reducer = umap.UMAP(
            n_neighbors=max(2, min(self.settings.umap_n_neighbors, len(X) - 1)),
            min_dist=self.settings.umap_min_dist,
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

        ax.set_title("Proyección UMAP de Personas", color=self._chart_text)
        ax.set_xlabel("UMAP-1", color=self._chart_muted)
        ax.set_ylabel("UMAP-2", color=self._chart_muted)
        ax.tick_params(colors=self._chart_muted)
        for spine in ax.spines.values():
            spine.set_color(self._chart_grid)
        ax.grid(True, color=self._chart_grid, linewidth=0.6, alpha=0.6)

        # Anotaciones con nombres
        self.annotation = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 10),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc=self._chart_bg, ec=self._chart_grid, alpha=0.92),
            color=self._chart_text
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
        self._apply_chart_theme()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor(self._chart_bg)
        ax.text(0.5, 0.5, msg, ha="center", va="center", fontsize=14, color=self._chart_text)
        ax.axis("off")
        self.canvas.draw()

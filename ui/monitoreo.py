"""Ventana independiente de monitoreo de rendimiento y exactitud.

Se abre desde el menu "Vistas" del MainWindow, pero vive en su propia ventana
top-level para poder observarla en paralelo a la camara (por ejemplo mientras la
pantalla de Asistencia esta capturando).

Pestanas:
- Rendimiento: FPS, latencia de inferencia, CPU/RAM/GPU en vivo.
- Reconocimiento: contadores de coincidencias y distribucion de similitudes.
- Exactitud: evaluacion offline sobre faces.db (ROC, AUC, EER, FAR/FRR,
  exactitud de identificacion leave-one-out).
"""

import csv
import json
import os
import time
from collections import deque

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core.metrics import MetricsCollector, SystemSampler, contexto_inferencia
from core.paths import FACES_DB_PATH, from_base
from ui.app_settings import AppSettings, is_light_theme

REPORTES_DIR = from_base("reportes")


class _EvalWorker(QtCore.QObject):
    """Corre la evaluacion offline en un hilo aparte para no congelar la UI."""

    resultado = QtCore.Signal(dict)
    error = QtCore.Signal(str)

    def __init__(self, db_path, umbral):
        super().__init__()
        self.db_path = db_path
        self.umbral = umbral

    @QtCore.Slot()
    def run(self):
        try:
            from core.evaluacion import evaluar_base

            self.resultado.emit(evaluar_base(self.db_path, self.umbral))
        except Exception as e:
            self.error.emit(str(e))


class MonitoreoWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Monitoreo del sistema — Bunny Detect")
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.resize(1120, 780)
        self.setMinimumSize(920, 620)

        self.collector = MetricsCollector()
        self.sampler = SystemSampler()
        self.settings = AppSettings()

        self._pausado = False
        self._sistema = {}
        self._tick_count = 0
        self._hist_t = deque(maxlen=600)
        self._hist_fps = deque(maxlen=600)
        self._hist_lat = deque(maxlen=600)
        self._ultimo_resultado = None
        self._eval_thread = None
        self._eval_worker = None

        self._build_ui()
        self._apply_chart_theme_all()

        self.timer_ui = QtCore.QTimer(self)
        self.timer_ui.timeout.connect(self._tick)
        self.timer_ui.start(500)

        self.timer_sistema = QtCore.QTimer(self)
        self.timer_sistema.timeout.connect(self._muestrear_sistema)
        self.timer_sistema.start(1000)
        QtCore.QTimer.singleShot(0, self._muestrear_sistema)

    # ------------------------------------------------------------------ UI base
    def _build_ui(self):
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(16, 16, 16, 16)
        raiz.setSpacing(12)

        raiz.addLayout(self._build_toolbar())
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_tab_rendimiento(), "Rendimiento")
        self.tabs.addTab(self._build_tab_reconocimiento(), "Reconocimiento")
        self.tabs.addTab(self._build_tab_exactitud(), "Exactitud")
        raiz.addWidget(self.tabs, stretch=1)

        self.lbl_estado = QLabel("Listo. Las metricas se alimentan desde la camara de reconocimiento activa.")
        self.lbl_estado.setObjectName("Hint")
        self.lbl_estado.setWordWrap(True)
        raiz.addWidget(self.lbl_estado)

    def _build_toolbar(self):
        barra = QHBoxLayout()

        self.btn_pausar = QPushButton("Pausar")
        self.btn_pausar.setProperty("variant", "ghost")
        self.btn_pausar.clicked.connect(self._toggle_pausa)

        self.btn_reiniciar = QPushButton("Reiniciar metricas")
        self.btn_reiniciar.setProperty("variant", "ghost")
        self.btn_reiniciar.clicked.connect(self._reiniciar)

        self.btn_exportar = QPushButton("Exportar reporte")
        self.btn_exportar.setProperty("variant", "ghost")
        self.btn_exportar.clicked.connect(self._exportar)

        self.btn_evaluar = QPushButton("Evaluar exactitud")
        self.btn_evaluar.clicked.connect(self._evaluar)

        barra.addWidget(self.btn_pausar)
        barra.addWidget(self.btn_reiniciar)
        barra.addStretch()
        barra.addWidget(self.btn_exportar)
        barra.addWidget(self.btn_evaluar)
        return barra

    def _kpi(self, titulo):
        card = QFrame()
        card.setObjectName("KpiCard")
        card.setFrameShape(QFrame.StyledPanel)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(2)
        t = QLabel(titulo)
        t.setObjectName("Hint")
        v = QLabel("—")
        v.setObjectName("KpiValue")
        v.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lay.addWidget(t)
        lay.addWidget(v)
        return card, v

    def _nuevo_canvas(self):
        fig = Figure(figsize=(4, 2.4), tight_layout=True)
        canvas = FigureCanvas(fig)
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return fig, canvas

    # -------------------------------------------------------- Tab Rendimiento
    def _build_tab_rendimiento(self):
        pagina = QWidget()
        lay = QVBoxLayout(pagina)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(10)
        self.kpis = {}
        tarjetas = [
            ("fps_actual", "FPS actual"),
            ("fps_promedio", "FPS promedio"),
            ("latencia_media_ms", "Latencia media (ms)"),
            ("latencia_p95_ms", "Latencia p95 (ms)"),
            ("latencia_max_ms", "Latencia max (ms)"),
            ("frames", "Frames procesados"),
            ("caras", "Caras detectadas"),
            ("caras_por_frame", "Caras / frame"),
        ]
        for i, (clave, titulo) in enumerate(tarjetas):
            card, valor = self._kpi(titulo)
            self.kpis[clave] = valor
            grid.addWidget(card, i // 4, i % 4)
        lay.addLayout(grid)

        graficas = QHBoxLayout()
        self.fig_fps, self.canvas_fps = self._nuevo_canvas()
        self.fig_lat, self.canvas_lat = self._nuevo_canvas()
        graficas.addWidget(self.canvas_fps)
        graficas.addWidget(self.canvas_lat)
        lay.addLayout(graficas, stretch=1)

        self.sistema_grid = QGridLayout()
        self.sistema_grid.setSpacing(6)
        self.lbl_sistema = {}
        etiquetas = [
            ("cpu_proceso_pct", "CPU proceso (%)"),
            ("cpu_sistema_pct", "CPU sistema (%)"),
            ("ram_proceso_mb", "RAM proceso (MB)"),
            ("ram_sistema_pct", "RAM sistema (%)"),
            ("gpu_uso_pct", "GPU uso (%)"),
            ("gpu_mem_used_mb", "VRAM usada (MB)"),
            ("proveedor", "Proveedor de inferencia"),
        ]
        for i, (clave, titulo) in enumerate(etiquetas):
            self.sistema_grid.addWidget(QLabel(titulo + ":"), i // 4, (i % 4) * 2)
            val = QLabel("—")
            val.setObjectName("KpiValue")
            self.lbl_sistema[clave] = val
            self.sistema_grid.addWidget(val, i // 4, (i % 4) * 2 + 1)
        lay.addLayout(self.sistema_grid)

        return pagina

    # ------------------------------------------------------- Tab Reconocimiento
    def _build_tab_reconocimiento(self):
        pagina = QWidget()
        lay = QVBoxLayout(pagina)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(10)
        self.kpis_rec = {}
        tarjetas = [
            ("matches", "Coincidencias (>= umbral)"),
            ("desconocidos", "Desconocidos"),
            ("tasa_match", "Tasa de coincidencia"),
            ("detecciones", "Frames con deteccion"),
            ("sim_media", "Similitud media"),
            ("sim_p95", "Similitud p95"),
            ("sim_max", "Similitud maxima"),
            ("muestras_sim", "Observaciones"),
        ]
        for i, (clave, titulo) in enumerate(tarjetas):
            card, valor = self._kpi(titulo)
            self.kpis_rec[clave] = valor
            grid.addWidget(card, i // 4, i % 4)
        lay.addLayout(grid)

        self.fig_sim, self.canvas_sim = self._nuevo_canvas()
        lay.addWidget(self.canvas_sim, stretch=1)
        return pagina

    # ------------------------------------------------------------ Tab Exactitud
    def _build_tab_exactitud(self):
        pagina = QWidget()
        lay = QVBoxLayout(pagina)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(12)

        controles = QHBoxLayout()
        self.lbl_eval_info = QLabel(
            "La evaluacion corre sobre los encodings registrados en faces.db "
            "(protocolos de verificacion 1:1 e identificacion 1:N leave-one-out)."
        )
        self.lbl_eval_info.setObjectName("Hint")
        self.lbl_eval_info.setWordWrap(True)
        controles.addWidget(self.lbl_eval_info, stretch=1)
        lay.addLayout(controles)

        cuerpo = QHBoxLayout()
        self.tabla = QTableWidget(0, 2)
        self.tabla.setHorizontalHeaderLabels(["Metrica", "Valor"])
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        cuerpo.addWidget(self.tabla, stretch=1)

        graficas = QVBoxLayout()
        self.fig_roc, self.canvas_roc = self._nuevo_canvas()
        self.fig_dist, self.canvas_dist = self._nuevo_canvas()
        graficas.addWidget(self.canvas_roc)
        graficas.addWidget(self.canvas_dist)
        cuerpo.addLayout(graficas, stretch=1)
        lay.addLayout(cuerpo, stretch=1)

        self.lbl_eval_estado = QLabel("Sin evaluar. Pulsa \"Evaluar exactitud\".")
        self.lbl_eval_estado.setObjectName("Hint")
        lay.addWidget(self.lbl_eval_estado)
        return pagina

    # ------------------------------------------------------------------ tema
    def _chart_colors(self):
        if is_light_theme(self.settings.theme_path):
            return "#ffffff", "#1f2a33", "#c7d3dd", "#4a5b68"
        return "#101c24", "#d9f2fb", "#2b4b5c", "#9db8ca"

    def _apply_chart_theme_all(self):
        self._bg, self._text, self._grid, self._muted = self._chart_colors()
        for fig in (self.fig_fps, self.fig_lat, self.fig_sim, self.fig_roc, self.fig_dist):
            try:
                fig.patch.set_facecolor(self._bg)
            except Exception:
                pass

    def _preparar_ejes(self, ax, titulo, xlabel="", ylabel=""):
        ax.set_facecolor(self._bg)
        ax.set_title(titulo, color=self._text, fontsize=10)
        ax.set_xlabel(xlabel, color=self._muted, fontsize=9)
        ax.set_ylabel(ylabel, color=self._muted, fontsize=9)
        ax.tick_params(colors=self._muted, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(self._grid)
        ax.grid(True, color=self._grid, linewidth=0.6, alpha=0.5)

    # ----------------------------------------------------------- muestreo sys
    def _muestrear_sistema(self):
        self._sistema = self.sampler.sample()
        self._sistema["proveedor"] = contexto_inferencia()["proveedor"]
        self._actualizar_labels_sistema()

    def _fmt(self, valor, sufijo="", dec=1):
        if valor is None:
            return "N/D"
        try:
            return "{:.{}f}{}".format(float(valor), dec, sufijo)
        except (TypeError, ValueError):
            return str(valor)

    def _actualizar_labels_sistema(self):
        s = self._sistema
        for clave, lbl in self.lbl_sistema.items():
            if clave == "proveedor":
                lbl.setText(str(s.get("proveedor", "N/D")))
            elif clave.endswith("_mb"):
                lbl.setText(self._fmt(s.get(clave), " MB", 1))
            elif clave.endswith("_pct"):
                lbl.setText(self._fmt(s.get(clave), " %", 1))
            else:
                lbl.setText(self._fmt(s.get(clave)))

    # --------------------------------------------------------------- ticks UI
    def _tick(self):
        if self._pausado:
            return
        self._tick_count += 1
        snap = self.collector.snapshot()
        self._actualizar_kpis(snap)

        self._hist_t.append(snap["duracion_s"])
        self._hist_fps.append(snap["fps_actual"])
        self._hist_lat.append(snap["latencia_media_ms"] or 0.0)

        if self._tick_count % 2 == 0:
            self._dibujar_fps_lat()
        if self._tick_count % 3 == 0:
            self._dibujar_similitudes()

    def _actualizar_kpis(self, snap):
        fmt = self._fmt
        self.kpis["fps_actual"].setText(fmt(snap["fps_actual"], dec=1))
        self.kpis["fps_promedio"].setText(fmt(snap["fps_promedio"], dec=1))
        self.kpis["latencia_media_ms"].setText(fmt(snap["latencia_media_ms"], " ms", 2))
        self.kpis["latencia_p95_ms"].setText(fmt(snap["latencia_p95_ms"], " ms", 2))
        self.kpis["latencia_max_ms"].setText(fmt(snap["latencia_max_ms"], " ms", 2))
        self.kpis["frames"].setText(str(snap["frames"]))
        self.kpis["caras"].setText(str(snap["caras"]))
        self.kpis["caras_por_frame"].setText(fmt(snap["caras_por_frame"], dec=2))

        self.kpis_rec["matches"].setText(str(snap["matches"]))
        self.kpis_rec["desconocidos"].setText(str(snap["desconocidos"]))
        self.kpis_rec["tasa_match"].setText(fmt(snap["tasa_match"] * 100.0, " %", 1))
        self.kpis_rec["detecciones"].setText(str(snap["detecciones"]))
        self.kpis_rec["sim_media"].setText(fmt(snap["sim_media"], dec=3))
        self.kpis_rec["sim_p95"].setText(fmt(snap["sim_p95"], dec=3))
        self.kpis_rec["sim_max"].setText(fmt(snap["sim_max"], dec=3))
        self.kpis_rec["muestras_sim"].setText(str(snap["muestras_sim"]))

    def _dibujar_fps_lat(self):
        t = list(self._hist_t)
        self.fig_fps.clear()
        ax = self.fig_fps.add_subplot(111)
        self._preparar_ejes(ax, "FPS en vivo", "segundos", "FPS")
        if t:
            ax.plot(t, list(self._hist_fps), color="#4fc3f7", linewidth=1.4)
        self.fig_fps.tight_layout()
        self.canvas_fps.draw_idle()

        self.fig_lat.clear()
        ax2 = self.fig_lat.add_subplot(111)
        self._preparar_ejes(ax2, "Latencia de inferencia (media por ventana)", "segundos", "ms")
        if t:
            ax2.plot(t, list(self._hist_lat), color="#ffb74d", linewidth=1.4)
        self.fig_lat.tight_layout()
        self.canvas_lat.draw_idle()

    def _dibujar_similitudes(self):
        scores = self.collector.scores()
        umbral = self.settings.similarity_threshold
        self.fig_sim.clear()
        ax = self.fig_sim.add_subplot(111)
        self._preparar_ejes(
            ax, "Distribucion de similitudes observadas", "similitud coseno", "frecuencia"
        )
        if scores.size:
            bins = min(40, max(10, scores.size // 5))
            ax.hist(scores[scores >= umbral], bins=bins, range=(0.0, 1.0),
                    color="#66bb6a", alpha=0.85, label=">= umbral")
            ax.hist(scores[scores < umbral], bins=bins, range=(0.0, 1.0),
                    color="#ef5350", alpha=0.85, label="< umbral")
            ax.axvline(umbral, color="#ffca28", linestyle="--", linewidth=1.4,
                       label="umbral = {:.2f}".format(umbral))
            ax.legend(loc="upper right", fontsize=8, facecolor=self._bg,
                      edgecolor=self._grid, labelcolor=self._text)
        else:
            ax.text(0.5, 0.5, "Sin observaciones", ha="center", va="center",
                    color=self._text)
        self.fig_sim.tight_layout()
        self.canvas_sim.draw_idle()

    # ---------------------------------------------------------------- acciones
    def _toggle_pausa(self):
        self._pausado = not self._pausado
        self.btn_pausar.setText("Reanudar" if self._pausado else "Pausar")

    def _reiniciar(self):
        self.collector.reset()
        self._hist_t.clear()
        self._hist_fps.clear()
        self._hist_lat.clear()
        self._tick_count = 0
        self.lbl_estado.setText("Metricas reiniciadas.")

    def _evaluar(self):
        if self._eval_thread is not None and self._eval_thread.isRunning():
            return
        if not os.path.exists(FACES_DB_PATH):
            self.lbl_eval_estado.setText("No se encontro faces.db en la raiz del proyecto.")
            return

        self.btn_evaluar.setEnabled(False)
        self.lbl_eval_estado.setText("Evaluando {} ...".format(os.path.basename(FACES_DB_PATH)))

        self._eval_thread = QtCore.QThread(self)
        self._eval_worker = _EvalWorker(FACES_DB_PATH, self.settings.similarity_threshold)
        self._eval_worker.moveToThread(self._eval_thread)
        self._eval_thread.started.connect(self._eval_worker.run)
        self._eval_worker.resultado.connect(self._on_evaluacion_terminada)
        self._eval_worker.error.connect(self._on_evaluacion_error)
        self._eval_worker.resultado.connect(self._eval_thread.quit)
        self._eval_worker.error.connect(self._eval_thread.quit)
        self._eval_thread.finished.connect(self._on_eval_liberar)
        self._eval_thread.start()

    def _on_eval_liberar(self):
        self.btn_evaluar.setEnabled(True)

    def _on_evaluacion_error(self, mensaje):
        self.lbl_eval_estado.setText("Error en la evaluacion: {}".format(mensaje))

    def _on_evaluacion_terminada(self, resultado):
        self._ultimo_resultado = resultado
        from core.evaluacion import _filas_metricas

        self.tabla.setRowCount(0)
        for etiqueta, valor in _filas_metricas(resultado):
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            self.tabla.setItem(fila, 0, QTableWidgetItem(str(etiqueta)))
            self.tabla.setItem(fila, 1, QTableWidgetItem(self._fmt_metrica(valor)))

        ver = resultado.get("verificacion", {}) or {}
        if "error" in ver:
            self.lbl_eval_estado.setText(ver["error"])
        else:
            auc = ver.get("auc")
            eer = ver.get("eer")
            self.lbl_eval_estado.setText(
                "Evaluacion lista: {} encodings, {} personas. AUC = {}, EER = {}.".format(
                    resultado.get("num_encodings"),
                    resultado.get("num_personas"),
                    self._fmt(auc, dec=4),
                    self._fmt(eer, dec=4),
                )
            )
        self._dibujar_roc(resultado)
        self._dibujar_distribuciones(resultado)

    def _fmt_metrica(self, valor):
        if valor is None:
            return "N/D"
        if isinstance(valor, float):
            return "{:.4f}".format(valor)
        return str(valor)

    def _dibujar_roc(self, resultado):
        ver = resultado.get("verificacion", {}) or {}
        self.fig_roc.clear()
        ax = self.fig_roc.add_subplot(111)
        self._preparar_ejes(ax, "Curva ROC (verificacion 1:1)", "FAR (FPR)", "TAR (TPR)")
        if "roc_fpr" in ver:
            ax.plot(ver["roc_fpr"], ver["roc_tpr"], color="#42a5f5", linewidth=1.6,
                    label="AUC = {:.4f}".format(ver.get("auc", 0.0)))
            ax.plot([0, 1], [0, 1], color=self._muted, linestyle=":", linewidth=1.0)
            ax.legend(loc="lower right", fontsize=8, facecolor=self._bg,
                      edgecolor=self._grid, labelcolor=self._text)
        else:
            ax.text(0.5, 0.5, ver.get("error", "Sin datos"), ha="center", va="center",
                    color=self._text, wrap=True)
        self.fig_roc.tight_layout()
        self.canvas_roc.draw_idle()

    def _dibujar_distribuciones(self, resultado):
        ver = resultado.get("verificacion", {}) or {}
        umbral = resultado.get("umbral_configurado", self.settings.similarity_threshold)
        self.fig_dist.clear()
        ax = self.fig_dist.add_subplot(111)
        self._preparar_ejes(
            ax, "Similitudes: genuinos vs impostores", "similitud coseno", "frecuencia"
        )
        if "genuinos" in ver:
            genuinos = ver["genuinos"]
            impostores = ver["impostores"]
            bins = 40
            ax.hist(genuinos, bins=bins, range=(-0.2, 1.0), color="#66bb6a",
                    alpha=0.75, label="genuinos ({})".format(len(genuinos)))
            ax.hist(impostores, bins=bins, range=(-0.2, 1.0), color="#ef5350",
                    alpha=0.75, label="impostores ({})".format(len(impostores)))
            ax.axvline(umbral, color="#ffca28", linestyle="--", linewidth=1.4,
                       label="umbral = {:.2f}".format(umbral))
            ax.legend(loc="upper center", fontsize=8, facecolor=self._bg,
                      edgecolor=self._grid, labelcolor=self._text)
        else:
            ax.text(0.5, 0.5, ver.get("error", "Sin datos"), ha="center", va="center",
                    color=self._text)
        self.fig_dist.tight_layout()
        self.canvas_dist.draw_idle()

    # --------------------------------------------------------------- exportar
    def _exportar(self):
        from core.evaluacion import _json_safe, _filas_metricas

        snap = self.collector.snapshot()
        reporte = {
            "contexto": contexto_inferencia(),
            "configuracion": {
                "umbral_similitud": self.settings.similarity_threshold,
                "confirmaciones_necesarias": self.settings.confirmations_needed,
                "intervalo_deteccion": self.settings.detection_interval,
                "resolucion_camara": self.settings.camera_resolution,
            },
            "rendimiento": snap,
            "sistema_ultimo": self._sistema,
            "evaluacion_exactitud": self._ultimo_resultado,
        }

        os.makedirs(REPORTES_DIR, exist_ok=True)
        marca = time.strftime("%Y%m%d_%H%M%S")
        ruta_json = os.path.join(REPORTES_DIR, "monitoreo_{}.json".format(marca))
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(_json_safe(reporte), f, ensure_ascii=False, indent=2)

        ruta_csv = os.path.join(REPORTES_DIR, "monitoreo_{}.csv".format(marca))
        with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["seccion", "metrica", "valor"])
            for clave, valor in snap.items():
                if isinstance(valor, (int, float)):
                    writer.writerow(["rendimiento", clave, valor])
            for clave, valor in self._sistema.items():
                writer.writerow(["sistema", clave, valor])
            if self._ultimo_resultado is not None:
                for etiqueta, valor in _filas_metricas(self._ultimo_resultado):
                    writer.writerow(["exactitud", etiqueta, valor])

        self.lbl_estado.setText("Reporte exportado a: {}".format(ruta_json))

    # ----------------------------------------------------------------- cierre
    def closeEvent(self, event):
        try:
            self.timer_ui.stop()
            self.timer_sistema.stop()
        except Exception:
            pass
        if self._eval_thread is not None and self._eval_thread.isRunning():
            self._eval_thread.quit()
            self._eval_thread.wait(3000)
        event.accept()

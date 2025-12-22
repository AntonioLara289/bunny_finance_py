# main_window.py
import random  # si no lo usas, elimínalo
from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QStatusBar, QMenu

from ui.consultas import Consultas
from ui.asistencia import AsistenciaPantalla
from ui.camera import CameraWidget
from ui.calculo import Calculo
from ui.visualizacionEncodings import UMAPViewer
from ui.escaneoRostro import EscanerRostro
from ui.Historial import Historial
from ui.animated_menu import AnimatedMenu

try:
    import mediapipe as mp
    print("MediaPipe importado correctamente")
except ImportError as e:
    print("Error de importación de MediaPipe:", e)
except Exception as e:
    print("Otro error con MediaPipe:", e)


class MainWindow(QtWidgets.QMainWindow):
    titulo_ventana = "Bunny Detect"

    def __init__(self, load_stylesheet_callback=None, parent=None) -> None:
        super().__init__(parent)

        self.load_stylesheet_callback = load_stylesheet_callback

        self.setWindowTitle(self.titulo_ventana)
        self.setGeometry(100, 100, 800, 600)

        # Status bar
        self.setStatusBar(QStatusBar(self))

        # StackedWidget como central
        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        # Pantalla inicial
        self.pantallaMostrandose = EscanerRostro()
        self.stack.addWidget(self.pantallaMostrandose)
        self.stack.setCurrentWidget(self.pantallaMostrandose)

        if hasattr(self.pantallaMostrandose, "onDestroy"):
            self.pantallaMostrandose.destroyed.connect(self.pantallaMostrandose.onDestroy)

        # Menús
        self._crear_menus()

    # =============================
    # MENÚS
    # =============================
    def _crear_menus(self) -> None:
        menu_bar = self.menuBar()

        # ---- Menú Opciones ----
        opciones_menu = AnimatedMenu("Opciones", self)
        menu_bar.addMenu(opciones_menu)
        self._crear_menu_opciones(opciones_menu)

        # ---- Menú Estilos ----
        estilos_menu = QMenu("Estilos", self)  # para probar sin AnimatedMenu
        menu_bar.addMenu(estilos_menu)
        self._crear_menu_estilos(estilos_menu)

        # ---- Menú Acerca ----
        acerca_menu = AnimatedMenu("Acerca", self)
        menu_bar.addMenu(acerca_menu)
        # Aquí podrías agregar un QAction "Acerca de..." que abra un QDialog

    def _crear_menu_opciones(self, menu) -> None:
        # Registro de rostro
        self._add_action(
            menu,
            text="Registro de rostro",
            tip="Escaneo de rostro con cámara",
            slot=self.mostrarVistaEscaneo,
        )

        menu.addSeparator()

        # Historial
        self._add_action(
            menu,
            text="Historial",
            tip="Historial de las detecciones",
            slot=self.mostrarVistaHistorial,
        )

        # Visualización Encodings
        self._add_action(
            menu,
            text="Visualización Encodings",
            tip="UMAP Encodings",
            slot=self.mostrarVistaVisualizarEncodings,
        )

        # Consultas
        self._add_action(
            menu,
            text="Consultas",
            tip="Consulta del registro de personas y estatus",
            slot=self.mostrarVistaConsultas,
        )

        # Asistencia
        self._add_action(
            menu,
            text="Asistencia",
            tip="Pantalla de toma de asistencia",
            slot=self.mostrarVistaAsistencia,
        )

        menu.addSeparator()

        # Salir
        self._add_action(
            menu,
            text="Salir",
            tip="Salir de la aplicación",
            slot=self.salir,
        )

    def _crear_menu_estilos(self, menu) -> None:
        estilos = [
            ("Aero", "Estilo Frutiger Aero", "styles/style.qss"),
            ("Aero Dark", "Estilo Frutiger Aero Dark", "styles/frutigerdark.qss"),
            ("Aero Green", "Estilo Frutiger Aero verde", "styles/aerogreen.qss"),
            ("Aero Sunset", "Estilo Frutiger Aero sunset", "styles/aerosunset.qss"),
            ("Aero Frost", "Estilo Frutiger Aero Frost", "styles/aerofrost.qss"),
            ("Aero Organic", "Estilo Frutiger Aero Organic", "styles/aeroorganic.qss"),
        ]

        for nombre, tip, path in estilos:
            # Capturamos la ruta en el lambda y luego _add_action la llamará sin parámetros extra
            self._add_action(
                menu,
                text=nombre,
                tip=tip,
                slot=lambda p=path: self._cambiar_estilo(p),
            )

    def _cambiar_estilo(self, path: str) -> None:
        import traceback
        print(f"[STYLE] Cambiando estilo a: {path!r}")
        if self.load_stylesheet_callback is not None:
            try:
                self.load_stylesheet_callback(path)
            except Exception as e:
                print("[ERROR] Excepción en load_stylesheet_callback:", e)
                traceback.print_exc()
        else:
            print(f"[WARN] No hay callback para cambiar estilos. Archivo: {path}")

    def _add_action(self, menu, text: str, tip: str, slot) -> QAction:
        action = QAction(text, self)
        action.setStatusTip(tip)
        # QAction.triggered(bool checked) → ignoramos 'checked' y llamamos al slot sin args
        action.triggered.connect(lambda checked=False, s=slot: s())
        menu.addAction(action)
        return action

    # =============================
    # ANIMACIÓN ENTRE VISTAS
    # =============================
    def animate_switch(self, new_widget: QtWidgets.QWidget) -> None:
        current = self.stack.currentWidget()
        new_widget.setGeometry(self.stack.geometry())

        self.stack.addWidget(new_widget)

        # Animación deslizante
        anim_slide = QtCore.QPropertyAnimation(new_widget, b"geometry")
        anim_slide.setDuration(300)
        anim_slide.setStartValue(
            self.stack.geometry().adjusted(self.width(), 0, self.width(), 0)
        )
        anim_slide.setEndValue(self.stack.geometry())
        anim_slide.setEasingCurve(QtCore.QEasingCurve.OutCubic)

        # Animación de opacidad
        effect = QtWidgets.QGraphicsOpacityEffect(new_widget)
        new_widget.setGraphicsEffect(effect)
        anim_fade = QtCore.QPropertyAnimation(effect, b"opacity")
        anim_fade.setDuration(300)
        anim_fade.setStartValue(0)
        anim_fade.setEndValue(1)
        anim_fade.setEasingCurve(QtCore.QEasingCurve.OutCubic)

        anim_slide.start()
        anim_fade.start()

        # Guardar referencias
        self._anim_slide = anim_slide
        self._anim_fade = anim_fade

        self.stack.setCurrentWidget(new_widget)

    # =============================
    # CAMBIO DE VISTAS
    # =============================
    def destroyActual(self) -> None:
        if getattr(self, "pantallaMostrandose", None):
            try:
                self.pantallaMostrandose.close()
                self.pantallaMostrandose.deleteLater()
            except Exception:
                pass
        self.pantallaMostrandose = None

    def _cambiar_vista(self, nueva_clase_widget) -> None:
        self.destroyActual()
        self.pantallaMostrandose = nueva_clase_widget()
        self.animate_switch(self.pantallaMostrandose)

    def mostrarVistaEscaneo(self) -> None:
        print("Mostrando la vista de escaneo")
        self._cambiar_vista(EscanerRostro)

    def mostrarVistaHistorial(self) -> None:
        print("Mostrando la vista de historial")
        self._cambiar_vista(Historial)

    def mostrarVistaVisualizarEncodings(self) -> None:
        print("Mostrando la vista de visualización Encodings")
        self._cambiar_vista(UMAPViewer)

    def mostrarVistaConsultas(self) -> None:
        print("Mostrando vista Consultas")
        self._cambiar_vista(Consultas)

    def mostrarVistaAsistencia(self) -> None:
        print("Mostrando vista Asistencia")
        self._cambiar_vista(AsistenciaPantalla)

    # =============================
    # OTROS
    # =============================
    def salir(self) -> None:
        self.destroyActual()
        QtWidgets.QApplication.quit()

    def mostrar_camara(self) -> None:
        self.cam_window = CameraWidget(self)
        modal = QtWidgets.QDialog(self)
        modal.setWindowTitle("Modal Dialog")
        modal_layout = QtWidgets.QVBoxLayout(modal)
        modal_label = QtWidgets.QLabel(
            "This is a modal dialog", alignment=QtCore.Qt.AlignCenter
        )
        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(modal.accept)

        modal_layout.addWidget(modal_label)
        modal_layout.addWidget(close_button)
        modal.exec()

    def calculo(self) -> None:
        self.calculo_obj = Calculo()
        self.calculo_obj.signalCalculo.connect(self.recibir_calculo)
        self.calculo_obj.enviarCalculo()

    def recibir_calculo(self, valor) -> None:
        print("El cálculo recibido desde cámara es:", valor)

import random  # si no lo usas, elimínalo
from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QStatusBar, QMenu
from PySide6.QtCore import QTimer
from datetime import datetime

from ui.consultas import Consultas
from ui.asistencia import AsistenciaPantalla
from ui.camera import CameraWidget
from ui.calculo import Calculo
from ui.visualizacionEncodings import UMAPViewer
from ui.escaneoRostro import EscanerRostro
from ui.preferencias import Preferencias
from ui.Historial import Historial
from ui.insightFacesDemo import FaceRecognitionView
from ui.PersonRegisterView import PersonRegisterView
from ui.sesiones import Sesiones
from ui.animated_menu import AnimatedMenu
from ui.acerca import Acerca
from database.db_manager import DBManager

class MainWindow(QtWidgets.QMainWindow):
    titulo_ventana = "Bunny Detect"

    def __init__(self, load_stylesheet_callback=None, parent=None) -> None:
        super().__init__(parent)

        self.load_stylesheet_callback = load_stylesheet_callback

        self.setWindowTitle(self.titulo_ventana)
        self.setGeometry(100, 100, 800, 600)

        # Barra de estatus
        self.setStatusBar(QStatusBar(self))

        # Centrar el StackedWidget
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

        # Sistema global de sesiones automáticas
        self.db = DBManager()
        self.active_session_id = None
        self._saved_attendance = set()
        self._prior_vista = None  # guardar vista anterior antes de sesión

        self.session_timer = QTimer(self)
        self.session_timer.timeout.connect(self._check_sessions_global)
        self.session_timer.start(30000)  # revisar cada 30s

    # MENÚS
    def _crear_menus(self) -> None:
        menu_bar = self.menuBar()

        # ---- Menú Opciones ----
        opciones_menu = AnimatedMenu("Opciones", self)
        menu_bar.addMenu(opciones_menu)
        self._crear_menu_opciones(opciones_menu)

        # ---- Menú Vistas ----
        vistas_menu = AnimatedMenu("Vistas", self)
        menu_bar.addMenu(vistas_menu)
        self._crear_menu_vistas(vistas_menu)

        # ---- Menú Acerca ----
        acerca_menu = AnimatedMenu("Acerca", self)
        menu_bar.addMenu(acerca_menu)
        self._crear_menu_data(acerca_menu)

    def _crear_menu_opciones(self, menu) -> None:
        # Preferencias
        self._add_action(
            menu,
            text="Preferencias",
            tip="Ver configuraciones generales",
            slot=self.mostrarVistaPreferencias,
        )

        menu.addSeparator()

        # Salir
        self._add_action(
            menu,
            text="Salir",
            tip="Salir de la aplicación",
            slot=self.salir,
        )

    def _crear_menu_vistas(self, menu) -> None:
        # Registro de rostro
        self._add_action(
            menu,
            text="Registro de rostro",
            tip="Escaneo de rostro con cámara",
            slot=self.mostrarVistaEscaneo,
        )

        menu.addSeparator()

        # Asistencia
        self._add_action(
            menu,
            text="Asistencia",
            tip="Pantalla de toma de asistencia",
            slot=self.mostrarVistaAsistencia,
        )

        # Sesiones
        self._add_action(
            menu,
            text="Sesiones",
            tip="Pantalla de asignacion de sesiones",
            slot=self.mostrarVistaSesiones,
        )

        # Consultas
        self._add_action(
            menu,
            text="Consultas",
            tip="Consulta del registro de personas y estatus",
            slot=self.mostrarVistaConsultas,
        )

        menu.addSeparator()

        # Historial SesionesPantalla
        self._add_action(
            menu,
            text="Historial",
            tip="Historial de las detecciones",
            slot=self.mostrarVistaHistorial,
        )

        # Visualización Encodings
        self._add_action(
            menu,
            text="Encodings",
            tip="UMAP Encodings",
            slot=self.mostrarVistaVisualizarEncodings,
        )

        menu.addSeparator()

        # InsightFaces
        self._add_action(
            menu,
            text="InsightFaces",
            tip="...",
            slot=self.mostrarVistaInsightFaces,
        )

        # InsightFacesRegister
        self._add_action(
            menu,
            text="InsightFaces Register",
            tip="...",
            slot=self.mostrarVistaInsightFacesRegister,
        )

    def _crear_menu_data(self, menu) -> None:
        # Pantalla acerca
        self._add_action(
            menu,
            text="Acerca",
            tip="Informacion del programa y licencias",
            slot=self.mostrarVistaAcerca,
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

    # ANIMACIÓN ENTRE VISTAS
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

    # CAMBIO DE VISTAS
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

    def mostrarVistaPreferencias(self) -> None:
        print("Mostrando la vista de Preferencias")
        self._cambiar_vista(Preferencias)

    def mostrarVistaEscaneo(self) -> None:
        print("Mostrando la vista de escaneo")
        self._cambiar_vista(EscanerRostro)

    def mostrarVistaHistorial(self) -> None:
        print("Mostrando la vista de historial")
        self._cambiar_vista(Historial)

    def mostrarVistaInsightFaces(self) -> None:
        print("Mostrando la vista de visualización Encodings")
        self._cambiar_vista(FaceRecognitionView)

    def mostrarVistaInsightFacesRegister(self) -> None:
        print("Mostrando la vista de visualización Encodings")
        self._cambiar_vista(PersonRegisterView)

    def mostrarVistaVisualizarEncodings(self) -> None:
        print("Mostrando la vista de visualización Encodings")
        self._cambiar_vista(UMAPViewer)

    def mostrarVistaConsultas(self) -> None:
        print("Mostrando vista Consultas")
        self._cambiar_vista(Consultas)

    def mostrarVistaSesiones(self) -> None:
        print("Mostrando la vista de historial")
        self._cambiar_vista(Sesiones)

    def mostrarVistaAsistencia(self) -> None:
        print("Mostrando vista Asistencia")
        self._cambiar_vista(AsistenciaPantalla)

    def mostrarVistaAcerca(self) -> None:
        print("Mostrando vista acerca")
        self._cambiar_vista(Acerca)

    # SESIONES AUTOMÁTICAS
    def _check_sessions_global(self) -> None:
        """Revisa si hay una sesión activa en este momento y navega automáticamente"""
        ahora = datetime.now().time()
        sesiones = self.db.getSesiones()

        found_active = None
        for id_sesion, nombre, inicio_str, fin_str in sesiones:
            try:
                inicio_time = datetime.strptime(inicio_str, "%H:%M").time()
                fin_time = datetime.strptime(fin_str, "%H:%M").time()
            except Exception:
                continue

            # Caso normal: inicio <= ahora < fin
            if inicio_time <= ahora < fin_time:
                found_active = (id_sesion, nombre)
                break

        # Si hay una sesión activa y no está ya abierta, navegar a asistencia
        if found_active and self.active_session_id != found_active[0]:
            self.active_session_id = found_active[0]
            self._prior_vista = self.pantallaMostrandose  # guardar vista anterior

            # Cambiar a AsistenciaPantalla con sesión activa
            self.destroyActual()
            self.pantallaMostrandose = AsistenciaPantalla(
                session_name=found_active[1],
                auto_start_camera=True,
                session_id=found_active[0]
            )
            self.animate_switch(self.pantallaMostrandose)

            # Reset saved attendance para esta sesión
            self._saved_attendance = set()

            # Poller para persistir asistencias
            self._attendance_poller = QTimer(self)
            self._attendance_poller.timeout.connect(self._persist_attendance_global)
            self._attendance_poller.start(1000)

        # Si no hay sesión activa pero antes sí, cerrar y volver
        if not found_active and self.active_session_id is not None:
            # Flush pending attendance
            try:
                self._persist_attendance_global()
            except Exception:
                pass

            if getattr(self, '_attendance_poller', None):
                try:
                    self._attendance_poller.stop()
                except Exception:
                    pass

            # Exportar automáticamente al cerrar sesión
            if self.pantallaMostrandose:
                try:
                    self.pantallaMostrandose.close()
                except Exception:
                    pass

            self.active_session_id = None

            # Volver a vista anterior (o a Sesiones si no hay)
            if self._prior_vista:
                try:
                    vista_anterior = self._prior_vista
                    self._prior_vista = None
                    self.destroyActual()
                    self.pantallaMostrandose = vista_anterior
                    self.animate_switch(self.pantallaMostrandose)
                except Exception:
                    self.mostrarVistaSesiones()
            else:
                self.mostrarVistaSesiones()

    def _persist_attendance_global(self) -> None:
        """Persiste asistencias confirmadas en la DB"""
        if not isinstance(self.pantallaMostrandose, AsistenciaPantalla):
            return

        nuevos = self.pantallaMostrandose.attendance_given - self._saved_attendance
        for persona_id in nuevos:
            try:
                self.db.guardarAsistencia(persona_id, self.active_session_id, True)
            except Exception:
                pass
            self._saved_attendance.add(persona_id)

    # OTROS
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

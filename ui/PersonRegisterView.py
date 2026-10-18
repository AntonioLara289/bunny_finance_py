from PySide6 import QtWidgets, QtCore, QtGui
from ui.top_bar import TopBar
from log import log
from ui.app_settings import AppSettings, set_banner_state

import os
import cv2
import sqlite3
import numpy as np
from insightface.app import FaceAnalysis

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "faces.db")


def get_ctx_id():
    import onnxruntime as ort
    if 'CUDAExecutionProvider' in ort.get_available_providers():
        return 0
    return -1


class PersonRegisterView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Registro de Personas")
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)
        log.push("Vista registro", "Abierto")

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        self.top_bar = TopBar("Registrar Persona")
        main_layout.addWidget(self.top_bar)

        subtitle = QtWidgets.QLabel(
            "Captura varias muestras del rostro para mejorar la precisión del reconocimiento."
        )
        subtitle.setObjectName("Hint")
        subtitle.setWordWrap(True)
        main_layout.addWidget(subtitle)

        input_frame = QtWidgets.QFrame()
        input_frame.setObjectName("Card")
        input_layout = QtWidgets.QVBoxLayout(input_frame)
        input_layout.setContentsMargins(14, 12, 14, 12)
        input_layout.setSpacing(8)

        name_label = QtWidgets.QLabel("Nombre de la persona")
        name_label.setObjectName("SectionTitle")
        input_layout.addWidget(name_label)

        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Escribe el nombre completo...")
        self.name_input.setMinimumHeight(34)
        input_layout.addWidget(self.name_input)

        main_layout.addWidget(input_frame)

        self.video_container = QtWidgets.QFrame()
        self.video_container.setObjectName("Card")
        video_layout = QtWidgets.QVBoxLayout(self.video_container)
        video_layout.setContentsMargins(8, 8, 8, 8)

        self.image_label = QtWidgets.QLabel()
        self.image_label.setObjectName("VideoFrame")
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setMinimumSize(320, 240)
        self.image_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.image_label.setScaledContents(False)
        video_layout.addWidget(self.image_label, stretch=1)

        main_layout.addWidget(self.video_container, stretch=1)

        self.capture_count_label = QtWidgets.QLabel("Capturas: 0")
        self.capture_count_label.setObjectName("Muted")
        self.capture_count_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(self.capture_count_label)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(12)

        self.capture_btn = QtWidgets.QPushButton("Capturar rostro")
        self.capture_btn.setMinimumHeight(44)
        self.capture_btn.setToolTip("Toma una muestra del rostro que aparece en la cámara")
        self.capture_btn.clicked.connect(self.capture_face)
        btn_layout.addWidget(self.capture_btn)

        self.save_btn = QtWidgets.QPushButton("Guardar en base de datos")
        self.save_btn.setProperty("variant", "success")
        self.save_btn.setMinimumHeight(44)
        self.save_btn.setToolTip("Guarda las muestras capturadas con el nombre indicado")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_person)
        btn_layout.addWidget(self.save_btn)

        main_layout.addLayout(btn_layout)

        self.status = QtWidgets.QLabel("Listo para registrar")
        self.status.setObjectName("StatusBanner")
        self.status.setAlignment(QtCore.Qt.AlignCenter)
        self.status.setProperty("state", "info")
        main_layout.addWidget(self.status)

        self.app = FaceAnalysis()
        self.app.prepare(ctx_id=get_ctx_id())

        self.conn = sqlite3.connect(DB_PATH)
        self.create_tables()

        self.cap = None
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.current_embeddings = []
        self.current_frame = None

        self.settings = AppSettings()
        self._init_camera_from_settings()

    def _init_camera_from_settings(self):
        cam_index = self.settings.camera_index
        res_str = self.settings.camera_resolution
        w, h = int(res_str.split("x")[0]), int(res_str.split("x")[1])

        self.cap = cv2.VideoCapture(cam_index)
        if not self.cap or not self.cap.isOpened():
            set_banner_state(self.status, "error", f"No se pudo abrir cámara [{cam_index}]")
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        self.timer.start(30)

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS encodings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            embedding BLOB
        )
        """)
        self.conn.commit()

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        self.current_frame = frame.copy()

        faces = self.app.get(frame)
        for face in faces:
            box = face.bbox.astype(int)
            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (137, 180, 250), 2)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QtGui.QImage(rgb.data, w, h, ch * w, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qt_img)
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)

    # Captura de rostro
    def capture_face(self):
        # Revisar que exista una camara
        if self.current_frame is None:
            set_banner_state(self.status, "warning", "Esperando cámara...")
            return

        faces = self.app.get(self.current_frame) 

        if len(faces) == 0:
            set_banner_state(self.status, "error", "No se detectó rostro")
            return

        emb = faces[0].embedding
        self.current_embeddings.append(emb)

        self.capture_count_label.setText(f"Capturas: {len(self.current_embeddings)}")
        self.save_btn.setEnabled(True)

        set_banner_state(
            self.status,
            "success",
            f"Rostro capturado ({len(self.current_embeddings)})",
        )

    def save_person(self):
        name = self.name_input.text().strip()

        if not name:
            set_banner_state(self.status, "warning", "Ingresa un nombre")
            return

        if len(self.current_embeddings) == 0:
            set_banner_state(self.status, "warning", "Captura al menos un rostro")
            return

        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO persons (name) VALUES (?)", (name,))
        person_id = cursor.lastrowid

        for emb in self.current_embeddings:
            blob = emb.tobytes()
            cursor.execute(
                "INSERT INTO encodings (person_id, embedding) VALUES (?, ?)",
                (person_id, blob)
            )

        self.conn.commit()

        log.push("Persona registrada", name)

        self.current_embeddings = []
        self.name_input.clear()
        self.capture_count_label.setText("Capturas: 0")
        self.save_btn.setEnabled(False)

        set_banner_state(self.status, "success", f"Guardado correctamente: {name}")

    def closeEvent(self, event):
        if self.cap:
            self.cap.release()
        self.timer.stop()
        self.conn.close()
        event.accept()

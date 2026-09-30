from PySide6 import QtWidgets, QtCore, QtGui
from ui.top_bar import TopBar
from log import log
from ui.app_settings import AppSettings, set_banner_state

import os
import cv2
import numpy as np
import sqlite3
from insightface.app import FaceAnalysis

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "faces.db")


def get_ctx_id():
    import onnxruntime as ort
    if 'CUDAExecutionProvider' in ort.get_available_providers():
        return 0
    return -1


class FaceRecognitionView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("InsightFace Demo")
        self.resize(900, 700)
        self.setMinimumSize(400, 300)

        self.settings = AppSettings()

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        self.top_bar = TopBar("Demo InsightFace")
        main_layout.addWidget(self.top_bar)

        self.status_label = QtWidgets.QLabel("Iniciando...")
        self.status_label.setObjectName("StatusBanner")
        self.status_label.setProperty("state", "info")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        self.video_label = QtWidgets.QLabel()
        self.video_label.setObjectName("VideoFrame")
        self.video_label.setAlignment(QtCore.Qt.AlignCenter)
        self.video_label.setMinimumSize(320, 240)
        main_layout.addWidget(self.video_label, stretch=1)

        # Panel de coincidencia
        self.info_frame = QtWidgets.QFrame()
        self.info_frame.setObjectName("Card")
        info_layout = QtWidgets.QVBoxLayout(self.info_frame)
        info_layout.setContentsMargins(14, 12, 14, 12)
        self.match_label = QtWidgets.QLabel("Esperando detección...")
        self.match_label.setObjectName("SectionTitle")
        self.match_label.setAlignment(QtCore.Qt.AlignCenter)
        info_layout.addWidget(self.match_label)

        main_layout.addWidget(self.info_frame)

        self.app = FaceAnalysis()
        self.app.prepare(ctx_id=get_ctx_id())

        self.conn = sqlite3.connect(DB_PATH)
        self.known_embeddings, self.known_names = self.load_database()

        self.cap = None
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.threshold = self.settings.similarity_threshold
        self._best_sim = -1.0

        self._init_camera_from_settings()

    def _init_camera_from_settings(self):
        cam_index = self.settings.camera_index
        res_str = self.settings.camera_resolution
        w, h = int(res_str.split("x")[0]), int(res_str.split("x")[1])

        self.cap = cv2.VideoCapture(cam_index)
        if not self.cap or not self.cap.isOpened():
            set_banner_state(self.status_label, "error", f"No se pudo abrir cámara [{cam_index}]")
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        set_banner_state(self.status_label, "info", "Buscando rostro...")
        self.timer.start(30)

    def load_database(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT persons.name, encodings.embedding
        FROM encodings
        JOIN persons ON persons.id = encodings.person_id
        """)

        embeddings = []
        names = []

        for name, blob in cursor.fetchall():
            emb = np.frombuffer(blob, dtype=np.float32)
            embeddings.append(emb)
            names.append(name)

        log.push("DB cargada", f"{len(embeddings)} embeddings")
        return embeddings, names

    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def find_match(self, embedding):
        best_sim = -1
        best_name = "Unknown"

        for db_emb, name in zip(self.known_embeddings, self.known_names):
            sim = self.cosine_similarity(embedding, db_emb)
            if sim > best_sim:
                best_sim = sim
                best_name = name

        return best_name, best_sim

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        faces = self.app.get(frame)

        recognized_any = False
        best_label = ""
        self._best_sim = -1.0

        for face in faces:
            name, sim = self.find_match(face.embedding)
            box = face.bbox.astype(int)

            if sim > self.threshold:
                recognized_any = True
                color = (0, 255, 0)
                label = f"{name} ({sim:.2f})"
            else:
                color = (0, 0, 255)
                label = f"Unknown ({sim:.2f})"

            if sim > self._best_sim:
                self._best_sim = sim
                best_label = label

            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2)
            cv2.rectangle(frame, (box[0], box[1] - 25), (box[0] + 200, box[1]), color, cv2.FILLED)
            cv2.putText(frame, label, (box[0] + 6, box[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        if recognized_any:
            set_banner_state(self.status_label, "success", "Rostro reconocido")
            self.match_label.setText(f"Coincidencia: {best_label}")
        else:
            set_banner_state(self.status_label, "info", "Buscando rostro...")
            self.match_label.setText("Sin coincidencias")

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QtGui.QImage(rgb.data, w, h, ch * w, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qt_img)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        if self.cap:
            self.cap.release()
        self.timer.stop()
        self.conn.close()
        event.accept()

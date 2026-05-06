from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QSizePolicy
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
import os
import cv2
import numpy as np
from insightface.app import FaceAnalysis
from cv2_enumerate_cameras import enumerate_cameras
from ui.dialogs.camarasDisponibles import CamarasDisponibles

# BASE DE DATOS UTILIZADA
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "faces.db")


def get_ctx_id():
    import onnxruntime as ort
    providers = ort.get_available_providers()
    if 'CUDAExecutionProvider' in providers:
        print("[INFO] InsightFace: Using CUDA GPU acceleration")
        return 0
    elif 'DmlExecutionProvider' in providers:
        print("[INFO] InsightFace: Using DirectML (AMD/Integrated GPU)")
        return 0
    else:
        print("[INFO] InsightFace: Using CPU mode")
        return -1


class CameraInsightFaceWidget(QWidget):
    personaConfirmada = Signal(str, int, float)

    def __init__(self, parent=None, encodings_db=None, names_db=None, ids_db=None):
        super().__init__(parent)

        self.names_db = names_db or []
        self.ids_db = ids_db or []

        if encodings_db and len(encodings_db) > 0:
            self.known_embeddings = np.array(encodings_db, dtype=np.float32)
        else:
            self.known_embeddings = np.empty((0, 512), dtype=np.float32)

        self.layout = QVBoxLayout(self)
        self.cam_label = QLabel("Cámara apagada", self)
        self.cam_label.setAlignment(Qt.AlignCenter)
        self.cam_label.setMinimumSize(320, 240)
        self.cam_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cam_label.setStyleSheet("background-color: #000; border-radius: 8px;")
        self.layout.addWidget(self.cam_label, stretch=1)

        self.btn_open = QPushButton("Abrir cámara", self)
        self.btn_close = QPushButton("Cerrar cámara", self)
        self.btn_close.hide()

        self.layout.addWidget(self.btn_open)
        self.layout.addWidget(self.btn_close)

        self.btn_open.clicked.connect(self.start_camera)
        self.btn_close.clicked.connect(self.stop_camera)

        self.setAttribute(Qt.WA_DeleteOnClose, True)

        self.app = FaceAnalysis()
        self.app.prepare(ctx_id=get_ctx_id())

        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        self.SIMILARITY_THRESHOLD = 0.5
        self.confirmations_needed = 2

        self.confirmations = {}
        self.confirmed_set = set()
        self.frame_counter = 0
        self.detection_interval = 3
        self.last_faces = []
        self.camera_index = 0

    def start_camera(self):
        if self.cap and self.cap.isOpened():
            return

        camaras_disponibles = []
        for camera_info in enumerate_cameras():
            camaras_disponibles.append({"index": camera_info.index, "nombre": camera_info.name})

        camaras_disponibles = list({c['nombre']: c for c in camaras_disponibles}.values())

        if not camaras_disponibles:
            self.cam_label.setText("No se encontraron cámaras")
            return

        modal = CamarasDisponibles(camaras_disponibles=camaras_disponibles)
        resultado = modal.exec()

        if resultado != CamarasDisponibles.Accepted:
            self.cam_label.setText("Selección de cámara cancelada")
            return

        camara_seleccionada = camaras_disponibles[modal.getCurrentIndexCombox()]
        self.camera_index = camara_seleccionada["index"]

        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            self.cam_label.setText("No se pudo abrir la cámara")
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        self.btn_open.hide()
        self.btn_close.show()
        self.timer.start(30)
        self.confirmations.clear()
        self.confirmed_set.clear()
        self.last_faces = []
        self.frame_counter = 0

    def stop_camera(self):
        if self.timer.isActive():
            self.timer.stop()

        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.cap = None

        self.cam_label.clear()
        self.cam_label.setText("Cámara apagada")

        self.btn_open.show()
        self.btn_close.hide()
        self.confirmations.clear()
        self.confirmed_set.clear()
        self.last_faces = []

    def find_match_batch(self, embedding):
        if len(self.known_embeddings) == 0:
            return "Desconocido", 0.0, -1

        norms_query = np.linalg.norm(embedding)
        norms_db = np.linalg.norm(self.known_embeddings, axis=1)
        similarities = (self.known_embeddings @ embedding) / (norms_db * norms_query)

        best_idx = int(np.argmax(similarities))
        best_sim = float(similarities[best_idx])
        best_name = self.names_db[best_idx]
        best_id = self.ids_db[best_idx]

        return best_name, best_sim, best_id

    def update_frame(self):
        if not self.cap or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        self.frame_counter += 1

        if self.frame_counter % self.detection_interval == 0:
            faces = self.app.get(frame)
            self.last_faces = faces
        else:
            faces = self.last_faces

        for face in faces:
            name, sim, id_ = self.find_match_batch(face.embedding)
            box = face.bbox.astype(int)

            if sim >= self.SIMILARITY_THRESHOLD:
                color = (0, 255, 0)
                label = f"{name} ({sim*100:.1f}%)"

                if id_ not in self.confirmations:
                    self.confirmations[id_] = {"count": 0, "name": name}
                self.confirmations[id_]["count"] += 1

                if self.confirmations[id_]["count"] >= self.confirmations_needed and id_ not in self.confirmed_set:
                    self.confirmed_set.add(id_)
                    sim_percent = sim * 100
                    self.personaConfirmada.emit(name, id_, sim_percent)
                    print(f"PERSONA CONFIRMADA: {name} - {sim_percent:.1f}%")
            else:
                color = (0, 0, 255)
                label = f"Desconocido ({sim*100:.1f}%)"
                if id_ in self.confirmations:
                    self.confirmations[id_]["count"] = max(0, self.confirmations[id_]["count"] - 1)

            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2)
            label_w = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0][0] + 12
            cv2.rectangle(frame, (box[0], box[1] - 25), (box[0] + label_w, box[1]), color, cv2.FILLED)
            cv2.putText(frame, label, (box[0] + 6, box[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_image = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.cam_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.cam_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        self.stop_camera()
        event.accept()

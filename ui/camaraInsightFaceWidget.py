from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
import os
import cv2
import numpy as np
from insightface.app import FaceAnalysis
from cv2_enumerate_cameras import enumerate_cameras
from ui.dialogs.camarasDisponibles import CamarasDisponibles
from ui.app_settings import AppSettings

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

    def __init__(self, parent=None, encodings_db=None, names_db=None, ids_db=None, detection_interval=None):
        super().__init__(parent)

        self.settings = AppSettings()

        self.known_embeddings = np.array([])
        self.names_db = names_db or []
        self.ids_db = ids_db or []

        if encodings_db is not None and len(encodings_db) > 0:
            self.known_embeddings = np.array(encodings_db, dtype=np.float32)

        self.cam_label = QLabel("Iniciando cámara...")
        self.cam_label.setAlignment(Qt.AlignCenter)
        self.cam_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.cam_label)

        self.setAttribute(Qt.WA_DeleteOnClose, True)

        self.app = FaceAnalysis()
        self.app.prepare(ctx_id=get_ctx_id())

        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        self.SIMILARITY_THRESHOLD = self.settings.similarity_threshold
        self.confirmations_needed = self.settings.confirmations_needed

        self.confirmations = {}
        self.confirmed_set = set()
        self.frame_counter = 0
        self.detection_interval = detection_interval or self.settings.detection_interval
        self.last_faces = []
        self.camera_index = 0

        self.settings.settings_changed.connect(self._on_settings_changed)

    def start_camera(self, auto_select=False):
        if self.cap and self.cap.isOpened():
            return

        camaras_disponibles = []
        for camera_info in enumerate_cameras():
            camaras_disponibles.append({"index": camera_info.index, "nombre": camera_info.name})

        camaras_disponibles = list({c['nombre']: c for c in camaras_disponibles}.values())

        if not camaras_disponibles:
            self.cam_label.setText("No se encontraron cámaras")
            return

        if auto_select:
            idx = self.settings.camera_index
            candidates = [c for c in camaras_disponibles if c["index"] == idx]
            if candidates:
                camara_seleccionada = candidates[0]
            else:
                camara_seleccionada = camaras_disponibles[0]
        else:
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

        res_str = self.settings.camera_resolution
        w, h = int(res_str.split("x")[0]), int(res_str.split("x")[1])
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

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

        self.confirmations.clear()
        self.confirmed_set.clear()
        self.last_faces = []

    def _on_settings_changed(self, key):
        self.SIMILARITY_THRESHOLD = self.settings.similarity_threshold
        self.confirmations_needed = self.settings.confirmations_needed
        self.detection_interval = self.settings.detection_interval

        res_str = self.settings.camera_resolution
        w, h = int(res_str.split("x")[0]), int(res_str.split("x")[1])
        if self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

        # If camera index changed, reopen
        new_idx = self.settings.camera_index
        if self.camera_index != new_idx:
            was_running = self.cap is not None and self.cap.isOpened()
            if was_running:
                self.stop_camera()
            self.camera_index = new_idx
            if was_running:
                self.start_camera(auto_select=True)

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
        # Scale using label's size (no smooth transformation = faster)
        scaled_pixmap = pixmap.scaled(
            self.cam_label.size(),
            Qt.KeepAspectRatio,
            Qt.FastTransformation
        )
        self.cam_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        self.stop_camera()
        event.accept()

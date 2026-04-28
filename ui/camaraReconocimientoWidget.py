from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
import cv2
import numpy as np
from insightface.app import FaceAnalysis


class CameraRecognitionWidget(QWidget):
    personaConfirmada = Signal(str, int, float)

    def __init__(self, parent=None, encodings_db=None, names_db=None, ids_db=None):
        super().__init__(parent)

        self.encodings_db = encodings_db or []
        self.names_db = names_db or []
        self.ids_db = ids_db or []

        self.layout = QVBoxLayout(self)
        self.cam_label = QLabel("Cámara apagada", self)
        self.cam_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.cam_label)

        self.btn_open = QPushButton("Abrir cámara", self)
        self.btn_close = QPushButton("Cerrar cámara", self)
        self.btn_close.hide()

        self.layout.addWidget(self.btn_open)
        self.layout.addWidget(self.btn_close)

        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        self.btn_open.clicked.connect(self.start_camera)
        self.btn_close.clicked.connect(self.stop_camera)

        self.setAttribute(Qt.WA_DeleteOnClose, True)

        self.confirmaciones = {}
        self.confirmaciones_necesarias = 2
        self.frame_counter = 0
        self.encoding_pesado_usado = {}

        self.last_locations = []
        self.last_labels = []
        self.last_colors = []

        self.app = None

    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def start_camera(self):
        if self.cap and self.cap.isOpened():
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.cam_label.setText("No se pudo abrir la cámara")
            return

        self.btn_open.hide()
        self.btn_close.show()
        self.timer.start(50)
        self.confirmaciones.clear()
        self.encoding_pesado_usado.clear()
        self.last_locations = []
        self.last_labels = []
        self.last_colors = []

        try:
            self.app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            print("InsightFace inicializado en CameraRecognitionWidget")
        except Exception as e:
            print(f"Error inicializando InsightFace: {e}")
            self.app = None

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
        self.confirmaciones.clear()
        self.encoding_pesado_usado.clear()
        self.last_locations = []
        self.last_labels = []
        self.last_colors = []

    def update_frame(self):
        if not self.cap or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        self.frame_counter += 1

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        procesar_deteccion = self.frame_counter % 2 == 0
        procesar_recalculo = self.frame_counter % 15 == 0

        if procesar_deteccion and self.app is not None:
            try:
                faces = self.app.get(rgb)

                if len(faces) > 0:
                    if procesar_recalculo:
                        face_encodings = [face.embedding for face in faces]
                        
                        self.last_locations = []
                        self.last_labels = []
                        self.last_colors = []

                        for face in faces:
                            embedding = face.embedding
                            best_sim = -1
                            best_name = "Desconocido"
                            best_id = -1

                            for i, db_emb in enumerate(self.encodings_db):
                                sim = self.cosine_similarity(embedding, db_emb)
                                if sim > best_sim:
                                    best_sim = sim
                                    best_name = self.names_db[i]
                                    best_id = self.ids_db[i]

                            box = face.bbox.astype(int)

                            if best_sim > 0.5:
                                if best_id not in self.confirmaciones:
                                    self.confirmaciones[best_id] = {"count": 0, "name": best_name}

                                self.confirmaciones[best_id]["count"] += 1

                                if self.confirmaciones[best_id]["count"] >= self.confirmaciones_necesarias:
                                    if best_id not in self.encoding_pesado_usado:
                                        print(f"PERSONA CONFIRMADA: {best_name} - {best_sim * 100:.1f}%")
                                        self.personaConfirmada.emit(best_name, best_id, best_sim * 100)
                                    self.confirmaciones[best_id]["count"] += 1

                                label = f"{best_name} ({best_sim * 100:.0f}%)"
                                color = (0, 255, 0)
                            else:
                                label = "Nuevo"
                                color = (0, 165, 255)
                                self.confirmaciones.clear()

                            self.last_locations.append(box)
                            self.last_labels.append(label)
                            self.last_colors.append(color)
                    else:
                        for face in faces:
                            box = face.bbox.astype(int)
                            self.last_locations.append(box)

                    for box, label, color in zip(self.last_locations, self.last_labels, self.last_colors):
                        cv2.rectangle(rgb, (box[0], box[1]), (box[2], box[3]), color, 2)
                        cv2.putText(rgb, label, (box[0], box[1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                else:
                    self.confirmaciones.clear()
                    self.last_locations = []
                    self.last_labels = []
                    self.last_colors = []

            except Exception as e:
                print(f"Error en update_frame: {e}")

        elif self.last_locations:
            for box, label, color in zip(self.last_locations, self.last_labels, self.last_colors):
                cv2.rectangle(rgb, (box[0], box[1]), (box[2], box[3]), color, 2)
                cv2.putText(rgb, label, (box[0], box[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.cam_label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        self.stop_camera()
        event.accept()
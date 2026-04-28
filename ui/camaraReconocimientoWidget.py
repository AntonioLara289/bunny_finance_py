from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
import cv2
import face_recognition
import numpy as np


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

        procesar_deteccion = self.frame_counter % 3 == 0
        procesar_recalculo = self.frame_counter % 15 == 0

        if procesar_deteccion or procesar_recalculo:
            face_locations = face_recognition.face_locations(rgb, model="CNN")

            if len(face_locations) > 0:
                if procesar_recalculo:
                    face_encodings = face_recognition.face_encodings(rgb, face_locations, num_jitters=5, model="large")
                    self.last_locations = []
                    self.last_labels = []
                    self.last_colors = []

                    for loc, encoding in zip(face_locations, face_encodings):
                        name = "Desconocido"
                        color = (0, 0, 255)
                        similarity = 0.0
                        id_ = -1

                        if self.encodings_db:
                            face_distances = face_recognition.face_distance(self.encodings_db, encoding)
                            best_match_index = np.argmin(face_distances) if len(face_distances) > 0 else None

                            if best_match_index is not None and face_distances[best_match_index] < 0.4:
                                name = self.names_db[best_match_index]
                                id_ = self.ids_db[best_match_index]
                                similarity = round((1 - face_distances[best_match_index]) * 100, 2)
                                color = (0, 255, 0)

                                if id_ not in self.confirmaciones:
                                    self.confirmaciones[id_] = {"count": 0, "name": name}

                                self.confirmaciones[id_]["count"] += 1

                                if self.confirmaciones[id_]["count"] >= self.confirmaciones_necesarias:
                                    if id_ not in self.encoding_pesado_usado:
                                        similitud_confirmada = self.confirmar_con_encoding_pesado(frame, loc, id_)
                                        if similitud_confirmada is not None:
                                            print(f"PERSONA CONFIRMADA: {name} - {similitud_confirmada:.1f}%")
                                            self.personaConfirmada.emit(name, id_, similitud_confirmada)
                                        self.encoding_pesado_usado[id_] = True
                                    self.confirmaciones[id_]["count"] += 1
                            else:
                                for key in list(self.confirmaciones.keys()):
                                    self.confirmaciones[key]["count"] = max(0, self.confirmaciones[key]["count"] - 1)

                        self.last_locations.append(loc)
                        self.last_labels.append(f"{name} {similarity:.1f}%")
                        self.last_colors.append(color)
                else:
                    self.last_locations = face_locations

                for loc, label, color in zip(self.last_locations, self.last_labels, self.last_colors):
                    top, right, bottom, left = loc
                    cv2.rectangle(rgb, (left, top), (right, bottom), color, 2)
                    cv2.putText(rgb, label, (left, top - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            else:
                self.confirmaciones.clear()
                self.last_locations = []
                self.last_labels = []
                self.last_colors = []

        elif self.last_locations:
            for loc, label, color in zip(self.last_locations, self.last_labels, self.last_colors):
                top, right, bottom, left = loc
                cv2.rectangle(rgb, (left, top), (right, bottom), color, 2)
                cv2.putText(rgb, label, (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.cam_label.setPixmap(QPixmap.fromImage(qt_image))

    def confirmar_con_encoding_pesado(self, frame, face_location, persona_id):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encoding_pesado = face_recognition.face_encodings(
            rgb,
            [face_location],
            num_jitters=100,
            model="large"
        )

        if encoding_pesado:
            indices_persona = [i for i, pid in enumerate(self.ids_db) if pid == persona_id]
            distancias = face_recognition.face_distance([self.encodings_db[i] for i in indices_persona], encoding_pesado[0])
            distancia_minima = np.min(distancias)
            similitud = (1 - distancia_minima) * 100
            return similitud
        return None

    def closeEvent(self, event):
        self.stop_camera()
        event.accept()

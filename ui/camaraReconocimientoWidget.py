from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
import cv2
import face_recognition
import mediapipe as mp
import numpy as np


class CameraRecognitionWidget(QWidget):
    faceRecognized = Signal(str, int, float)  # nombre, id, similaridad

    def __init__(self, parent=None, encodings_db=None, names_db=None, ids_db=None, encodings_agrupados=None):
        super().__init__(parent)

        # Datos conocidos (de DB)
        self.encodings_db = encodings_db or []
        self.names_db = names_db or []
        self.ids_db = ids_db or []
        self.encodings_agrupados = encodings_agrupados

        # UI
        self.layout = QVBoxLayout(self)
        self.cam_label = QLabel("Cámara apagada", self)
        self.cam_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.cam_label)

        self.btn_open = QPushButton("Abrir cámara", self)
        self.btn_close = QPushButton("Cerrar cámara", self)
        self.btn_close.hide()

        self.layout.addWidget(self.btn_open)
        self.layout.addWidget(self.btn_close)

        # Mediapipe y Face Recognition
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(min_detection_confidence=0.8)

        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        # Conexiones
        self.btn_open.clicked.connect(self.start_camera)
        self.btn_close.clicked.connect(self.stop_camera)

        self.setAttribute(Qt.WA_DeleteOnClose, True)  # ensures cleanup on close

    def start_camera(self):
        if self.cap and self.cap.isOpened():
            return  # already running

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.cam_label.setText("No se pudo abrir la cámara")
            return

        self.btn_open.hide()
        self.btn_close.show()
        self.timer.start(33)  # ~30 FPS

    def stop_camera(self):
        # stop timer first
        if self.timer.isActive():
            self.timer.stop()

        # release camera safely
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.cap = None

        # clear frame
        self.cam_label.clear()
        self.cam_label.setText("Cámara apagada")

        self.btn_open.show()
        self.btn_close.hide()

    def update_frame(self):
        if not self.cap or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Use smaller frame for faster detection (optional)
        small_frame = cv2.resize(rgb, (0, 0), fx=0.5, fy=0.5)
        results = self.face_detection.process(small_frame)
        face_locations = face_recognition.face_locations(small_frame)
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)

        for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
            # Scale back up to original size
            top *= 2
            right *= 2
            bottom *= 2
            left *= 2

            name = "Desconocido"
            color = (0, 0, 255)
            similarity = 0.0
            id_ = -1

            # Estrategia de comparación por promedio por persona (nueva)
            if self.encodings_agrupados and len(self.encodings_agrupados) > 0:
                mejor_distancia = float('inf')
                mejor_persona_id = None
                mejor_nombre = "Desconocido"
                
                # Iterar sobre cada persona en la base de datos
                for persona_id, encodings_lista in self.encodings_agrupados.items():
                    # Calcular distancias para los 3 perfiles de esta persona
                    if len(encodings_lista) == 0:
                        continue
                        
                    # Convertir a array numpy para face_distance
                    encodings_array = np.array(encodings_lista)
                    distancias = face_recognition.face_distance(encodings_array, encoding)
                    
                    # Calcular distancia promedio para esta persona
                    distancia_promedio = np.mean(distancias)
                    
                    # Mantener el mejor (menor distancia promedio)
                    if distancia_promedio < mejor_distancia:
                        mejor_distancia = distancia_promedio
                        mejor_persona_id = persona_id
                        # Buscar el nombre correspondiente al ID
                        if self.ids_db and persona_id in self.ids_db:
                            idx = self.ids_db.index(persona_id)
                            mejor_nombre = self.names_db[idx]
                
                # Umbral estricto para 90% de similitud (distancia < 0.1)
                if mejor_distancia < 0.1:
                    name = mejor_nombre
                    id_ = mejor_persona_id
                    color = (0, 255, 0)
                    similarity = round((1 - mejor_distancia) * 100, 2)
                    self.faceRecognized.emit(name, id_, similarity)
            
            # Fallback: usar estructura plana antigua si no hay agrupada
            elif self.encodings_db:
                matches = face_recognition.compare_faces(self.encodings_db, encoding)
                face_distances = face_recognition.face_distance(self.encodings_db, encoding)
                best_match_index = np.argmin(face_distances) if len(face_distances) > 0 else None

                if best_match_index is not None and matches[best_match_index]:
                    name = self.names_db[best_match_index]
                    id_ = self.ids_db[best_match_index]
                    color = (0, 255, 0)
                    similarity = round((1 - face_distances[best_match_index]) * 100, 2)
                    self.faceRecognized.emit(name, id_, similarity)

            cv2.rectangle(rgb, (left, top), (right, bottom), color, 2)
            cv2.putText(rgb, f"{name} {similarity:.1f}%", (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # Convert frame for QLabel
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.cam_label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        """Stop camera safely when the widget is closed or replaced."""
        self.stop_camera()
        event.accept()

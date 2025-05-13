# camera_widget.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
import cv2
import mediapipe as mp
import face_recognition
import numpy as np

class CameraWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.label = QLabel("Iniciando cámara...")
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.label.setText("❌ No se pudo abrir la cámara.")
            return

        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(min_detection_confidence=0.5)
        self.mp_drawing = mp.solutions.drawing_utils

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_frame)

        if results.detections:
            h, w, _ = rgb_frame.shape

            for detection in results.detections:
                # Dibujar la detección
                self.mp_drawing.draw_detection(rgb_frame, detection)

                # Obtener bbox relativa
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)

                # Asegurar que los valores estén dentro del frame
                x = max(0, x)
                y = max(0, y)
                x2 = min(w, x + width)
                y2 = min(h, y + height)

                # Recortar rostro
                face_crop = rgb_frame[y:y2, x:x2]

                # Obtener embeddings faciales
                face_encodings = face_recognition.face_encodings(face_crop)
                if face_encodings:
                    # print("🧬 Embedding facial (vector de 128D):")
                    # print(face_encodings[0])  # Puedes guardarlo en DB o compararlo
                    height

        # Convertir para mostrar en QLabel
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        self.cap.release()
        self.timer.stop()
        super().closeEvent(event)

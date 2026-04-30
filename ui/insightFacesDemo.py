from PySide6 import QtWidgets, QtCore, QtGui
from ui.top_bar import TopBar
from log import log
from ui.dialogs.camarasDisponibles import CamarasDisponibles

import cv2
import numpy as np
import sqlite3
from insightface.app import FaceAnalysis
from cv2_enumerate_cameras import enumerate_cameras


class FaceRecognitionView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Reconocimiento Facial")
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)
        log.push("Vista reconocimiento", "Abierto")

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        self.top_bar = TopBar("Reconocimiento Facial")
        main_layout.addWidget(self.top_bar)

        self.status_label = QtWidgets.QLabel("Cargando modelo...")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: 600;
                padding: 10px 20px;
                border-radius: 8px;
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
        """)
        main_layout.addWidget(self.status_label)

        self.video_container = QtWidgets.QFrame()
        self.video_container.setStyleSheet("""
            QFrame {
                background-color: #11111b;
                border: 2px solid #313244;
                border-radius: 12px;
            }
        """)
        video_layout = QtWidgets.QVBoxLayout(self.video_container)
        video_layout.setContentsMargins(8, 8, 8, 8)

        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setMinimumSize(640, 480)
        self.image_label.setStyleSheet("background-color: #000; border-radius: 8px;")
        self.image_label.setScaledContents(False)
        video_layout.addWidget(self.image_label)

        main_layout.addWidget(self.video_container, stretch=1)

        self.info_frame = QtWidgets.QFrame()
        self.info_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e2e;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        info_layout = QtWidgets.QHBoxLayout(self.info_frame)

        self.match_label = QtWidgets.QLabel("Sin coincidencias")
        self.match_label.setAlignment(QtCore.Qt.AlignCenter)
        self.match_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #a6adc8;
                padding: 8px;
            }
        """)
        info_layout.addWidget(self.match_label)

        main_layout.addWidget(self.info_frame)

        self.app = FaceAnalysis()
        self.app.prepare(ctx_id=0)

        self.conn = sqlite3.connect("faces.db")
        self.known_embeddings, self.known_names = self.load_database()

        self.cap = None
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.select_camera()

    def select_camera(self):
        camaras_disponibles = []
        for camera_info in enumerate_cameras():
            camara = {"index": camera_info.index, "nombre": camera_info.name}
            camaras_disponibles.append(camara)
            print(f"Index: {camera_info.index}, Name: {camera_info.name}")

        camaras_disponibles = list({c['nombre']: c for c in camaras_disponibles}.values())

        modal = CamarasDisponibles(camaras_disponibles=camaras_disponibles)
        resultado = modal.exec()

        if resultado == QtWidgets.QDialog.Accepted:
            camara_seleccionada = camaras_disponibles[modal.getCurrentIndexCombox()]
            print(f"Camera selected: {camara_seleccionada['nombre']}")
        else:
            print("Camera selection cancelled")
            self.status_label.setText("No se seleccionó cámara")
            return

        self.cap = cv2.VideoCapture(camara_seleccionada["index"])
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.status_label.setText("Buscando rostro...")
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

        for face in faces:
            name, sim = self.find_match(face.embedding)
            box = face.bbox.astype(int)

            if sim > 0.5:
                recognized_any = True
                color = (0, 255, 0)
                label = f"{name} ({sim:.2f})"
            else:
                color = (0, 0, 255)
                label = f"Unknown ({sim:.2f})"

            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2)
            cv2.rectangle(frame, (box[0], box[1] - 25), (box[0] + 200, box[1]), color, cv2.FILLED)
            cv2.putText(frame, label, (box[0] + 6, box[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        if recognized_any:
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 15px;
                    font-weight: 600;
                    padding: 10px 20px;
                    border-radius: 8px;
                    background-color: #a6e3a1;
                    color: #1e1e2e;
                }
            """)
            self.status_label.setText("Rostro reconocido")
            self.match_label.setText(f"Match: {label}")
            self.match_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #a6e3a1;
                    padding: 8px;
                    font-weight: 600;
                }
            """)
        else:
            self.status_label.setStyleSheet("""
                QLabel {
                    font-size: 15px;
                    font-weight: 600;
                    padding: 10px 20px;
                    border-radius: 8px;
                    background-color: #1e1e2e;
                    color: #cdd6f4;
                }
            """)
            self.status_label.setText("Buscando rostro...")
            self.match_label.setText("Sin coincidencias")
            self.match_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #a6adc8;
                    padding: 8px;
                }
            """)

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

    def closeEvent(self, event):
        if self.cap:
            self.cap.release()
        self.timer.stop()
        self.conn.close()
        event.accept()

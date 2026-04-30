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
        log.push("Vista reconocimiento", "Abierto")

        layout = QtWidgets.QVBoxLayout(self)

        # TOP BAR
        self.top_bar = TopBar("Reconocimiento Facial")
        layout.addWidget(self.top_bar)

        # Label de estado
        self.status_label = QtWidgets.QLabel("Cargando modelo...")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Webcam display
        self.image_label = QtWidgets.QLabel()
        self.image_label.setFixedHeight(400)
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.image_label)

        # InsightFace
        self.app = FaceAnalysis()
        self.app.prepare(ctx_id=0)

        # DB
        self.conn = sqlite3.connect("faces.db")
        self.known_embeddings, self.known_names = self.load_database()

        # Webcam selection
        self.cap = None
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)

        # Show camera selection dialog
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
        self.status_label.setText("Buscando rostro...")
        self.timer.start(30)

    # LOAD DATABASE
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

    # SIMILARITY
    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    # FIND BEST MATCH
    def find_match(self, embedding):
        best_sim = -1
        best_name = "Unknown"

        for db_emb, name in zip(self.known_embeddings, self.known_names):
            sim = self.cosine_similarity(embedding, db_emb)

            if sim > best_sim:
                best_sim = sim
                best_name = name

        return best_name, best_sim

    # UPDATE FRAME
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        faces = self.app.get(frame)

        recognized_any = False

        for face in faces:
            name, sim = self.find_match(face.embedding)

            box = face.bbox.astype(int)

            # Threshold (ajústalo)
            if sim > 0.5:
                recognized_any = True
                color = (0, 255, 0)
                label = f"{name} ({sim:.2f})"
            else:
                color = (0, 0, 255)
                label = f"Unknown ({sim:.2f})"

            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2)
            cv2.putText(frame, label, (box[0], box[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        if recognized_any:
            self.status_label.setText("Reconocido")
        else:
            self.status_label.setText("No reconocido")

        # Convert to Qt
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QtGui.QImage(rgb.data, w, h, ch * w, QtGui.QImage.Format_RGB888)
        self.image_label.setPixmap(QtGui.QPixmap.fromImage(qt_img))

    # CLEANUP
    def closeEvent(self, event):
        if self.cap:
            self.cap.release()
        self.timer.stop()
        self.conn.close()
        event.accept()
from PySide6 import QtWidgets, QtCore, QtGui
from ui.top_bar import TopBar
from log import log

import cv2
import sqlite3
import numpy as np
from insightface.app import FaceAnalysis


class PersonRegisterView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Registro de Personas")
        log.push("Vista registro", "Abierto")

        layout = QtWidgets.QVBoxLayout(self)

        # TOP BAR
        self.top_bar = TopBar("Registrar Persona")
        layout.addWidget(self.top_bar)

        # Nombre input
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Nombre de la persona")
        layout.addWidget(self.name_input)

        # Webcam
        self.image_label = QtWidgets.QLabel()
        self.image_label.setFixedHeight(400)
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.image_label)

        # Botones
        btn_layout = QtWidgets.QHBoxLayout()

        self.capture_btn = QtWidgets.QPushButton("Capturar rostro")
        self.capture_btn.clicked.connect(self.capture_face)
        btn_layout.addWidget(self.capture_btn)

        self.save_btn = QtWidgets.QPushButton("Guardar en base de datos")
        self.save_btn.clicked.connect(self.save_person)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

        # Estado
        self.status = QtWidgets.QLabel("Listo")
        self.status.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.status)

        # InsightFace
        self.app = FaceAnalysis()
        self.app.prepare(ctx_id=0)

        # Webcam
        self.cap = cv2.VideoCapture(1)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # DB
        self.conn = sqlite3.connect("faces.db")
        self.create_tables()

        # buffer de embeddings capturados
        self.current_embeddings = []

    # DATABASE
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

    # WEBCAM
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        self.current_frame = frame.copy()

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QtGui.QImage(rgb.data, w, h, ch * w, QtGui.QImage.Format_RGB888)
        self.image_label.setPixmap(QtGui.QPixmap.fromImage(qt_img))

    # CAPTURE FACE
    def capture_face(self):
        faces = self.app.get(self.current_frame)

        if len(faces) == 0:
            self.status.setText("No se detectó rostro")
            return

        emb = faces[0].embedding
        self.current_embeddings.append(emb)

        self.status.setText(f"📸 Capturas: {len(self.current_embeddings)}")

    # SAVE TO DB
    def save_person(self):
        name = self.name_input.text().strip()

        if not name:
            self.status.setText("Ingresa un nombre")
            return

        if len(self.current_embeddings) == 0:
            self.status.setText("Captura al menos un rostro")
            return

        cursor = self.conn.cursor()

        # Insert person
        cursor.execute("INSERT INTO persons (name) VALUES (?)", (name,))
        person_id = cursor.lastrowid

        # Insert embeddings
        for emb in self.current_embeddings:
            blob = emb.tobytes()
            cursor.execute(
                "INSERT INTO encodings (person_id, embedding) VALUES (?, ?)",
                (person_id, blob)
            )

        self.conn.commit()

        log.push("Persona registrada", name)

        # Reset
        self.current_embeddings = []
        self.name_input.clear()

        self.status.setText("Guardado correctamente")

    # CLEANUP
    def closeEvent(self, event):
        self.cap.release()
        self.timer.stop()
        self.conn.close()
        event.accept()
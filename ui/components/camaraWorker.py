from PySide6.QtCore import QObject, QThread, Signal
import cv2
import face_recognition

class CameraWorker(QObject):
    frame_ready = Signal(object)  # Enviamos frame a GUI
    finished = Signal()

    def __init__(self, cap):
        super().__init__()
        self.cap = cap
        self.running = True

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.frame_ready.emit(frame)
        self.finished.emit()

class FaceRecognitionWorker(QObject):
    frame_processed = Signal(object)  # Frame con rectángulos dibujados
    finished = Signal()

    def __init__(self, encodings_db, nombres_db):
        super().__init__()
        self.encodings_db = encodings_db
        self.nombres_db = nombres_db
        self.running = True

    def process_frame(self, frame):
        # Procesamiento costoso aquí
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
            resultados = face_recognition.compare_faces(self.encodings_db, encoding)
            nombre = "Desconocido"
            if True in resultados:
                index = resultados.index(True)
                nombre = self.nombres_db[index]

            cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)
            cv2.putText(frame, nombre, (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0),2)

        self.frame_processed.emit(frame)

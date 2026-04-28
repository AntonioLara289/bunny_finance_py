from PySide6.QtCore import QObject, Signal, QThread
import cv2
import numpy as np
from insightface.app import FaceAnalysis


class FaceRecognitionWorkerInsight(QObject):
    """Worker para reconocimiento facial usando InsightFace buffalo_l"""
    frame_processed = Signal(np.ndarray)
    finished = Signal()
    persona_identificada = Signal(str, int, float)
    persona_nueva = Signal()

    def __init__(self, encodings_db=None, nombres_db=None, ids_db=None, parent=None):
        super().__init__(parent)

        self.frame_counter = 0
        self.skip_frames = 2
        self.skip_recalculo = 15
        self._running = True

        self.known_encodings = encodings_db if encodings_db is not None else []
        self.known_names = nombres_db if nombres_db is not None else []
        self.known_ids = ids_db if ids_db is not None else []

        self.umbral_similitud = 0.5

        self.confirmaciones = {}
        self.confirmaciones_necesarias = 2

        self.last_locations = []
        self.last_labels = []
        self.last_colors = []

        self.app = None
        self._app_initialized = False

    def _init_app(self):
        if not self._app_initialized:
            try:
                self.app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
                self.app.prepare(ctx_id=0, det_size=(640, 640))
                self._app_initialized = True
                print("InsightFace (buffalo_l) inicializado correctamente")
            except Exception as e:
                print(f"Error inicializando InsightFace: {e}")
                self.app = None

    def cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def find_best_match(self, embedding):
        best_sim = -1
        best_name = "Desconocido"
        best_id = None

        for i, db_emb in enumerate(self.known_encodings):
            if db_emb is None:
                continue
            sim = self.cosine_similarity(embedding, db_emb)
            if sim > best_sim:
                best_sim = sim
                best_name = self.known_names[i]
                best_id = self.known_ids[i]

        return best_name, best_id, best_sim

    def process_frame(self, frame):
        if frame is None or not self._running:
            return

        if not self._app_initialized:
            self._init_app()

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

        frame_para_recalculo = self.frame_counter % self.skip_recalculo == 0
        frame_para_deteccion = self.frame_counter % self.skip_frames == 0

        if frame_para_deteccion and self.app is not None:
            try:
                faces = self.app.get(rgb_frame)

                if len(faces) > 0:
                    if frame_para_recalculo:
                        self.last_locations = []
                        self.last_labels = []
                        self.last_colors = []

                        for face in faces:
                            embedding = face.embedding
                            nombre, persona_id, similitud = self.find_best_match(embedding)

                            if similitud > self.umbral_similitud:
                                if persona_id not in self.confirmaciones:
                                    self.confirmaciones[persona_id] = {"count": 0, "nombre": nombre}

                                self.confirmaciones[persona_id]["count"] += 1

                                if self.confirmaciones[persona_id]["count"] >= self.confirmaciones_necesarias:
                                    self.persona_identificada.emit(nombre, persona_id, similitud * 100)

                                label = f"ID: {persona_id} ({similitud * 100:.0f}%)"
                                color = (0, 255, 0)
                            else:
                                label = "Nuevo"
                                color = (0, 165, 255)
                                self.confirmaciones.clear()
                                if self.frame_counter % (self.skip_recalculo * 2) == 0:
                                    self.persona_nueva.emit()

                            box = face.bbox.astype(int)
                            self.last_locations.append(box)
                            self.last_labels.append(label)
                            self.last_colors.append(color)
                    else:
                        for face in faces:
                            box = face.bbox.astype(int)
                            self.last_locations.append(box)

                    for box, label, color in zip(self.last_locations, self.last_labels, self.last_colors):
                        cv2.rectangle(output_frame, (box[0], box[1]), (box[2], box[3]), color, 2)
                        cv2.putText(output_frame, label, (box[0], box[1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                else:
                    self.confirmaciones.clear()
                    self.last_locations = []
                    self.last_labels = []
                    self.last_colors = []

            except Exception as e:
                print(f"Error en process_frame: {e}")

        elif self.last_locations:
            for box, label, color in zip(self.last_locations, self.last_labels, self.last_colors):
                cv2.rectangle(output_frame, (box[0], box[1]), (box[2], box[3]), color, 2)
                cv2.putText(output_frame, label, (box[0], box[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        self.frame_counter += 1
        self.frame_processed.emit(output_frame)

    def stop(self):
        self._running = False
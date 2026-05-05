from PySide6.QtCore import QObject, Signal
import cv2
import numpy as np
from insightface.app import FaceAnalysis

class FaceRecognitionInsightFaceWorker(QObject):
    # Señales solicitadas
    frame_processed = Signal(np.ndarray)
    finished = Signal()
    persona_identificada = Signal(str, int, float) # Nombre, ID, Similitud
    persona_nueva = Signal()

    def __init__(self, encodings_db, nombres_db, ids_db, parent=None):
        super().__init__(parent)
        # Importante: known_encodings deben ser de 512 dimensiones (InsightFace)
        self.known_encodings = np.array(encodings_db) if len(encodings_db) > 0 else np.array([])
        self.known_names = nombres_db
        self.known_ids = ids_db
        
        self._running = True
        self.frame_counter = 0
        self.skip_frames = 2  # Procesa 1 de cada 2 frames para fluidez

        # Inicialización de InsightFace
        # Si tienes GPU Nvidia, cambia a ['CUDAExecutionProvider']
        self.app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))

        # Control de señales para evitar spam en la UI
        self.last_emitted_id = None
        self.frames_since_new_person_emit = 0
        self.umbral_similitud = 0.45 # Ajustable (0.0 a 1.0)

    def process_frame(self, frame):
        """Punto de entrada: self.cam_worker.frame_ready.connect(self.face_worker.process_frame)"""
        if frame is None or not self._running:
            return

        # 1. Pre-procesamiento de iluminación (Cita: Mejora técnica sugerida)
        frame_ready = self.aplicar_clahe(frame)
        output_frame = frame.copy()

        if self.frame_counter % self.skip_frames == 0:
            # 2. Detección y Reconocimiento en un solo paso
            faces = self.app.get(frame_ready)
            
            if not faces:
                self.last_emitted_id = None
            else:
                for face in faces:
                    nombre, similitud, persona_id = self.identificar_persona(face.normed_embedding)
                    
                    # Dibujado básico
                    box = face.bbox.astype(int)
                    color = (0, 255, 0) if persona_id else (0, 165, 255)
                    cv2.rectangle(output_frame, (box[0], box[1]), (box[2], box[3]), color, 2)

                    # 3. Lógica de Emisión de Señales
                    if persona_id is not None:
                        # Solo emitimos si es una nueva detección o cambió la persona
                        if persona_id != self.last_emitted_id:
                            self.persona_identificada.emit(nombre, persona_id, similitud)
                            self.last_emitted_id = persona_id
                    else:
                        # Lógica para "Persona Nueva"
                        self.last_emitted_id = None
                        if self.frames_since_new_person_emit > 30: # 1 vez por segundo aprox
                            self.persona_nueva.emit()
                            self.frames_since_new_person_emit = 0
                
            self.frames_since_new_person_emit += 1

        # 4. Finalizar frame y enviar a UI
        self.frame_counter += 1
        self.frame_processed.emit(output_frame)

    def identificar_persona(self, embedding_actual):
        """Calcula la similitud de coseno contra la base de datos"""
        if self.known_encodings.size == 0:
            return "Desconocido", 0.0, None

        # Producto punto para similitud de coseno (vectores ya normalizados)
        similitudes = np.dot(self.known_encodings, embedding_actual)
        idx_mejor = np.argmax(similitudes)
        mejor_sim = similitudes[idx_mejor]

        if mejor_sim > self.umbral_similitud:
            return self.known_names[idx_mejor], mejor_sim * 100, self.known_ids[idx_mejor]
        
        return "Desconocido", mejor_sim * 100, None

    def aplicar_clahe(self, bgr_frame):
        """Mejora el contraste para ambientes con poca luz"""
        lab = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    def stop(self):
        self._running = False

    def getEncoding(self, frame):
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        face = self.app.get(rgb)

        if not face:
            return None
        else:
            return face
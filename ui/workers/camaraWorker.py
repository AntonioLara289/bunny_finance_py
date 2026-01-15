from PySide6.QtCore import QObject, Signal, QRunnable, QThread
import cv2
import time
import numpy as np

class CameraWorker(QObject):
    # Señal para emitir el frame de video leído (un array de numpy)
    frame_ready = Signal(np.ndarray)
    finished = Signal()
    
    def __init__(self, cap: cv2.VideoCapture, parent=None):
        super().__init__(parent)
        self.cap = cap
        self._running = True

    def run(self):
        """El bucle principal de lectura de la cámara."""
        while self._running and self.cap.isOpened():
            ret, frame = self.cap.read()
            
            if ret:
                # Emitir el frame al hilo principal o a otro worker
                self.frame_ready.emit(frame)
            
            # Control de velocidad (opcional, pero ayuda a no sobrecargar la CPU)
            # time.sleep(0.005) # ~200 FPS, ajusta según necesidad
            
        self.finished.emit()

    def stop(self):
        """Detiene el bucle de ejecución."""
        self._running = False

# ... (FaceRecognitionWorker se define en el siguiente paso)

# Continúa en ui/components/camaraWorker.py
import face_recognition
import mediapipe as mp
# ... otras importaciones necesarias: numpy, cv2

# --- Dentro de ui/components/camaraWorker.py (o donde definiste FaceRecognitionWorker) ---

class FaceRecognitionWorker(QObject):
    
    # Señal para emitir el frame ya dibujado (para el cam_live en la UI)
    frame_processed = Signal(np.ndarray)
    finished = Signal()

    def __init__(self, encodings_db, nombres_db, ids_db, parent=None):
        # ... (Tu código de inicialización de modelos y datos de DB) ...
        
        super().__init__(parent)
        
        # Datos de la base de datos para la identificación
        self.known_encodings = encodings_db
        self.known_names = nombres_db
        self.known_ids = ids_db
        
        # Inicialización única de modelos (¡Más eficiente!)
        # NUEVAS VARIABLES PARA OPTIMIZACIÓN
        self.frame_counter = 0
        self.skip_frames = 5  # <--- AJUSTA ESTE VALOR (e.g., 3, 5, 10)
        
        # Almacenar el último resultado conocido para dibujar rápidamente
        self.last_face_locations = []
        self.last_face_names = []
        self.last_face_colors = []

        # MediaPipe Face Detection para obtener el Bounding Box (rápido)
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(min_detection_confidence=0.5)
    def process_frame(self, frame):
        if frame is None:
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 1. Ejecutar la lógica pesada solo cada 'skip_frames'
        if self.frame_counter % self.skip_frames == 0:
            
            # --- ZONA DE PROCESAMIENTO LENTO ---
            
            # Detección y Encoding
            face_locations = face_recognition.face_locations(rgb_frame, model="hog")
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            # Almacenar resultados de la identificación
            current_face_names = []
            current_face_colors = []
            
            for loc, encoding in zip(face_locations, face_encodings):
                # ... (Lógica de face_recognition.compare_faces, determinar nombre y color) ...
                
                # Ejemplo de la lógica que ya tenías:
                resultados = face_recognition.compare_faces(self.known_encodings, encoding)
                nombre = "Desconocido"
                color = (255, 0, 0)
                
                if True in resultados:
                    index = resultados.index(True)
                    nombre = self.known_names[index] + ", ID: " + str(self.known_ids[index])
                    color = (0, 255, 0)
                    
                current_face_names.append(nombre)
                current_face_colors.append(color)

            # 2. Actualizar las variables de dibujo rápido
            self.last_face_locations = face_locations
            self.last_face_names = current_face_names
            self.last_face_colors = current_face_colors
            
            # --- FIN ZONA DE PROCESAMIENTO LENTO ---
        
        
        # 3. Dibujar en CADA frame usando los últimos datos conocidos (¡Zona Rápida!)
        for loc, name, color in zip(self.last_face_locations, self.last_face_names, self.last_face_colors):
            top, right, bottom, left = loc
            
            # Dibujar rectángulo + nombre en el frame RGB
            cv2.rectangle(rgb_frame, (left, top), (right, bottom), color, 2)
            cv2.putText(rgb_frame, name, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2, cv2.LINE_AA)
        
        self.frame_counter += 1
        self.frame_processed.emit(rgb_frame)


    def porcentajeSimilitud(self, encoding):
        # 1. Obtener la distancia (es un array de distancias)
        distancias = face_recognition.face_distance(self.known_encodings, encoding)

        # 2. Si quieres el porcentaje de la cara que más se parece:
        mejor_distancia = min(distancias)
        porcentaje_similitud = (1 - mejor_distancia) * 100

        return float(porcentaje_similitud, 2)
        # print(f"Similitud: {porcentaje_similitud:.2f}%")

        
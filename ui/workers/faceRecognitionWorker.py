# Continúa en ui/components/camaraWorker.py
from PySide6.QtCore import QObject, Signal, QRunnable, QThread
import cv2
import time
import numpy as np
import face_recognition
import mediapipe as mp

class FaceRecognitionWorker(QObject):
    frame_processed = Signal(np.ndarray)
    finished = Signal()

    def __init__(self, encodings_db, nombres_db, ids_db, parent=None):
        super().__init__(parent)
        self.known_encodings = encodings_db
        self.known_names = nombres_db
        self.known_ids = ids_db
        
        self.frame_counter = 0
        self.skip_frames = 5  
        
        self.last_face_locations = []
        self.last_face_names = []
        self.last_face_colors = []
        self._running = True # Bandera para detener el worker

    def process_frame(self, frame):
        if frame is None or not self._running:
            return

        # Redimensionar para procesar más rápido (opcional pero recomendado)
        # small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if self.frame_counter % self.skip_frames == 0:
            # Detección de rostros
            face_locations = face_recognition.face_locations(rgb_frame, model="hog")
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            current_face_names = []
            current_face_colors = []
            
            for encoding in face_encodings:
                nombre, porcentaje = self.identificar_persona(encoding)
                print('porcentaje parentezco: ', porcentaje)
                
                # Definir color basado en si es conocido o no
                if nombre != "Desconocido":
                    color = (0, 255, 0) # Verde
                    label = f"{nombre} ({porcentaje:.1f}%)"
                else:
                    color = (255, 0, 0) # Rojo
                    label = "Desconocido"
                    
                current_face_names.append(label)
                current_face_colors.append(color)

            self.last_face_locations = face_locations
            self.last_face_names = current_face_names
            self.last_face_colors = current_face_colors
        
        # Dibujar (Zona Rápida)
        # Importante: convertimos de vuelta a BGR para que la UI de OpenCV/Qt lo vea bien
        output_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
        
        for loc, name, color in zip(self.last_face_locations, self.last_face_names, self.last_face_colors):
            top, right, bottom, left = loc
            cv2.rectangle(output_frame, (left, top), (right, bottom), color, 2)
            cv2.putText(output_frame, name, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        self.frame_counter += 1
        self.frame_processed.emit(output_frame)

    def identificar_persona(self, encoding):
        """Busca la mejor coincidencia y devuelve (nombre, porcentaje)"""
        if not self.known_encodings:
            return "Desconocido", 0.0

        distancias = face_recognition.face_distance(self.known_encodings, encoding)
        indice_mejor = np.argmin(distancias)
        distancia_minima = distancias[indice_mejor]
        
        # Convertir a porcentaje
        porcentaje = (1 - distancia_minima) * 100
        
        # Umbral de confianza (0.6 es el estándar, puedes bajarlo a 0.5 para ser más estricto)
        if distancia_minima < 0.6:
            nombre = f"{self.known_names[indice_mejor]} (ID: {self.known_ids[indice_mejor]})"
            return nombre, porcentaje
        
        return "Desconocido", porcentaje

    def stop(self):
        self._running = False
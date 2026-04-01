# Continúa en ui/components/camaraWorker.py
from PySide6.QtCore import QObject, Signal, QRunnable, QThread
import cv2
import time
import numpy as np
import face_recognition
import mediapipe as mp
import os

class FaceRecognitionWorker(QObject):
    frame_processed = Signal(np.ndarray)
    finished = Signal()
    persona_confirmada = Signal(str, int, float)

    def __init__(self, encodings_db, nombres_db, ids_db, parent=None):
        super().__init__(parent)
        self.known_encodings = np.array(encodings_db)
        self.known_names = nombres_db
        self.known_ids = ids_db
        
        self.frame_counter = 0
        self.skip_frames = 3
        
        self.last_face_locations = []
        self.last_face_names = []
        self.last_face_colors = []
        self._running = True

        self.confirmaciones = {}
        self.confirmaciones_necesarias = 2
        self.frame_sin_deteccion = 0
        self.max_frames_sin_deteccion = 10
        self.frame_para_confirmacion = None

    def process_frame(self, frame):
        if frame is None or not self._running:
            return

        rgb_frame_clah = self.aplicar_clahe(frame)
        rgb_frame = cv2.cvtColor(rgb_frame_clah, cv2.COLOR_BGR2RGB)

        if self.frame_counter % self.skip_frames == 0:
            face_locations = face_recognition.face_locations(rgb_frame, model="hog")
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations, num_jitters=1, model="large")
            
            current_face_names = []
            current_face_colors = []

            if len(face_locations) > 0:
                self.frame_sin_deteccion = 0
                
                for i, encoding in enumerate(face_encodings):
                    nombre, porcentaje, persona_id = self.identificar_persona_rapida(encoding)
                    loc = face_locations[i]
                    
                    if persona_id is not None:
                        if persona_id not in self.confirmaciones:
                            self.confirmaciones[persona_id] = {"count": 0, "similarities": []}
                        
                        self.confirmaciones[persona_id]["count"] += 1
                        self.confirmaciones[persona_id]["similarities"].append(porcentaje)
                        
                        if self.confirmaciones[persona_id]["count"] >= self.confirmaciones_necesarias:
                            if self.confirmaciones[persona_id]["count"] == self.confirmaciones_necesarias:
                                similitud_confirmada = self.confirmar_con_encoding_pesado(rgb_frame, loc, persona_id)
                                if similitud_confirmada is not None:
                                    print(f"PERSONA CONFIRMADA: {nombre} - {similitud_confirmada:.1f}%")
                                    self.persona_confirmada.emit(nombre, persona_id, similitud_confirmada)
                                self.confirmaciones[persona_id]["count"] += 1
                        
                        color = (0, 255, 0)
                        label = f"{nombre} ({porcentaje:.1f}%)"
                    else:
                        color = (255, 0, 0)
                        label = "Desconocido"
                        if persona_id in self.confirmaciones:
                            del self.confirmaciones[persona_id]
                    
                    current_face_names.append(label)
                    current_face_colors.append(color)

                self.last_face_locations = face_locations
            else:
                self.frame_sin_deteccion += 1
                if self.frame_sin_deteccion >= self.max_frames_sin_deteccion:
                    self.confirmaciones.clear()
        
        output_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
        
        for loc, name, color in zip(self.last_face_locations, self.last_face_names, self.last_face_colors):
            top, right, bottom, left = loc
            cv2.rectangle(output_frame, (left, top), (right, bottom), color, 2)
            cv2.putText(output_frame, name, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        self.frame_counter += 1
        self.frame_processed.emit(output_frame)

    def confirmar_con_encoding_pesado(self, rgb_frame, face_location, persona_id):
        encoding_pesado = face_recognition.face_encodings(
            rgb_frame, 
            [face_location], 
            num_jitters=100, 
            model="large"
        )
        
        if encoding_pesado:
            idx = self.known_ids.index(persona_id)
            distancia = face_recognition.face_distance([self.known_encodings[idx]], encoding_pesado[0])[0]
            similitud = (1 - distancia) * 100
            return similitud
        return None

    def identificar_persona_rapida(self, encoding_actual):
        if self.known_encodings is None or len(self.known_encodings) == 0:
            return "Desconocido", 0.0, None

        distancias = face_recognition.face_distance(self.known_encodings, encoding_actual)
        
        if len(distancias) == 0:
            return "Desconocido", 0.0, None
            
        indice_mejor = np.argmin(distancias)
        distancia_minima = distancias[indice_mejor]
        porcentaje = (1 - distancia_minima) * 100
        
        if distancia_minima < 0.4:
            nombre = self.known_names[indice_mejor]
            persona_id = self.known_ids[indice_mejor]
            return nombre, porcentaje, persona_id
        
        return "Desconocido", porcentaje, None

    def aplicar_clahe(self, bgr_frame):
        lab = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    def identificar_persona(self, encoding_actual):
        # 1. Validación de seguridad: ¿Hay encodings cargados?
        if self.known_encodings is None or len(self.known_encodings) == 0:
            return "Desconocido", 0.0

        # 2. Asegurarse de que known_encodings sea un array de NumPy
        # Esto es vital para que face_distance devuelva una lista de distancias
        distancias = face_recognition.face_distance(self.known_encodings, encoding_actual)

        # 3. Verificar si distancias es una lista/array (iterable)
        if isinstance(distancias, np.ndarray) or isinstance(distancias, list):
            if len(distancias) == 0:
                return "Desconocido", 0.0
                
            indice_mejor = np.argmin(distancias)
            # Acceso seguro al índice
            distancia_minima = distancias[indice_mejor]
        else:
            # Si por alguna razón devolvió un solo número
            distancia_minima = distancias

        # 4. Cálculo de porcentaje
        porcentaje = (1 - distancia_minima) * 100
        
        if distancia_minima < 0.4:
            nombre = self.known_names[indice_mejor]
            persona_id = self.known_ids[indice_mejor]
            return f"{nombre} (ID: {persona_id})", porcentaje
        
        return "Desconocido", porcentaje

    def generarEnconding(self, frame):
        if frame is None:
            return (f"la foto no tiene datos")

        # Convertir a RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detectar rostro
        locations = face_recognition.face_locations(rgb)

        if len(locations) == 0:
            return(f"No se detectó rostro en la foto") 

        # Obtener encoding
        return face_recognition.face_encodings(rgb, locations)[0]
        

    def stop(self):
        self._running = False

    def obtenerAnguloGiro(self, face_landmarks_list):
        
        if not face_landmarks_list:
            return
    
        # Ahora enviamos estos puntos a tu función
        print(f'Giro: ', self.obtener_posicion_asistida(face_landmarks_list[0]))
    
    # def obtener_angulo_giro_mejorado(self, ojo_izq, ojo_der, nariz):
    #     # ojo_izq es una tupla (x, y)
    #     # nariz es una tupla (x, y)
        
    #     # Distancia horizontal (X) desde la nariz a cada ojo
    #     dist_izq = abs(nariz[0] - ojo_izq[0])
    #     dist_der = abs(nariz[0] - ojo_der[0])
        
    #     # Evitar división por cero
    #     if dist_der == 0: dist_der = 1
        
    #     ratio = dist_izq / dist_der
        
    #     # --- Lógica de Asistencia ---
    #     if 0.85 < ratio < 1.15:
    #         return "FRENTE", ratio
    #     elif ratio <= 0.85:
    #         return "IZQUIERDA", ratio
    #     else:
    #         return "DERECHA", ratio

    def obtener_posicion_asistida(self, landmarks):

        # Puntos de los extremos de la cara (Mandíbula/Orejas)
        extremo_izq = landmarks['chin'][0]   # Punto 0
        extremo_der = landmarks['chin'][-1]  # Punto 16
        punta_nariz = landmarks['nose_bridge'][-1] # Punta de la nariz

        # 1. Calculamos el ancho total de la cara detectada
        ancho_total = abs(extremo_der[0] - extremo_izq[0])
        
        # 2. Calculamos dónde está la nariz respecto al borde izquierdo
        distancia_a_la_izquierda = abs(punta_nariz[0] - extremo_izq[0])
        
        # 3. Calculamos el porcentaje de "Centrado"
        # 0.5 significa que la nariz está exactamente a la mitad (50%)
        porcentaje_centro = distancia_a_la_izquierda / ancho_total

        # --- LÓGICA DE ESTADOS ---
        # Frente: La nariz debe estar entre el 45% y 55% del ancho de la cara
        if 0.45 <= porcentaje_centro <= 0.55:
            # self.emitir_beep_rapido()
            return "FRENTE", porcentaje_centro
        
        # Izquierda: La nariz se acerca al borde derecho (porcentaje alto > 0.65)
        elif porcentaje_centro > 0.65:
            # self.emitir_beep_rapido()
            return "IZQUIERDA", porcentaje_centro
        
        # Derecha: La nariz se acerca al borde izquierdo (porcentaje bajo < 0.35)
        elif porcentaje_centro < 0.35:
            # self.emitir_beep_rapido()
            return "DERECHA", porcentaje_centro

        return "MOVIÉNDOSE", porcentaje_centro
        
    
    # def emitir_beep(self):
    #     # Reproduce un sonido de sistema estándar de Ubuntu
    #     os.system('canberra-gtk-play --id="message-new-instant"')
    def emitir_beep_rapido(self):
        # El símbolo '&' es la clave para que NO se trabe
        os.system('canberra-gtk-play --id="message-new-instant" &')


class FaceRecognitionWorkerRegistro(QObject):
    """Worker para modo registro con HOG rápido y confirmaciones + encoding pesado"""
    frame_processed = Signal(np.ndarray)
    finished = Signal()
    persona_identificada = Signal(str, int, float)
    persona_nueva = Signal()

    def __init__(self, encodings_db=None, nombres_db=None, ids_db=None, parent=None):
        super().__init__(parent)
        self.frame_counter = 0
        self.skip_deteccion = 5
        self.skip_recalculo = 30
        self._running = True

        self.known_encodings = np.array(encodings_db) if encodings_db is not None and len(encodings_db) > 0 else np.array([])
        self.known_names = nombres_db or []
        self.known_ids = ids_db or []
        self.umbral_hog = 0.35

        self.confirmaciones = {}
        self.confirmaciones_necesarias = 2
        self.encoding_pesado_usado = {}

        self.last_locations = []
        self.last_labels = []
        self.last_colors = []

    def process_frame(self, frame):
        if frame is None or not self._running:
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

        frame_para_recalculo = self.frame_counter % self.skip_recalculo == 0
        frame_para_deteccion = self.frame_counter % self.skip_deteccion == 0

        if frame_para_deteccion:
            face_locations = face_recognition.face_locations(rgb_frame, model="hog")

            if len(face_locations) > 0:
                if frame_para_recalculo:
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations, num_jitters=1, model="small")
                    self.last_locations = []
                    self.last_labels = []
                    self.last_colors = []

                    for loc, encoding in zip(face_locations, face_encodings):
                        distancia, nombre, persona_id = self.obtener_mejor_match(encoding)
                        top, right, bottom, left = loc

                        if distancia is not None and distancia < self.umbral_hog:
                            similitud = (1 - distancia) * 100

                            if persona_id not in self.confirmaciones:
                                self.confirmaciones[persona_id] = {"count": 0, "nombre": nombre}

                            self.confirmaciones[persona_id]["count"] += 1

                            if self.confirmaciones[persona_id]["count"] >= self.confirmaciones_necesarias:
                                if persona_id not in self.encoding_pesado_usado:
                                    similitud_final = self.encoding_pesado_confirmacion(rgb_frame, loc, persona_id)
                                    if similitud_final is not None:
                                        self.persona_identificada.emit(nombre, persona_id, similitud_final)
                                        self.encoding_pesado_usado[persona_id] = True
                                else:
                                    self.persona_identificada.emit(nombre, persona_id, similitud)

                            label = f"ID: {persona_id} ({similitud:.0f}%)"
                            color = (0, 255, 0)
                        else:
                            label = "Nuevo"
                            color = (0, 165, 255)
                            if persona_id in self.confirmaciones:
                                del self.confirmaciones[persona_id]
                            if self.frame_counter % (self.skip_recalculo * 2) == 0:
                                self.persona_nueva.emit()

                        self.last_locations.append(loc)
                        self.last_labels.append(label)
                        self.last_colors.append(color)
                else:
                    self.last_locations = face_locations

                for loc, label, color in zip(self.last_locations, self.last_labels, self.last_colors):
                    top, right, bottom, left = loc
                    cv2.rectangle(output_frame, (left, top), (right, bottom), color, 2)
                    cv2.putText(output_frame, label, (left, top - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            else:
                self.confirmaciones.clear()
                self.last_locations = []
                self.last_labels = []
                self.last_colors = []

        elif self.last_locations:
            for loc, label, color in zip(self.last_locations, self.last_labels, self.last_colors):
                top, right, bottom, left = loc
                cv2.rectangle(output_frame, (left, top), (right, bottom), color, 2)
                cv2.putText(output_frame, label, (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        self.frame_counter += 1
        self.frame_processed.emit(output_frame)

    def obtener_mejor_match(self, encoding_actual):
        if len(self.known_encodings) == 0:
            return None, None, None

        distancias = face_recognition.face_distance(self.known_encodings, encoding_actual)
        
        if len(distancias) == 0:
            return None, None, None

        indice_mejor = np.argmin(distancias)
        distancia_minima = distancias[indice_mejor]
        
        return distancia_minima, self.known_names[indice_mejor], self.known_ids[indice_mejor]

    def encoding_pesado_confirmacion(self, rgb_frame, face_location, persona_id):
        encoding_pesado = face_recognition.face_encodings(
            rgb_frame,
            [face_location],
            num_jitters=50,
            model="large"
        )

        if encoding_pesado:
            idx = self.known_ids.index(persona_id)
            distancia = face_recognition.face_distance([self.known_encodings[idx]], encoding_pesado[0])[0]
            similitud = (1 - distancia) * 100
            print(f"Encoding pesado confirmado: {self.known_names[idx]} - {similitud:.1f}%")
            return similitud
        return None

    def stop(self):
        self._running = False
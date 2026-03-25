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

    def __init__(self, encodings_db, nombres_db, ids_db, parent=None):
        super().__init__(parent)
        self.known_encodings = np.array(encodings_db)
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

        # frame_equilibrado = self.aplicar_clahe(frame)

        # small_frame = cv2.resize(frame_equilibrado, (0, 0), fx=0.5, fy=0.5)
        # rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        #     # --- MEJORA DE LUZ ---
        # # Convertimos a espacio de color LAB para ajustar solo el brillo (L)
        # lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        # l, a, b = cv2.split(lab)
        
        # # Aplicamos CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        # cl = clahe.apply(l)
        
        # # Fusionamos y volvemos a BGR
        # limg = cv2.merge((cl,a,b))
        # frame_mejorado = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        # # ---------------------

        # rgb_frame = cv2.cvtColor(frame_mejorado, cv2.COLOR_BGR2RGB)
        # ... resto de tu lógica de detección

        # Redimensionar para procesar más rápido (opcional pero recomendado)
        # small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame_clah = self.aplicar_clahe(frame)
        rgb_frame = cv2.cvtColor(rgb_frame_clah, cv2.COLOR_BGR2RGB)

        if self.frame_counter % self.skip_frames == 0:
            # Detección de rostros
            # Dentro de process_frame, después de convertir a RGB:
            # Reducir a un tamaño estándar (ej. 1/2 del original)
            # pequeno = cv2.resize(rgb_frame, (0, 0), fx=0.5, fy=0.5)

            face_locations = face_recognition.face_locations(rgb_frame, model="cnn")
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations, num_jitters=50, model="large")
            
            # 2. Obtener los landmarks (puntos de referencia)
            # Esto devuelve una lista de diccionarios (uno por cada cara detectada)
            # face_landmarks_list = face_recognition.face_landmarks(rgb_frame, face_locations)
            self.obtenerAnguloGiro(face_recognition.face_landmarks(rgb_frame, face_locations))
            current_face_names = []
            current_face_colors = []            # Normalizar encodings conocidos para similitud coseno
            if self.known_encodings is not None and len(self.known_encodings) > 0:
                # Evita división por cero
                norms = np.linalg.norm(self.known_encodings, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                self.known_encodings_norm = self.known_encodings / norms
            else:
                self.known_encodings_norm = None
            
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

    def aplicar_clahe(self, bgr_frame):
        # 1. Convertimos a espacio de color LAB 
        # (L = Luminosidad, A y B = Colores)
        lab = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # 2. Creamos el objeto CLAHE
        # clipLimit: 2.0 es el estándar para no generar ruido artificial
        # tileGridSize: (8,8) divide la cara en una rejilla para nivelar la luz
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        
        # 3. Aplicamos solo a la capa de Luminosidad (L)
        cl = clahe.apply(l)

        # 4. Volvemos a fusionar los canales y regresar a BGR
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
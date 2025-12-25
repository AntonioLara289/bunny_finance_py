from PySide6 import QtWidgets
from PySide6.QtWidgets import (
    QPushButton,
    QLabel,
    QLineEdit,
    QScrollArea,
    QWidget,
    QDialog,
    QVBoxLayout,
    QHBoxLayout
)
from PySide6.QtGui import (
    QImage,
    QPixmap,
    QGuiApplication,
)
from PySide6.QtCore import (
    QTimer,
    Qt,
    QThread
)
import mediapipe as mp
import face_recognition
import cv2
import json
import numpy as np
import math
from ui.dialogs.nombrarFotoCapturada import NombrarFotoCapturada
from database.db_manager import DBManager
from ui.components.camaraWorker import CameraWorker, FaceRecognitionWorker


class EscanerRostro(QtWidgets.QWidget):
    
    def __init__(self):
        super().__init__()
        
        self.directorio_guardar = "src/capturas_personas/"
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(QtWidgets.QLabel("Soy la pantalla de escaner"))

        self.encoding_foto_capturada = None
        self.encodings_db = list()
        self.nombres_personas_db = list()
        self.ids_personas_db = list()
        self.ids_personas_indetificadas = list()
        self.cantidad_fotos = 0
        self.fotografias = {}

        self.dbManager = DBManager()
        self.cargarDatosPersonas()

        # Add your content (e.g., many QLabels) to content_layout
        #ESTO AGREGA SOLO 20 Items para el apartado del scroll pero fue destacado por la ventana modal
        # for i in range(20):
        #     content_layout.addWidget(QLabel(f"Item {i}"))

        # scroll_area.setWidget(content_widget)

        # self.pantalla = QGuiApplication.primaryScreen()
        self.medidas_pantalla = QGuiApplication.primaryScreen().size()

        self.boton_abrir_camara = self.botonInicializarCamara()
        self.boton_cerrar_camara = self.botonCerrarCamara()
        self.boton_guardar_foto = self.botonGuardarFoto()

        self.frame_camera = QLabel(self)
        self.frames_camera = []

         # ----- Scroll area -----
        self.scrollBarAreaFotos = QScrollArea()
        self.scrollBarAreaFotos.setWidgetResizable(True)  # importante
        self.content_widget_scroll_bar = QWidget()

        self.layout_scroll_bar = QHBoxLayout(self.content_widget_scroll_bar)
        self.layout_scroll_bar.setContentsMargins(10, 10, 10, 10)
        # self.layout_scroll_bar.setSpacing(10)

        self.scrollBarAreaFotos.setWidget(self.content_widget_scroll_bar)

        self.cam_live = QLabel(self)
        # self.label_foto_capturada = QLabel(self)
        # self.foto_de_camara = QLabel(self)
        # self.input_nombre_foto = QLineEdit()
        # self.input_nombre_foto.setPlaceholderText("Introduzca el nombre de la foto")
        # self.input_nombre_foto.textChanged.connect(lambda text: print(f"El texto cambio {text}"))
        # self.input_nombre_foto.text()

        # content_widget = QWidget()
        # content_layout = QtWidgets.QVBoxLayout(content_widget)
        # content_layout.addWidget(QLabel(self.label_foto_capturada))

        self.layout.addWidget(self.scrollBarAreaFotos)
        self.layout.addWidget(self.frame_camera)
        self.layout.addWidget(self.cam_live, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.boton_abrir_camara)
        self.layout.addWidget(self.boton_cerrar_camara)
        self.layout.addWidget(self.boton_guardar_foto)
        # self.layout.addWidget(self.input_nombre_foto)

        #La ocultamos ya que la mostrará y ocultara muchas veces
        self.boton_cerrar_camara.hide()
        self.boton_guardar_foto.hide()
        # self.input_nombre_foto.hide()

        # self.pantalla = QGuiApplication.primaryScreen()
        # self.medidas_pantalla = self.pantalla.size()

        self.timer_update = QTimer()
        self.timer_update.timeout.connect(self.update)
        self.timer_update.start(30)
        
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(min_detection_confidence=0.8)
        # self.mp_face_mesh = mp.solutions.face_mesh
        # self.face_mesh = self.mp_face_mesh.FaceMesh(
        #     static_image_mode=False,
        #     max_num_faces=1,
        #     refine_landmarks=True,   # Más preciso para ojos y boca
        #     min_detection_confidence=0.5,
        #     min_tracking_confidence=0.5
        # )

        # if not self.known_encodings:
        #     print("No se encontró rostro en la imagen conocida.")
        #     exit()

        # self.dialog = DialogExample()
        # self.dialog.show()
        #Marca error de formato en este apartado#
        

    def update(self):
        pass
        # print(f"Altura de la pantalla: {self.medidas_pantalla.width()}")
        # print(f"Ancho de la pantalla: {self.medidas_pantalla.height()}")


    def botonInicializarCamara(self):
        boton_abrir_camara = QPushButton("Abrir Cámara")
        boton_abrir_camara.setStatusTip("Abrir cámara para detectar rostro")
        
        # conectas la acción
        boton_abrir_camara.clicked.connect(self.abrirCamara)  # <-- Aquí el fix
                                                            #no utilizar el parentesis '()' ya que activa la función
        return boton_abrir_camara

    def botonGuardarFoto(self):
        boton_guardar_foto = QPushButton("Capturar fotografía")
        boton_guardar_foto.setStatusTip("Captura la foto actual en pantalla")
        
        boton_guardar_foto.clicked.connect(self.guardarFoto)
        return boton_guardar_foto
    
    def botonGuardarFotoCambiarTexto(self, cambiar):
        print('cambiar: ', cambiar)

        if cambiar == 1:    
            self.boton_guardar_foto.setText("Guardar Fotos")
        
        if cambiar == 2:
            self.boton_guardar_foto.setText("Capturar fotografía")
        
        if cambiar != 2 and cambiar != 1:
            self.boton_guardar_foto.setText("Error en la función")
    
    def botonCerrarCamara(self):
        boton_cerrar_camara = QPushButton("Cerrar Cámara")
        boton_cerrar_camara.setStatusTip("Cierra la cámara de detección")
        
        # conectas la acción
        boton_cerrar_camara.clicked.connect(self.cerrarCamara)  # <-- Aquí el fix
        return boton_cerrar_camara
    
    def cerrarCamara(self):
        self.cap.release()
        self.boton_abrir_camara.show()
        self.boton_cerrar_camara.hide()
        self.cam_live.hide()
        self.boton_guardar_foto.hide()

    def abrirCamara(self):
        self.boton_abrir_camara.hide()
        self.boton_guardar_foto.show()
        self.cam_live.show()
        # self.layout.removeWidget(self.boton_abrir_camara)
        # self.layout.addWidget(self.boton_cerrar_camara)
        self.boton_cerrar_camara.show()
        self.cargarDatosPersonas()

        # Iniciar cámara
        index = 0
        arr = []

        while index < 5:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                arr.append(index)
                
            else:
                pass

            cap.release()
            index += 1    
            

        self.cap = cv2.VideoCapture(0)
        print('Lista de camaras: ', arr)

        # Timer que lee frames cada 30 ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.leerDatosCamara)
        self.timer.start(0)
        
        # FaceRecognition
        # self.face_worker = FaceRecognitionWorker(self.encodings_db, self.nombres_db)
        # self.face_thread = QThread()
        # self.face_worker.moveToThread(self.face_thread)
        # self.face_worker.frame_processed.connect(self.update_image)  # Actualiza QLabel
        # self.face_worker.finished.connect(self.face_thread.quit)
        # self.face_thread.start()

        # self.cap = cv2.VideoCapture(0)
        # self.cam_thread = QThread()
        # self.cam_worker = CameraWorker(self.cap)
        # self.cam_worker.moveToThread(self.cam_thread)
        # self.cam_thread.started.connect(self.cam_worker.run)
        # self.cam_worker.frame_ready.connect(self.face_worker.process_frame)
        # self.cam_worker.finished.connect(self.cam_thread.quit)
        # self.cam_thread.start()





        ##Codigo deprecado, da errores y ya se adapto correctamente
        # Open the default camera
        # cam = cv2.VideoCapture(0)

        # # Get the default frame width and height
        # frame_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        # frame_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # # Define the codec and create VideoWriter object
        # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        # out = cv2.VideoWriter('output.mp4', fourcc, 20.0, (frame_width, frame_height))

        # while True:
        #     ret, frame = cam.read()

        #     self.foto_capturar = frame

        #     # # Write the frame to the output file
        #     out.write(frame)

        #     # # Display the captured frame
        #     # cv2.imshow('Camera', frame)

        #     # Press 'q' to exit the loop
        #     if cv2.waitKey(1) == ord('q'):
        #         break

        # # Release the capture and writer objects
        # cam.release()
        # # out.release()
        # cv2.destroyAllWindows()

    def leerDatosCamara(self):

        # self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 280)
        # self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 340)

        ret, frame = self.cap.read()

        self.frame_camera = frame

        if not ret:
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # results = None
        results = self.face_detection.process(rgb_frame)

        # results_mesh = self.face_mesh.process(rgb_frame)

        # landmarks = []

        # if results_mesh.multi_face_landmarks:
        #     face_landmarks = results_mesh.multi_face_landmarks[0]

        #     h, w, _ = rgb_frame.shape
        #     landmarks = [
        #         (int(lm.x * w), int(lm.y * h), lm.z)
        #         for lm in face_landmarks.landmark
        #     ]

        #     if landmarks:
        #         yaw = self.obtener_yaw(landmarks)
        #         pitch = self.obtener_pitch(landmarks)
        #         roll = self.obtener_roll(landmarks)
        #         self.evaluar_giro(yaw=yaw)
        #         print(f"Yaw: {yaw:.2f}º | Pitch: {pitch:.2f}º | Roll: {roll:.2f}º")



        if results.detections is  not None:
            h, w, _ = rgb_frame.shape

            for detection in results.detections:

                # Dibujar la detección
                # self.mp_drawing.draw_detection(rgb_frame, detection)

                # Bounding box relativa
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)

                # Asegurar límites válidos
                x = max(0, x)
                y = max(0, y)
                x2 = min(w, x + width)
                y2 = min(h, y + height)

                # Evitar recortes inválidos
                if x2 <= x or y2 <= y:
                    continue

                # Recortar rostro
                face_crop = rgb_frame[y:y2, x:x2]

                # Algunos modelos requieren al menos 1 canal, tamaño mínimo, etc.
                if face_crop.size == 0:
                    continue

                
                face_locations = face_recognition.face_locations(rgb_frame, model="hog")
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                self.face_mesh = mp.solutions.face_mesh.FaceMesh()

                # Código pendiente por comprender, esto salvo la detección multiple con identificación
                for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):

                    # resultados = []
                    resultados = face_recognition.compare_faces(self.encodings_db, encoding)

                    self.encoding_foto_capturada = encoding

                    if True in resultados:

                        index = resultados.index(True)

                        nombre = self.nombres_personas_db[index]

                        color = (0, 255, 0)

                        id = self.ids_personas_db[index]

                        nombre += ", ID: " + str(id)

                        # self.boton_guardar_foto.setEnabled(False)

                        if id in self.ids_personas_db:
                            pass
                        else:
                            self.ids_personas_indetificadas.appen(self.ids_personas_db[index])

                    else:
                        nombre = "Desconocido"
                        color = (0, 0, 255)
                        self.boton_guardar_foto.setEnabled(True)

                    # Dibujar rectángulo + nombre
                    cv2.rectangle(rgb_frame, (left, top), (right, bottom), color, 2)
                    cv2.putText(rgb_frame, nombre, (left, top - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2, cv2.LINE_AA)

                
                # Ahora usar face_recognition para obtener los encodings
                # face_locations = face_recognition.face_locations(rgb_frame)
                # face_encodings = face_recognition.face_encodings(frame, face_locations)
                # print('face_encodings: ', face_encodings)

                # self.encoding_foto_capturada = face_encodings

                # if face_encodings:

                #     for encoding in face_encodings:
                #         # print("Encoding obtenido:", encoding)
                #         resultados = face_recognition.compare_faces(self.encodings_db, encoding)
                #         # distancia = face_recognition.face_distance(self.known_encodings, encoding)
                #         # print(f'Validación de comparación de datos biometricos', resultados)

                #         if True in resultados:
                            
                #             index = resultados.index(True)
                #             nombre = self.nombres_personas_db[index]

                #             #Dibujar el nombre en la detección
                #             cv2.putText(
                #                 rgb_frame,
                #                 nombre,
                #                 (x, y - 10),  # posición (arriba del rectángulo)
                #                 cv2.FONT_HERSHEY_SIMPLEX,
                #                 0.9,  # tamaño de la fuente
                #                 (0, 255, 0),  # color (verde)
                #                 2,  # grosor
                #                 cv2.LINE_AA
                #             )

                #             print(f'La persona es {nombre}')

                #         else:
                #                                     #Dibujar el nombre en la detección
                #             cv2.putText(
                #                 rgb_frame,
                #                 "Desconocido",
                #                 (x, y - 10),
                #                 cv2.FONT_HERSHEY_SIMPLEX,
                #                 0.9,
                #                 (0, 0, 255),  # rojo
                #                 2,
                #                 cv2.LINE_AA
                #             )

                #             print(f'La persona no esta registrada')

                # else:
                #     # No se pudo obtener el encoding con face_recognition
                #     print("No se detectó algun rostro")
        else:
            
            pass

        # Convertir para mostrar en QLabel
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.cam_live.setPixmap(QPixmap.fromImage(qt_image))

        # if ret:

        #     # Aquí conviertes el frame a QImage y lo muestras en un QLabel
        #     self.foto_de_camara = frame
        #     rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        #     h, w, ch = rgb.shape
        #     qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        #     pixmap = QPixmap.fromImage(qimg)
        #     self.cam_live.setPixmap(pixmap)


    # DEPRECADO
    # def capturarFoto(self):
        
    #     if self.frame_camera is not None:
    #         rgb = cv2.cvtColor(self.frame_actual, cv2.COLOR_BGR2RGB)
    #         h, w, ch = rgb.shape
    #         qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
    #         pixmap = QPixmap.fromImage(qimg)
    #         # self.label_foto_capturada.setPixmap(pixmap)

    def guardarFoto(self):

        if self.frame_camera is not None:
            rgb = cv2.cvtColor(self.frame_camera, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            pixmap_label = QLabel()
            pixmap_label.setPixmap(pixmap)
            pixmap_label.setFixedSize(200, 200)
            pixmap_label.setScaledContents(True)
            
            if self.cantidad_fotos < 3:

                # Agregamos la imagen al layout
                self.layout_scroll_bar.addWidget(pixmap_label)
                
                boton_foto_camara = QPushButton("Borrar Foto")
                boton_foto_camara.setGeometry(50, 50, 200, 40) # x=50, y=50, width=150, height=40
                boton_foto_camara.setStatusTip("Elimina la foto de aquí")
                boton_foto_camara.clicked.connect(lambda _, idx=self.cantidad_fotos: self.borrarFoto(idx))
                self.layout_scroll_bar.addWidget(boton_foto_camara)
                
                # self.frames_camera.append(self.frame_camera)

                # self.fotografias[self.cantidad_fotos]["data"] = self.frame_camera
                self.fotografias[self.cantidad_fotos] = {
                    "label": pixmap_label,
                    "boton": boton_foto_camara,
                    "data": self.frame_camera,
                    "pixmap": pixmap
                }

                print(f"Aún no, hay {self.cantidad_fotos} fotos")
                self.cantidad_fotos += 1

            if self.cantidad_fotos < 3:
                return

            self.botonGuardarFotoCambiarTexto(cambiar=1)

            self.cap.release()
            rgb = cv2.cvtColor(self.frame_camera, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            
            self.modal = NombrarFotoCapturada(
                self, 
                #mandamos la foto que se mostrara en el modal
                data= self.fotografias[1]["pixmap"], 
                #mandamos todas las fotos en crudo
                imagenes=self.obtenerFotografias(), 
                #mandamos los encodings generados en promedio
                encodigns=self.generarEncodingPromedio()
            )
            # self.modal.show()
            self.resultado = self.modal.exec()
            
            if self.resultado == QDialog.Accepted:
                # self.fotografias = []

                for item in range(self.cantidad_fotos):
                    print('item: ', item)
                    self.borrarFoto(item)
                    
                print("Aceptada")
            elif self.resultado == QDialog.Rejected:
                print("Rechazado")
                
            self.abrirCamara()
            # self.modal.accept()

        else:
            print("Algo salio mal...")

    def borrarFoto(self, idx):
        if idx in self.fotografias:
            widgets = self.fotografias[idx]

            if widgets is None:
                print("Ocurrio un error")
                return
            # Eliminar label
            self.layout_scroll_bar.removeWidget(widgets["label"])
            widgets["label"].hide()
            widgets["label"].deleteLater()

            # Eliminar botón
            self.layout_scroll_bar.removeWidget(widgets["boton"])
            widgets["boton"].hide()
            widgets["boton"].deleteLater()

            # Eliminar del diccionario
            del self.fotografias[idx]
            self.cantidad_fotos -= 1
            self.botonGuardarFotoCambiarTexto(cambiar=2)

            print(f"Foto {idx} eliminada.")


    def cargarDatosPersonas(self):

        self.getPersonas = self.dbManager.getPersonas()

        for persona in self.getPersonas:

            # En Python, no se utiliza el nombre del atributo del array/objeto al que quieres acceder, sino que se 
            # utilizan los numeros.
            
            # Encodings
            self.encodings_db.append(json.loads(persona[3]))
            # Nombres
            self.nombres_personas_db.append(persona[1])
            # Ids
            self.ids_personas_db.append(persona[0])

            print(f"{json.loads(persona[3])}")

        print('self.encodings_db: ', type(self.encodings_db))
        print('self.getPersonas: ', self.getPersonas)

    def onDestroy(self, event):
        print("Cerrando escaneo de rostro")
        # Esto sirve para al momento de cambiar la pantalla desde el menú, debemos liberar la cámara y que no 
        # sigan los procesos que no son terminados al cambiar de pantalla y que afectan al sistema
        if self.cap.isOpened():
            self.cap.release()
        event.accept()
    # def abrirModalFotoCapturada(self):

    def obtenerEncodingsDeFotos(self):
        encodings = []

        for idx, foto in self.fotografias.items():
            frame = foto["data"]
            if frame is None:
                print(f"Foto {idx} no tiene datos")
                continue

            # Convertir a RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detectar rostro
            locations = face_recognition.face_locations(rgb)

            if len(locations) == 0:
                print(f"No se detectó rostro en la foto {idx}")
                continue

            # Obtener encoding
            encoding = face_recognition.face_encodings(rgb, locations)[0]
            encodings.append(encoding)

        return encodings

    def generarEncodingPromedio(self):
        encodings = self.obtenerEncodingsDeFotos()

        if len(encodings) == 0:
            print("No se pudieron generar encodings.")
            return None

        # Si hay 1, 2 o 3 encodings, se promedian
        encoding_promedio = np.mean(encodings, axis=0)

        # Convertir a lista para guardar en SQLite
        return encoding_promedio.tolist()


    def obtenerFotografias(self):
        
        fotos = []

        for idx, foto in self.fotografias.items():
            if foto["data"] is not None:
                fotos.append(foto["data"])

        return fotos

    def obtener_yaw(self, landmarks):
        # Ojo izquierdo (33) y derecho (263)
        lx, ly, _ = landmarks[33]
        rx, ry, _ = landmarks[263]

        # Diferencias
        dx = rx - lx
        dy = ry - ly

        # Yaw = inclinación vertical de los ojos
        yaw = math.degrees(math.atan2(dy, dx))
        return yaw


    def obtener_pitch(self, landmarks):
        # Nariz (1) y mentón (152)
        nx, ny, _ = landmarks[1]
        cx, cy, _ = landmarks[152]

        dy = cy - ny
        dx = abs(cx - nx) + 0.0001  # evita división por 0

        pitch = math.degrees(math.atan2(dy, dx))
        return pitch


    def obtener_roll(self, landmarks):
        # Ojos (33 y 263)
        lx, ly, _ = landmarks[33]
        rx, ry, _ = landmarks[263]

        roll = math.degrees(math.atan2(ry - ly, rx - lx))
        return roll

    def update_image(self, frame):
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.cam_live.setPixmap(QPixmap.fromImage(qt_image))

    def evaluar_giro(self, yaw):
        """
        Evalúa el giro de la cabeza de la persona según el yaw.
        
        Parámetros:
            yaw (float): ángulo de giro de la cabeza
            pitch (float, opcional): ángulo vertical
            roll (float, opcional): ángulo de inclinación lateral

        Retorna:
            str: mensaje indicando si la persona está en el rango ideal
        """

        # Ajustamos la referencia: 0 = perfil izquierdo, 90 = frente, 180 = perfil derecho
        yaw_rel = yaw + 90  # suponer que yaw = 0 frontal, -90 izquierda, +90 derecha

        # Normalizamos entre 0 y 180
        yaw_rel = max(0, min(180, yaw_rel))
        print('yaw_rel: ', yaw_rel)


        # Verificar si está en rango ideal (30° a 45° desde el perfil izquierdo/derecho)
        if 30 <= yaw_rel <= 45:
            print ("Giro ideal hacia la izquierda")
        elif 135 <= yaw_rel <= 150:
            print ("Giro ideal hacia la derecha")
        elif 45 < yaw_rel < 135:
            print ("Persona mirando de frente (no ideal para perfil)")
        else:
            print ("Giro fuera del rango esperado")

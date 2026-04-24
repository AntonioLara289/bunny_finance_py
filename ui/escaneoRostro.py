from PySide6 import QtWidgets
from PySide6.QtWidgets import (
    QPushButton,
    QLabel,
    QScrollArea,
    QWidget,
    QDialog,
    QHBoxLayout
)
from PySide6.QtGui import (
    QImage,
    QPixmap,
    QGuiApplication,
)
from PySide6.QtCore import (
    Qt,
    QThread
)
import mediapipe as mp
import face_recognition
import cv2
from cv2_enumerate_cameras import enumerate_cameras
import json
import numpy as np
import math
from ui.dialogs.nombrarFotoCapturada import NombrarFotoCapturada
from database.db_manager import DBManager
# from ui.components.camaraWorker import CameraWorker, FaceRecognitionWorker
from ui.workers.camaraWorker import CameraWorker
from ui.workers.faceRecognitionWorker import FaceRecognitionWorkerRegistro
from ui.dialogs.camarasDisponibles import CamarasDisponibles
from ui.dialogs.camarasDisponiblesMultiple import CamarasDisponiblesMultiple

class EscanerRostro(QtWidgets.QWidget):
    
    def __init__(self):
        super().__init__()
        
        self.directorio_guardar = "src/capturas_personas/"
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(QtWidgets.QLabel("Soy la pantalla de escaner"))

        # self.encoding_foto_capturada = None
        self.encodings_db = []
        self.nombres_personas_db = []
        self.ids_personas_db = []
        # self.ids_personas_indetificadas = list()
        self.cantidad_fotos = 0
        self.fotografias = {}

        self.dbManager = DBManager()
        # self.cargarDatosPersonas()

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
        self.label_estado_reconocimiento = QLabel("")
        self.label_estado_reconocimiento.setAlignment(Qt.AlignCenter)
        self.label_estado_reconocimiento.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
        """)
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
        self.layout.addWidget(self.label_estado_reconocimiento)
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

        # self.timer_update = QTimer()
        # self.timer_update.timeout.connect(self.update)
        # self.timer_update.start(30)
        
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
        
        # 1. Indicar a los Workers que detengan su bucle interno
        if hasattr(self, 'cam_worker'):
            self.cam_worker.stop() 
        
        # 2. Esperar a que los hilos terminen de forma segura
        if hasattr(self, 'cam_thread'):
            self.cam_thread.quit()
            self.cam_thread.wait() # Espera a que termine

        if hasattr(self, 'face_thread'):
            self.face_thread.quit()
            self.face_thread.wait() # Espera a que termine
            
        # 3. Liberar la captura de OpenCV
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
            
        # 4. Actualizar UI
        self.boton_abrir_camara.show()
        self.boton_cerrar_camara.hide()
        self.cam_live.hide()
        self.boton_guardar_foto.hide()
        self.label_estado_reconocimiento.setText("")
        self.label_estado_reconocimiento.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
        """)

    def onDestroy(self, event):
        # Asegurarse de llamar a cerrarCamara para limpiar los hilos al cambiar de pantalla
        self.cerrarCamara()
        print("Cerrando escaneo de rostro")
        event.accept()
    # def cerrarCamara(self):
    #     self.cap.release()
    #     self.boton_abrir_camara.show()
    #     self.boton_cerrar_camara.hide()
    #     self.cam_live.hide()
    #     self.boton_guardar_foto.hide()


    def abrirCamara(self):
        
        self.boton_abrir_camara.hide()
        self.boton_guardar_foto.show()
        self.cam_live.show()
        self.boton_cerrar_camara.show()
        self.label_estado_reconocimiento.setText("Escaneando rostro...")

        self.cargarDatosPersonas()
        self.iniciarCamaraWorker()

    def iniciarCamaraWorker(self):
        
        camaras_disponibles = []

        for camera_info in enumerate_cameras():

            camara = {"index": camera_info.index, "nombre": camera_info.name}
            camaras_disponibles.append(camara)

            print(f"Index: {camera_info.index}, Name: {camera_info.name}")

        camaras_disponibles = list({c['nombre']: c for c in camaras_disponibles}.values())

        modal = CamarasDisponibles(camaras_disponibles=camaras_disponibles)
        resultado = modal.exec()

        if resultado == QDialog.Accepted:
            # print("Camara seleccionada Aceptada")

            camara_es_ip = modal.getTipoCamara()
            print('camara_es_ip: ', camara_es_ip)
            camara = ""

            if not camara_es_ip:
                # camara_seleccionada = camaras_disponibles[modal.getCurrentIndexCombox()]
                camara = camaras_disponibles[modal.getCurrentIndexCombox()]["index"]

            if camara_es_ip:
                camara =  modal.getIpCamara()
                

            # camaras_seleccionadas = modal.getCurrentIndexCombox()
            # print('camaras_seleccionadas: ', camaras_seleccionadas)
        elif resultado == QDialog.Rejected:
            print("Rechazado")
            self.cerrarCamara()
            return
                                

        # self.cap = cv2.VideoCapture("http://192.168.10.66:4747/video")
        print('camara: ', camara)
        self.cap = cv2.VideoCapture(camara)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        self.cam_thread = QThread()
        self.face_thread = QThread()

        self.cam_worker = CameraWorker(self.cap)
        self.face_worker = FaceRecognitionWorkerRegistro(
            encodings_db=self.encodings_db,
            nombres_db=self.nombres_personas_db,
            ids_db=self.ids_personas_db
        )

        # 3. Mover a hilos
        self.cam_worker.moveToThread(self.cam_thread)
        self.face_worker.moveToThread(self.face_thread)

        # --- CONEXIONES CRÍTICAS ---

        # Flujo: Cámara -> Reconocimiento -> UI
        self.cam_worker.frame_ready.connect(self.face_worker.process_frame)
        self.face_worker.frame_processed.connect(self.update_image)

        # Señales de detección de persona
        self.face_worker.persona_identificada.connect(self.on_persona_identificada)
        self.face_worker.persona_nueva.connect(self.on_persona_nueva)

        # Limpieza automática al terminar
        self.cam_worker.finished.connect(self.cam_thread.quit)
        self.face_worker.finished.connect(self.face_thread.quit)
        
        # Iniciar
        self.cam_thread.started.connect(self.cam_worker.run)
        self.face_thread.start()
        self.cam_thread.start()

    def on_persona_identificada(self, nombre, persona_id, similitud):
        self.label_estado_reconocimiento.setText(f"Ya registrado: {nombre} ({similitud:.1f}%)")
        self.label_estado_reconocimiento.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                background-color: #d4edda;
                color: #155724;
            }
        """)

    def on_persona_nueva(self):
        self.label_estado_reconocimiento.setText("Listo para registrar")
        self.label_estado_reconocimiento.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                background-color: #fff3cd;
                color: #856404;
            }
        """)
        
    def liberar_todos_los_recursos(self):
        """Libera TODOS los recursos antes de cerrar"""
        
        # 1. Detener workers de cámara
        if hasattr(self, 'cam_worker') and self.cam_worker:
            print("Deteniendo worker de cámara...")
            self.cam_worker.stop()
        
        # 2. Detener worker de reconocimiento
        if hasattr(self, 'face_worker') and self.face_worker:
            print("Deteniendo worker de reconocimiento...")
            self.face_worker.stop()
        
        # 3. Esperar que terminen los threads
        self.esperar_threads()
        
        # 4. Liberar cámara física
        if hasattr(self, 'cap') and self.cap:
            if self.cap.isOpened():
                print("Liberando cámara física...")
                self.cap.release()
            self.cap = None
        
        # 5. Limpiar referencias
        self.cam_worker = None
        self.face_worker = None
        self.cam_thread = None
        self.face_thread = None
        
        print("Todos los recursos liberados")

    def esperar_threads(self, timeout=1000):
        """Espera que los threads terminen con timeout"""
        
        threads = []
        if hasattr(self, 'cam_thread') and self.cam_thread.isRunning():
            threads.append(("Cámara", self.cam_thread))
        if hasattr(self, 'face_thread') and self.face_thread.isRunning():
            threads.append(("Reconocimiento", self.face_thread))
        
        for nombre, thread in threads:
            print(f"Esperando thread de {nombre}...")
            if not thread.wait(timeout):  # Esperar máximo 1 segundo
                print(f"Thread de {nombre} no respondió, forzando...")
                thread.terminate()  # Forzar (solo como último recurso)
                thread.wait(500)
        # ... otras conexiones existentes ...
        # self.cam_worker.pausa_cambio.connect(self.on_camera_pause_changed)

        # --- FIN DE HILOS ---


    # def abrirCamara(self):
    #     self.boton_abrir_camara.hide()
    #     self.boton_guardar_foto.show()
    #     self.cam_live.show()
    #     # self.layout.removeWidget(self.boton_abrir_camara)
    #     # self.layout.addWidget(self.boton_cerrar_camara)
    #     self.boton_cerrar_camara.show()
    #     self.cargarDatosPersonas()
        # # Iniciar cámara
        # index = 0
        # arr = []

        # while index < 5:
        #     cap = cv2.VideoCapture(index)
        #     if cap.isOpened():
        #         arr.append(index)
                
        #     else:
        #         pass

        #     cap.release()
        #     index += 1    
            

        # self.cap = cv2.VideoCapture(0)
        # print('Lista de camaras: ', arr)

        # # Timer que lee frames cada 30 ms
        # self.timer = QTimer()
        # self.timer.timeout.connect(self.leerDatosCamara)
        # self.timer.start(0)
        
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

    # def leerDatosCamara(self):

    #     # self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 280)
    #     # self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 340)

    #     ret, frame = self.cap.read()

    #     self.frame_camera = frame

    #     if not ret:
    #         return

    #     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #     # results = None
    #     results = self.face_detection.process(rgb_frame)

    #     # results_mesh = self.face_mesh.process(rgb_frame)

    #     # landmarks = []

    #     # if results_mesh.multi_face_landmarks:
    #     #     face_landmarks = results_mesh.multi_face_landmarks[0]

    #     #     h, w, _ = rgb_frame.shape
    #     #     landmarks = [
    #     #         (int(lm.x * w), int(lm.y * h), lm.z)
    #     #         for lm in face_landmarks.landmark
    #     #     ]

    #     #     if landmarks:
    #     #         yaw = self.obtener_yaw(landmarks)
    #     #         pitch = self.obtener_pitch(landmarks)
    #     #         roll = self.obtener_roll(landmarks)
    #     #         self.evaluar_giro(yaw=yaw)
    #     #         print(f"Yaw: {yaw:.2f}º | Pitch: {pitch:.2f}º | Roll: {roll:.2f}º")



    #     if results.detections is  not None:
    #         h, w, _ = rgb_frame.shape

    #         for detection in results.detections:

    #             # Dibujar la detección
    #             # self.mp_drawing.draw_detection(rgb_frame, detection)

    #             # Bounding box relativa
    #             bbox = detection.location_data.relative_bounding_box
    #             x = int(bbox.xmin * w)
    #             y = int(bbox.ymin * h)
    #             width = int(bbox.width * w)
    #             height = int(bbox.height * h)

    #             # Asegurar límites válidos
    #             x = max(0, x)
    #             y = max(0, y)
    #             x2 = min(w, x + width)
    #             y2 = min(h, y + height)

    #             # Evitar recortes inválidos
    #             if x2 <= x or y2 <= y:
    #                 continue

    #             # Recortar rostro
    #             face_crop = rgb_frame[y:y2, x:x2]

    #             # Algunos modelos requieren al menos 1 canal, tamaño mínimo, etc.
    #             if face_crop.size == 0:
    #                 continue

                
    #             face_locations = face_recognition.face_locations(rgb_frame, model="hog")
    #             face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    #             self.face_mesh = mp.solutions.face_mesh.FaceMesh()

    #             # Código pendiente por comprender, esto salvo la detección multiple con identificación
    #             for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):

    #                 # resultados = []
    #                 resultados = face_recognition.compare_faces(self.encodings_db, encoding)

    #                 self.encoding_foto_capturada = encoding

    #                 if True in resultados:

    #                     index = resultados.index(True)

    #                     nombre = self.nombres_personas_db[index]

    #                     color = (0, 255, 0)

    #                     id = self.ids_personas_db[index]

    #                     nombre += ", ID: " + str(id)

    #                     # self.boton_guardar_foto.setEnabled(False)

    #                     if id in self.ids_personas_db:
    #                         pass
    #                     else:
    #                         self.ids_personas_indetificadas.appen(self.ids_personas_db[index])

    #                 else:
    #                     nombre = "Desconocido"
    #                     color = (0, 0, 255)
    #                     self.boton_guardar_foto.setEnabled(True)

    #                 # Dibujar rectángulo + nombre
    #                 cv2.rectangle(rgb_frame, (left, top), (right, bottom), color, 2)
    #                 cv2.putText(rgb_frame, nombre, (left, top - 10),
    #                             cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2, cv2.LINE_AA)

                
    #             # Ahora usar face_recognition para obtener los encodings
    #             # face_locations = face_recognition.face_locations(rgb_frame)
    #             # face_encodings = face_recognition.face_encodings(frame, face_locations)
    #             # print('face_encodings: ', face_encodings)

    #             # self.encoding_foto_capturada = face_encodings

    #             # if face_encodings:

    #             #     for encoding in face_encodings:
    #             #         # print("Encoding obtenido:", encoding)
    #             #         resultados = face_recognition.compare_faces(self.encodings_db, encoding)
    #             #         # distancia = face_recognition.face_distance(self.known_encodings, encoding)
    #             #         # print(f'Validación de comparación de datos biometricos', resultados)

    #             #         if True in resultados:
                            
    #             #             index = resultados.index(True)
    #             #             nombre = self.nombres_personas_db[index]

    #             #             #Dibujar el nombre en la detección
    #             #             cv2.putText(
    #             #                 rgb_frame,
    #             #                 nombre,
    #             #                 (x, y - 10),  # posición (arriba del rectángulo)
    #             #                 cv2.FONT_HERSHEY_SIMPLEX,
    #             #                 0.9,  # tamaño de la fuente
    #             #                 (0, 255, 0),  # color (verde)
    #             #                 2,  # grosor
    #             #                 cv2.LINE_AA
    #             #             )

    #             #             print(f'La persona es {nombre}')

    #             #         else:
    #             #                                     #Dibujar el nombre en la detección
    #             #             cv2.putText(
    #             #                 rgb_frame,
    #             #                 "Desconocido",
    #             #                 (x, y - 10),
    #             #                 cv2.FONT_HERSHEY_SIMPLEX,
    #             #                 0.9,
    #             #                 (0, 0, 255),  # rojo
    #             #                 2,
    #             #                 cv2.LINE_AA
    #             #             )

    #             #             print(f'La persona no esta registrada')

    #             # else:
    #             #     # No se pudo obtener el encoding con face_recognition
    #             #     print("No se detectó algun rostro")
    #     else:
            
    #         pass

    #     # Convertir para mostrar en QLabel
    #     h, w, ch = rgb_frame.shape
    #     bytes_per_line = ch * w
    #     qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
    #     self.cam_live.setPixmap(QPixmap.fromImage(qt_image))

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

        #obtener primero la foto del worker
        if hasattr(self, 'cam_worker') and self.cam_worker:
            frame = self.cam_worker.obtenerUltimoFrame()
            if frame is not None:
                
                pixmap_label = self.convertirFrameALabel(frame=frame)
                pixmap = self.convertirFrameAPixmap(frame=frame)
                
                if self.cantidad_fotos < 3:

                    self.almacenarFotos(pixmap_label=pixmap_label, pixmap=pixmap, frame=frame)

                    if self.cantidad_fotos < 3:
                        return

                self.botonGuardarFotoCambiarTexto(cambiar=1)

                self.pausarCamara()
                # rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
                # h, w, ch = rgb.shape
                # qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
                # pixmap = QPixmap.fromImage(qimg)
                
                self.modal = NombrarFotoCapturada(
                    self, 
                    #mandamos la foto que se mostrara en el modal
                    data= self.fotografias[1]["pixmap"], 
                    #mandamos todas las fotos en crudo
                    imagenes=self.obtenerFotografias(), 
                    #mandamos los encodings
                    encoding_frente= self.generarEncodingPro(self.fotografias[1]["data"]),
                    encoding_perfil_derecho= self.generarEncodingPro(self.fotografias[2]["data"]),
                    encoding_perfil_izquierdo= self.generarEncodingPro(self.fotografias[0]["data"])
                )
                # self.modal.show()
                self.resultado = self.modal.exec()
                
                if self.resultado == QDialog.Accepted:
                    # self.fotografias = []

                    # for item in range(self.cantidad_fotos):
                    #     print('item: ', item)
                    #     self.borrarFoto(item)
                    self.obtenerEncodingsDeFotos()
                    print("Aceptada")
                elif self.resultado == QDialog.Rejected:
                    print("Rechazado")
                        
                    # self.modal.accept()

                else:
                    print("Algo salio mal...")

                for item in range(self.cantidad_fotos):
                    print('item: ', item)
                    self.borrarFoto(item)

                self.reanudarCamara()
            return None
            
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

        self.encodings_db = []
        self.nombres_personas_db = []
        self.ids_personas_db = []

        self.getPersonas = self.dbManager.getPersonas()

        for persona in self.getPersonas:
            # 1. Cargamos los 3 encodings
            izq = json.loads(persona[3])
            fre = json.loads(persona[4])
            der = json.loads(persona[5])
            
            # 2. USAR EXTEND en lugar de append con corchetes
            # Extend añade los elementos de la lista uno por uno al nivel principal
            self.encodings_db.extend([izq, fre, der])
            
            # 3. Hacemos lo mismo con nombres e IDs para que los índices coincidan
            self.nombres_personas_db.extend([persona[1], persona[1], persona[1]])
            self.ids_personas_db.extend([persona[0], persona[0], persona[0]])

        # MUY IMPORTANTE: Convertir a array de Numpy al final para el Worker
        self.encodings_db = np.array(self.encodings_db)
        
        print(f"Base de datos cargada. Total de vectores: {len(self.encodings_db)}")
        print(f"Forma del array (debe ser N, 128): {self.encodings_db.shape}")

    # def onDestroy(self, event):
    #     print("Cerrando escaneo de rostro")
    #     # Esto sirve para al momento de cambiar la pantalla desde el menú, debemos liberar la cámara y que no 
    #     # sigan los procesos que no son terminados al cambiar de pantalla y que afectan al sistema
    #     if self.cap.isOpened():
    #         self.cap.release()
    #     event.accept()
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

    def convertirFrameALabel(self, frame):
        #esta función nos permite que las fotos puedan ser visibles en la interfaz
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        pixmap_label = QLabel()
        pixmap_label.setPixmap(pixmap)
        pixmap_label.setFixedSize(200, 200)
        pixmap_label.setScaledContents(True)

        return pixmap_label
    
    def convertirFrameAPixmap(self, frame):
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        return pixmap

    
    def almacenarFotos(self, pixmap_label, pixmap, frame):
        print(f"Tipo de pixmap_label: {type(pixmap_label)}")
        print(f"Tipo de pixmap: {type(pixmap)}")
        
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
            "data": frame,
            "pixmap": pixmap
        }

        print(f"Aún no, hay {self.cantidad_fotos} fotos")
        self.cantidad_fotos += 1

    def pausarCamara(self):
        """Pausa la cámara desde la UI"""
        if hasattr(self, 'cam_worker'):
            self.cam_worker.alternarEstado()
            # self.boton_pausa.setText("Reanudar")
            # self.boton_pausa.clicked.disconnect()
            # self.boton_pausa.clicked.connect(self.reanudarCamara)

    def reanudarCamara(self):
        """Reanuda la cámara desde la UI"""
        if hasattr(self, 'cam_worker'):
            self.cam_worker.alternarEstado()
            # self.boton_pausa.setText("Pausar")
            # self.boton_pausa.clicked.disconnect()
            # self.boton_pausa.clicked.connect(self.pausarCamara)

    def alternarPausaCamara(self):
        """Alterna pausa con un solo botón"""
        if hasattr(self, 'cam_worker'):
            self.cam_worker.alternarEstado()

    def generarEnconding(self, frame):
        
        if frame is None:
            return ("la foto no tiene datos")

        # Convertir a RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detectar rostro
        locations = face_recognition.face_locations(rgb)

        if len(locations) == 0:
            return("No se detectó rostro en la foto") 

        # Obtener encoding
        return face_recognition.face_encodings(rgb, locations)[0]

    # Al momento de registrar a la persona en tu modal:
    def generarEncodingPro(self, imagen_cv2):
        # Convertir a RGB
        rgb = cv2.cvtColor(imagen_cv2, cv2.COLOR_BGR2RGB)
        
        # Localizar la cara
        boxes = face_recognition.face_locations(rgb, model="hog")
        
        if not boxes:
            return None

        # AQUÍ ESTÁ EL REMUESTREO:
        # num_jitters=100 es el estándar de alta precisión. 
        # Hará que el encoding sea mucho más estable.
        encoding = face_recognition.face_encodings(
            rgb, 
            known_face_locations=boxes, 
            num_jitters=100, 
            model="large"
        )[0]
        
        return encoding
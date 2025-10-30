from PySide6 import QtWidgets
# , QtCore, QtGui
from PySide6.QtWidgets import (
    QPushButton,
    QLabel,
    QLineEdit,
    QScrollArea,
    QWidget,
    QDialog,
    QVBoxLayout
)
from PySide6.QtGui import (
    QImage,
    QPixmap,
    QGuiApplication,
)
from PySide6.QtCore import (
    QTimer,
    Qt
)
import mediapipe as mp
import face_recognition
import cv2
import json
# from ui.dialogs.example import DialogExample
from ui.dialogs.nombrarFotoCapturada import NombrarFotoCapturada
from database.db_manager import DBManager
import time

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
        self.scrollBarAreaFotos.setWidgetResizable(True)  # 👈 importante
        self.content_widget_scroll_bar = QWidget()

        self.layout_scroll_bar = QVBoxLayout(self.content_widget_scroll_bar)
        self.layout_scroll_bar.setContentsMargins(10, 10, 10, 10)
        self.layout_scroll_bar.setSpacing(10)

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
        self.face_detection = self.mp_face_detection.FaceDetection(min_detection_confidence=0.5)
        
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
        # self.layout.removeWidget(self.boton_abrir_camara)
        self.boton_abrir_camara.hide()
        self.boton_guardar_foto.show()
        self.cam_live.show()
        # self.layout.addWidget(self.boton_cerrar_camara)
        self.boton_cerrar_camara.show()
        # print("Camara")
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
        self.timer.start(30)

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

        ret, frame = self.cap.read()

        self.frame_camera = frame

        if not ret:
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_frame)

        if results.detections is not None:
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

                
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

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
            pixmap_label.setFixedSize(100, 100)
            pixmap_label.setScaledContents(True)
            
            if len(self.frames_camera) < 2:
                # Agregamos la imagen al layout
                self.layout_scroll_bar.addWidget(pixmap_label)
                self.frames_camera.append(self.frame_camera)
                print(f"Aún no, fotos {len(self.frames_camera)}")
                return

            self.cap.release()

            rgb = cv2.cvtColor(self.frame_camera, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            
            self.modal = NombrarFotoCapturada(self, data=pixmap, 
                                              imagen=self.frame_camera, 
                                              encodigns=self.encoding_foto_capturada)
            # self.modal.show()
            self.resultado = self.modal.exec()

            if self.resultado == QDialog.Accepted:
                print("Aceptada")
            elif self.resultado == QDialog.Rejected:
                print("Rechazado")
                
            self.abrirCamara()
            # self.modal.accept()

        else:
            print("Algo salio mal...")

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
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import (
    QPushButton,
    QLabel,
    QApplication
)
from PySide6.QtGui import (
    QImage,
    QPixmap,
    QGuiApplication
)
from PySide6.QtCore import (
    QTimer,
    Qt
)
import mediapipe as mp
import face_recognition
import cv2

class EscanerRostro(QtWidgets.QWidget):
    
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(QtWidgets.QLabel("Soy la pantalla de escaner"))

        self.boton_abrir_camara = self.botonInicializarCamara()
        self.boton_cerrar_camara = self.botonCerrarCamara()
        
        self.cam_live = QLabel(self)
        self.foto_de_camara = QLabel(self)


        self.layout.addWidget(self.cam_live, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.foto_de_camara)
        self.layout.addWidget(self.boton_abrir_camara)
        self.layout.addWidget(self.boton_cerrar_camara)

        #La ocultamos ya que la mostrará y ocultara muchas veces
        self.boton_cerrar_camara.hide()

        self.pantalla = QGuiApplication.primaryScreen()
        self.medidas_pantalla = self.pantalla.size()
        self.timer_update = QTimer()
        self.timer_update.timeout.connect(self.update)
        self.timer_update.start(30)
        
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(min_detection_confidence=0.5)
        self.mp_drawing = mp.solutions.drawing_utils

        known_image = face_recognition.load_image_file("src/img/gabe.jpeg")
        self.known_encodings = face_recognition.face_encodings(known_image)[0]

        #Marca error de formato en este apartado#
        # if not self.known_encodings:
        #     print("No se encontró rostro en la imagen conocida.")
        #     exit()


    def update(self):
        pass
        # print(f"Altura de la pantalla: {self.medidas_pantalla.width()}")
        # print(f"Ancho de la pantalla: {self.medidas_pantalla.height()}")


    def botonInicializarCamara(self):
        boton_abrir_camara = QPushButton("Abrir Cámara")
        boton_abrir_camara.setStatusTip("Abrir cámara para detectar rostro")
        
        # conectas la acción
        boton_abrir_camara.clicked.connect(self.abrirCamara)  # <-- Aquí el fix
        return boton_abrir_camara

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

    def abrirCamara(self):
        # self.layout.removeWidget(self.boton_abrir_camara)
        self.boton_abrir_camara.hide()
        self.cam_live.show()
        # self.layout.addWidget(self.boton_cerrar_camara)
        self.boton_cerrar_camara.show()
        print("Camara")

        # Iniciar cámara
        self.cap = cv2.VideoCapture(0)

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
                self.mp_drawing.draw_detection(rgb_frame, detection)

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
                
                # Ahora usar face_recognition para obtener los encodings
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                if face_encodings:
                    encoding = face_encodings[0]
                    print("Encoding obtenido:", encoding)
                    resultados = face_recognition.compare_faces(self.known_encodings, face_encodings)
                    distancia = face_recognition.face_distance(self.known_encodings, face_encodings)[0]
                    print(f'Validación de comparación de datos biometricos', resultados)

                    if True in resultados:
                        print(f'Persona identificada como Gabe Newell')
                    else:
                        print(f'La persona no es Gabe Newell')

                else:
                    # No se pudo obtener el encoding con face_recognition
                    print("No se detectó algun rostro")



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


    def capturarFoto(self):
        if self.foto_de_camara is not None:
            rgb = cv2.cvtColor(self.frame_actual, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            self.cam_live.setPixmap(pixmap)
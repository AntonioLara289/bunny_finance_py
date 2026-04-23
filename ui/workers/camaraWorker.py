from PySide6.QtCore import QObject, Signal, QMutex, QMutexLocker
import cv2
import time
import numpy as np

class CameraWorker(QObject):
    frame_ready = Signal(np.ndarray)
    finished = Signal()
    pausa_cambio = Signal(bool)

    def __init__(self, cap: cv2.VideoCapture, parent=None):
        super().__init__(parent)
        self.cap = cap
        self._running = True
        self._pausado = False 
        
        self.ultimo_frame = None
        # Usamos QMutex que es más nativo para Qt
        self.mutex = QMutex()

    def run(self):
        """Bucle principal."""
        try:
            while self._running:
                if self._pausado:
                    time.sleep(0.1)
                    continue

                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret:
                        self.frame_ready.emit(frame)
                        with QMutexLocker(self.mutex):
                            self.ultimo_frame = frame.copy()
                    else:
                        # Si no hay frame, esperamos un poco para reintentar
                        time.sleep(0.01)
                else:
                    break
                
                time.sleep(0.01) # ~100 FPS es más que suficiente
        except Exception as e:
            print(f"Error en CameraWorker: {e}")
        finally:
            pass
            # self.liberar_recursos()
            # self.finished.emit()

    def stop(self):
        """Detiene el hilo definitivamente."""
        self._running = False

    def obtenerUltimoFrame(self):
        with QMutexLocker(self.mutex):
            return self.ultimo_frame.copy() if self.ultimo_frame is not None else None
        
    def set_pausa(self, estado: bool):
        """Método unificado para pausar/reanudar sin matar el hilo."""
        self._pausado = estado
        self.pausa_cambio.emit(estado)
        print(f"Cámara {'pausada' if estado else 'reanudada'}")

    def alternarEstado(self):
        self.set_pausa(not self._pausado)

    def liberar_recursos(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        print("Recursos de cámara liberados.")
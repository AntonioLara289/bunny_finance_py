from PySide6.QtCore import Signal, QObject
import random
class Calculo(QObject):
    # Definimos una señal que enviará un entero
    signalCalculo = Signal(int)

    def __init__(self):
        super().__init__()

    def enviarCalculo(self):
        calculo = random.randint(1, 100) * random.randint(1, 100)
        self.signalCalculo.emit(calculo)



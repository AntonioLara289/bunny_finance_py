# Clase de historial, los contenidos se muestran en historial
# Esta es una clase estatica, no nececitas crear una instancia de ella para utilizarla
# 	similar a un namespace en C++, solo debe ser usada como si ya existiera un objeto de esta.

from collections import deque
from datetime import datetime

historial = deque(maxlen=100)

class log:
    @staticmethod
    def push(accion: str, resultado: str = ""):
        historial.append({
            "hora": datetime.now().strftime("%H:%M:%S"),
            "accion": accion,
            "resultado": resultado
        })

    @staticmethod
    def all():
        return list(historial)

    @staticmethod
    def clear():
        historial.clear()

    @staticmethod
    def print():
        for entry in historial:
            print(f"[{entry['hora']}] > {entry['accion']}")
            if entry["resultado"]:
                print(f"    {entry['resultado']}")

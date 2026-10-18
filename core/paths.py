"""Rutas absolutas del proyecto.

DBManager usa por defecto "database/bunny_detect_v2.db", una ruta relativa que
depende del directorio de trabajo. Estos helpers la resuelven contra la raiz
del proyecto para que la consola funcione igual se llame desde donde se llame.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DB_PATH = os.path.join(BASE_DIR, "database", "bunny_detect_v2.db")
FACES_DB_PATH = os.path.join(BASE_DIR, "faces.db")


def from_base(*parts: str) -> str:
    return os.path.join(BASE_DIR, *parts)

"""Capa de servicios de Bunny Finance.

Logica de negocio sin Qt, compartida por la interfaz grafica (ui/) y por la
consola (cli/). Todo lo que se pueda resolver aqui se resuelve aqui para que
las dos interfaces se comporten exactamente igual.

Las rutas de las bases de datos se resuelven siempre contra la raiz del
proyecto, nunca contra el directorio de trabajo actual.
"""

from core.paths import BASE_DIR, DATA_DB_PATH, FACES_DB_PATH
from core.services import (
    ESTATUS_CODIGO_A_TEXTO,
    ESTATUS_TEXTO_A_CODIGO,
    Asistencia,
    Core,
    Diagnostico,
    ErrorServicio,
    Persona,
    RosterEntry,
    Sesion,
)

__all__ = [
    "BASE_DIR",
    "DATA_DB_PATH",
    "FACES_DB_PATH",
    "ESTATUS_CODIGO_A_TEXTO",
    "ESTATUS_TEXTO_A_CODIGO",
    "Asistencia",
    "Core",
    "Diagnostico",
    "ErrorServicio",
    "Persona",
    "RosterEntry",
    "Sesion",
]

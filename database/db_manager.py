import sqlite3
import numpy as np
import ast
from datetime import datetime

class DBManager:

    db_path = None

    def __init__(self, db_path="database/bunny_detect_v2.db"):
        self.conn = sqlite3.connect(db_path)
        self.db_path = db_path
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA table_info(table_name)")
        self.crearTablaPersonas()
        self.crearTablaSesiones()
        self.crearTablaAsistencias()

    def getColumns(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA table_info(personas)")
        columns = len(self.cursor.fetchall())
        self.cursor.close()
        self.conn.close()
        return columns

    def getRows(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT COUNT(*) FROM personas")
        rows = self.cursor.fetchone()[0]
        self.cursor.close()
        self.conn.close()
        return rows
        #self.crearTablaHistorial()
        
    def getPersonasData(self):
        # La tabla se asegura con su propia conexión: crearla aquí reasignaba
        # self.conn y dejaba self.cursor apuntando a una conexión ya cerrada.
        self.crearTablaPersonas()

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("SELECT * FROM personas where estatus = 1")

        filas = self.cursor.fetchall()

        self.conn.close()

        return filas
        
    def crearTablaPersonas(self):

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("CREATE TABLE IF NOT EXISTS personas (" \
        "id_persona INTEGER PRIMARY KEY AUTOINCREMENT, " \
        "nombre_persona TEXT NOT NULL, " \
        "imagen TEXT NOT NULL, " \
        "encoding_perfil_izquierdo TEXT NOT NULL, " \
        "encoding_frente TEXT NOT NULL, " \
        "encoding_perfil_derecho TEXT NOT NULL, " \
        "estatus INTEGER NOT NULL, " \
        "created_at TEXT NOT NULL)")

        self.conn.commit()
        self.conn.close()
    
    def getPersonas(self):

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # print("creando tabla")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS personas (" \
        "id_persona INTEGER PRIMARY KEY AUTOINCREMENT, " \
        "nombre_persona TEXT NOT NULL, " \
        "imagen TEXT NOT NULL, " \
        "encoding_perfil_izquierdo TEXT NOT NULL, " \
        "encoding_frente TEXT NOT NULL, " \
        "encoding_perfil_derecho TEXT NOT NULL, " \
        "estatus INTEGER NOT NULL, " \
        "created_at TEXT NOT NULL)")

        self.cursor.execute("SELECT * FROM personas where estatus = 1")
        filas = self.cursor.fetchall()

        self.conn.commit()
        self.conn.close()

        return filas

    def getEncodings(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute(
            "SELECT encoding_perfil_izquierdo, encoding_frente, encoding_perfil_derecho "
            "FROM personas WHERE estatus = 1"
        )
        rows = self.cursor.fetchall()

        self.conn.close()

        # Devuelve un vector de 3 x N (izquierdo, frente, derecho) por persona
        filas = []
        for izquierda, frente, derecho in rows:
            try:
                filas.append(np.array([
                    np.asarray(ast.literal_eval(izquierda), dtype=np.float64),
                    np.asarray(ast.literal_eval(frente), dtype=np.float64),
                    np.asarray(ast.literal_eval(derecho), dtype=np.float64),
                ]))
            except (ValueError, SyntaxError):
                # Fila corrupta o preexistente con otro formato: se omite
                continue
        return filas

    def getPersonasConEmbeddings(self):
        """Devuelve [(nombre, embedding_frente), ...] de las personas activas.

        Es la fuente de datos que usa la vista UMAP. Se lee de la misma tabla
        que el resto de la aplicacion ("personas" en bunny_detect_v2.db) para
        que las personas recien registradas aparezcan en la visualizacion.

        Se usa el encoding frontal porque es el que usa el reconocimiento.
        """
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute(
            "SELECT nombre_persona, encoding_frente FROM personas WHERE estatus = 1"
        )
        rows = self.cursor.fetchall()

        self.conn.close()

        resultado = []
        for nombre, encoding_frente in rows:
            try:
                emb = np.asarray(ast.literal_eval(encoding_frente), dtype=np.float64)
            except (ValueError, SyntaxError, TypeError):
                # Fila corrupta: se omite para no desalinear nombre y embedding
                continue
            if emb.ndim == 1 and emb.size:
                resultado.append((nombre, emb))

        return resultado

    def crearTablaHistorial(self):

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("CREATE TABLE IF NOT EXISTS historial_detecciones (id_deteccion INTEGER PRIMARY KEY AUTOINCREMENT, key_persona INTEGER NOT NULL, fecha TEXT NOT NULL)")

        self.conn.commit()
        self.conn.close()

    def crearTablaSesiones(self):

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # Stored times as 24-hour HH:MM strings
        self.cursor.execute("CREATE TABLE IF NOT EXISTS sesiones (" \
        "id_sesion INTEGER PRIMARY KEY AUTOINCREMENT, " \
        "nombre TEXT NOT NULL, " \
        "inicio TEXT NOT NULL, " \
        "fin TEXT NOT NULL)")

        self.conn.commit()
        self.conn.close()

    def getSesiones(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("CREATE TABLE IF NOT EXISTS sesiones (" \
        "id_sesion INTEGER PRIMARY KEY AUTOINCREMENT, " \
        "nombre TEXT NOT NULL, " \
        "inicio TEXT NOT NULL, " \
        "fin TEXT NOT NULL)")

        self.cursor.execute("SELECT id_sesion, nombre, inicio, fin FROM sesiones")
        filas = self.cursor.fetchall()

        self.conn.commit()
        self.conn.close()

        return filas

    def guardarSesion(self, nombre, inicio_hhmm, fin_hhmm):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        data = (nombre, inicio_hhmm, fin_hhmm)

        self.cursor.execute("INSERT INTO sesiones (nombre, inicio, fin) VALUES (?, ?, ?)", data)
        last_id = self.cursor.lastrowid

        self.conn.commit()
        self.conn.close()

        return last_id

    def actualizarSesion(self, id_sesion, nombre, inicio_hhmm, fin_hhmm):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute(
            "UPDATE sesiones SET nombre = ?, inicio = ?, fin = ? WHERE id_sesion = ?",
            (nombre, inicio_hhmm, fin_hhmm, id_sesion)
        )

        self.conn.commit()
        self.conn.close()

    def eliminarSesion(self, id_sesion):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("DELETE FROM sesiones WHERE id_sesion = ?", (id_sesion,))

        self.conn.commit()
        self.conn.close()

    def crearTablaAsistencias(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("CREATE TABLE IF NOT EXISTS asistencias (" \
        "id_asistencia INTEGER PRIMARY KEY AUTOINCREMENT, " \
        "id_persona INTEGER NOT NULL, " \
        "id_sesion INTEGER NOT NULL, " \
        "fecha TEXT NOT NULL, " \
        "presente INTEGER NOT NULL)")

        self.conn.commit()
        self.conn.close()

    def guardarAsistencia(self, id_persona, id_sesion, presente, fecha_iso=None):
        if fecha_iso is None:
            fecha_iso = datetime.now().isoformat()

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        data = (id_persona, id_sesion, fecha_iso, int(bool(presente)))

        self.cursor.execute("INSERT INTO asistencias (id_persona, id_sesion, fecha, presente) VALUES (?, ?, ?, ?)", data)

        self.conn.commit()
        self.conn.close()

    def guardarHistorial(self, key_persona):

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS historial_detecciones (id_deteccion INTEGER PRIMARY KEY AUTOINCREMENT, key_persona INTEGER NOT NULL, fecha TEXT NOT NULL)"
        )

        data = (key_persona, datetime.now().isoformat())

        self.cursor.execute("INSERT INTO historial_detecciones (key_persona, fecha) VALUES (?, ?)", data)

        self.conn.commit()
        self.conn.close()

    def guardarPersonaData(self, 
                           nombre_persona, 
                           imagen, 
                           encoding_frente, 
                           encoding_perfil_derecho, 
                           encoding_perfil_izquierdo
                           ):

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        data = (nombre_persona, imagen, encoding_frente, encoding_perfil_derecho, encoding_perfil_izquierdo, 1, datetime.now().isoformat())

        self.cursor.execute("INSERT INTO personas (nombre_persona, imagen, encoding_frente, encoding_perfil_derecho, encoding_perfil_izquierdo, estatus, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", data)

        self.conn.commit()
        self.conn.close()
    
    def getBalances(self):
        # Antes reutilizaba self.conn/self.cursor, que ya venían cerrados desde
        # el último método ejecutado y provocaban "Cannot operate on a closed database".
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS balance_actual ("
            "id_balance INTEGER PRIMARY KEY AUTOINCREMENT, balance REAL, created_at TEXT)"
        )
        self.conn.commit()

        self.cursor.execute("SELECT * FROM balance_actual;")
        filas = self.cursor.fetchall()

        self.conn.close()

        # Si hay datos
        if filas:
            return filas
        else:
            print("No hay datos.")
            return []

        
    def dbConection(self):
        return sqlite3.connect(self.db_path)

    def update_status(self, person_id, new_status):
        status_map = {
            "activado": 1,
            "desactivado": 0,
            "pendiente": 2
        }
        status_value = status_map.get(new_status, 0)

        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE personas SET estatus = ? WHERE id_persona = ?",
            (status_value, person_id)
        )
        self.conn.commit()
        self.conn.close()
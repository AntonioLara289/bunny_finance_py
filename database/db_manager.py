import sqlite3
from datetime import datetime

class DBManager:

    db_path = None

    def __init__(self, db_path="database/bunny_detect.db"):
        self.conn = sqlite3.connect(db_path)
        self.db_path = db_path
        self.cursor = self.conn.cursor()

    def getPersonasData(self):
        
        self.cursor.execute("CREATE TABLE IF NOT EXISTS personas (" \
        "id_persona INTEGER PRIMARY KEY AUTOINCREMENT, " \
        "nombre_persona TEXT NOT NULL, " \
        "imagen TEXT NOT NULL, " \
        "encodes TEXT NOT NULL, " \
        "created_at TEXT NOT NULL)")

        filas = self.cursor.fetchall()

        self.conn.close()

        return filas
    
    def guardarPersonaData(self, nombre_persona, imagen, encodes):

        self.conn = sqlite3.connect(self.db_path)

        data = (nombre_persona, imagen, encodes, datetime.now().isoformat())

        self.conn.execute("INSERT INTO personas (imagen, encodes, created_at) VALUES (?, ?, ?)", data)

        self.conn.commit()

        self.conn.close() 
    
    def getBalances(self):

        self.cursor.execute("CREATE TABLE IF NOT EXISTS balance_actual (id_balance INTEGER PRIMARY KEY AUTOINCREMENT, balance REAL, created_at TEXT)")
        last_id_balance = self.cursor.execute("SELECT * FROM balance_actual;")
        filas = self.cursor.fetchall()

        self.conn.close()
        
        # Si hay datos
        if filas:
            # id_balance, balance, created_at = filas            
            return filas
            # i = 1

            # for fila in filas:
            #     id_balance, balance, created_at = fila
            #     print("ID:", id_balance)
            #     print("Balance:", balance)
            #     print("Fecha:", created_at)
            #     print("ID:", id_balance)
            #     print("Balance:", balance)
            #     print("Fecha:", created_at)
            #     print(fila)

            #     i = i + 1
        else:
            print("No hay datos.")
            return []
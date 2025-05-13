import sqlite3

class DBManager:

    def __init__(self, db_path="database/finanza.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

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
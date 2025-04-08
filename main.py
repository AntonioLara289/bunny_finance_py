from tkinter import *
from tkinter import ttk

root = Tk()
frm = ttk.Frame(root, padding=10)
frm.grid()
ttk.Label(frm, text="Hello World!").grid(column=0, row=0)
ttk.Button(frm, text="Quit", command=root.destroy).grid(column=1, row=0)
root.mainloop()

import sqlite3
con = sqlite3.connect("finanza.db")

cur = con.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS balance_actual (id_balance INTEGER PRIMARY KEY AUTOINCREMENT, balance REAL, created_at TEXT)")

# cur.execute("INSERT INTO balance_actual (balance, created_at) VALUES (2702.00, '07/04/2025')")
last_id_balance = cur.execute("SELECT * FROM balance_actual where id_balance = (SELECT MAX(id_balance) from balance_actual);")
fila = cur.fetchone()

# Si hay datos
if fila:
    id_balance, balance, created_at = fila
    print("ID:", id_balance)
    print("Balance:", balance)
    print("Fecha:", created_at)
else:
    print("No hay datos.")

con.close()

# con.commit()
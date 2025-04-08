from tkinter import *
from tkinter import ttk
import sqlite3
conection = sqlite3.connect("finanza.db")

cur = conection.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS balance_actual (id_balance INTEGER PRIMARY KEY AUTOINCREMENT, balance REAL, created_at TEXT)")

cur.execute("INSERT INTO balance_actual (balance, created_at) VALUES (2702.00, '07/04/2025')")

conection.commit()
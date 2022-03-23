import sqlite3
from pathlib import Path


db = Path(__file__).parent / "../flask/concentration_grade.db"
conn = sqlite3.connect(db)

id = input("Enter ID: ")
time = input("Enter time interval: ")
grade = float(input("Enter concent grade: "))
sql = "INSERT INTO grades (id, interval, grade) VALUES (?, ?, ?);"
with conn:
    conn.execute(sql, (id, time, grade))
conn.close()

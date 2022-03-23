""" Display grades. """

import sqlite3
from pathlib import Path


db = Path(__file__).parent / "../flask/concentration_grade.db"
conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)

rows = conn.execute("SELECT * FROM grades;")
for row in rows:
    for field in row:
        print(field, end="\t")
    print()

conn.close()

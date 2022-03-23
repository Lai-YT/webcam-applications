""" Display grades. """

import sqlite3
from pathlib import Path


# go get the shared database
db = Path(__file__).parent / "../flask/concentration_grade.db"
# read-only since we're now simply displaying grades.
conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row

print("ID\tInterval\tGrade")
rows = conn.execute("SELECT * FROM grades;").fetchall()
for row in rows:
    print("{}\t{}\t{}".format(row["id"], row["interval"], row["grade"]))

conn.close()

# Display grades
import sqlite3


grades = "concentration_grade.db"
conn = sqlite3.connect(grades)

conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("select * from concentration_grade;")
rows = cur.fetchall()
print("ID\tInterval\tGrade")
for row in rows:
    print("{}\t{}\t{}".format(row['id'], row['interval'], row['grade']))

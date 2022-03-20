# Display grades
import sqlite3


grades = "concentration_grade.db"
conn = sqlite3.connect(grades)

rows = conn.execute("select * from concentration_grade;")
for row in rows:
    for field in row:
        print("{}\t".format(field), end="")
    print()
conn.close()

import sqlite3


grades = "concentration_grade.db"
conn = sqlite3.connect(grades)

id = input("Enter ID: ")
time = input("Enter time interval: ")
grade = float(input("Enter concent grade: "))
sql_str = "insert into concentration_grade(id, interval, grade) values('{}','{}',{});".format(id, time, grade)
conn.execute(sql_str)
conn.commit()
conn.close()

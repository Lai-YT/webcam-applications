import openpyxl

import fuzzy.parse as parse
from fuzzy.classes import GoodInterval


intervals = parse.read_intervals_from_json("good_intervals.json")

workbook = openpyxl.Workbook()
sheet = workbook.active

sheet.append(["start", "end", "grade"])
for interval in intervals:
    sheet.append([interval.start, interval.start + 60, interval.grade])

workbook.save(filename="good_intervals.xlsx")

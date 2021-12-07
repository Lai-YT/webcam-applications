from typing import List

from fuzzy.classes import Grade


SEPARATOR = "---"
# index mapping
BLINK = 0
BODY = 1
GRADE = 2

def is_separator(line: str) -> bool:
    return line.startswith(SEPARATOR)

def parse_grades(filename: str) -> List[Grade]:
    grades = []
    with open(filename, mode="r") as f:
        # blink rate (int), body concent (float), normalized grade (float)
        data = [0, 0.0, 0.0]
        types = [int, float, float]
        # pos is to record the current parsing data
        pos = 0
        for line in f:
            line = line.strip()
            if is_separator(line):
                grades.append(Grade(data[BLINK], data[BODY], data[GRADE]))
                pos = 0
                continue
            data[pos] = types[pos](line)
            pos += 1
    return grades

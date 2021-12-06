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
    with open("fuzzy_grades.txt", mode="r") as f:
        data = [0, 0.0, 0.0]
        types = [int, float, float]
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

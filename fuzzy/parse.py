from typing import List

from fuzzy.classes import Grade


SEPARATOR: str = "---"

def is_separator(line: str) -> bool:
    return line.startswith(SEPARATOR)


# index mapping
BLINK: int = 0
BODY: int = 1
GRADE: int = 2

def parse_grades(filename: str) -> List[Grade]:
    """Parse lines in designated file into list of Grades.

    Arguments:
        filename:
            The file which contains lines of grade. The first line should be
            blink rate, second be body concentration, third be the grade and
            ends with the separator "---"; which is the following format:
                11    <- 1st blink rate
                0.8   <- 1st body concent.
                0.65  <- 1st grade
                ---   <- 1st separator
                11    <- 2nd blink rate
                0.9   <- 2nd body concent.
                0.7   <- 2nd grade
                ---   <- 2nd separator
            The file is opened in "r" mode.
    """
    grades: List[Grade] = []
    with open(filename, mode="r") as f:
        # blink rate (int), body concent (float), normalized grade (float)
        # They're first stored as str and converted to their corresponding
        # type later.
        data: List[str] = ["", "", ""]
        # pos is to record the current parsing data
        pos: int = 0
        line: str
        for line in f:
            line = line.strip()
            if is_separator(line):
                grades.append(Grade(int(data[BLINK]),
                                    float(data[BODY]),
                                    float(data[GRADE])))
                pos = 0
                continue
            data[pos] = line
            pos += 1
    return grades

import json
from typing import Dict, List, Union

from fuzzy.classes import Grade


def save_grades_to_json(filename: str, grades: List[Grade]) -> None:
    """Converts the grades into the format of json and saves them.

    Arguments:
        filename: The json file to save the grades.
        grades: The grades to save.
    """
    with open(filename, mode="w+", encoding="utf-8") as f:
        # saves the dict of each grade
        json.dump([grade.__dict__ for grade in grades], f, indent=2)


def read_grades_from_json(filename: str) -> List[Grade]:
    """Returns the grades read from the json file.

    Arguments:
        filename: The json file which contains the grades.
    """
    def to_grade_object(raw_grade: Dict[str, Union[int ,float]]) -> Grade:
        """Converts the dict of blink, body and grade in to Grade object."""
        return Grade(**raw_grade)  # type: ignore
        # type ignored since mypy fails on such infer types

    with open(filename, mode="r", encoding="utf-8") as f:
        grades: List[Grade] = json.load(f, object_hook=to_grade_object)
    return grades

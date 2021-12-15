import json
from typing import Dict, List, Union

from fuzzy.classes import Grade, Interval


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


def read_intervals_from_json(filename: str) -> List[Interval]:
    """Returns the intervals read from the json file.

    Arguments:
        filename: The json file which contains the intervals.
    """
    def to_good_interval_object(raw_interval: Dict[str, Union[int ,float]]) -> Interval:
        """Converts the dict of start and grade in to Interval object."""
        return Interval(**raw_interval)  # type: ignore
        # type ignored since mypy fails on such infer types

    with open(filename, mode="r", encoding="utf-8") as f:
        intervals: List[Interval] = json.load(f, object_hook=to_good_interval_object)
    return intervals


def append_to_json(filename: str, x: Dict) -> None:
    with open(filename, mode="r+", encoding="utf-8") as f:
        data: List = json.load(f)
        data.append(x)
        f.seek(0)  # reset the file pointer to position 0
        json.dump(data, f, indent=2)


def init_json(filename: str) -> None:
    with open(filename, mode="w+", encoding="utf-8") as f:
        f.write("[]")

from dataclasses import dataclass
from typing import Optional


@dataclass
class Grade:
    """This data class stores the grade; and the corresponding blink rate and
    body concentration value of it.

    Data:
        blink
        body
        grade
    """
    blink: Optional[int]  # None occurs when face existence is low.
    body: float
    grade: float


@dataclass
class GoodInterval:
    """This data class stores the start time (epoch) and grade of a good
    concentration interval.

    Data:
        start
        grade
    """
    start: int
    grade: Grade

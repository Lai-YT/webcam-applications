from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Grade:
    """This data class stores the grade, and the corresponding blink rate and
    body concentration value of it.
    """
    grade: float
    blink: Optional[int]  # None occurs when face existence is low.
    body: float


@dataclass(order=True)
class Interval:
    """This data class stores the start time, end time (epoch) and grade of an
    interval.

    Interval is comparable as if it's the tuple (start, end).
    """
    start: int
    end: int
    # When comparing the intervals, grades aren't taken under consideration.
    # None means this interval isn't graded.
    grade: Optional[float] = field(default=None, compare=False)

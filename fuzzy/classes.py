from dataclasses import dataclass


@dataclass
class Grade:
    """This data class stores the grade; and the corresponding blink rate and
    body concentration value of it.
    """
    blink: int
    body: float
    grade: float

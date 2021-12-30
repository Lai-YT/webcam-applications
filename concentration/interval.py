from enum import Enum, auto


class IntervalType(Enum):
    """The types of interval that may trigger the grading process.""" 
    REAL_TIME = auto()
    LOOK_BACK = auto()
    LOW_FACE  = auto()

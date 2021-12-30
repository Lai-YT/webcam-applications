from enum import IntEnum


class IntervalType(IntEnum):
    """
    The types of interval that may trigger the grading process.
    Value indicates the priority,
    the lower the value is, the higher the priority is.
    """
    LOOK_BACK = 10
    LOW_FACE  = 20
    REAL_TIME = 30

from enum import IntEnum


class IntervalType(IntEnum):
    """
    The types of interval that may trigger the grading process.
    Value indicates the priority,
    the lower the value is, the higher the priority is.
    """
    LOW_FACE  = 10
    REAL_TIME = 20
    LOOK_BACK = 30

from enum import IntEnum


class IntervalType(IntEnum):
    """
    The types of interval that may trigger the grading process.
    Value indicates the priority,
    the lower the value is, the higher the priority is.
    """

    # current window interval by low face existence
    LOW_FACE = 10
    # current window interval by good blink rate
    REAL_TIME = 20
    # previous window interval by a successive record on current window
    EXTRUSION = 30
    # previous window interval by a full window
    LOOK_BACK = 40

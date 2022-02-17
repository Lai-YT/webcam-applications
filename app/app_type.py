from enum import Enum, auto


class ApplicationType(Enum):
    """The type of applcations."""
    BRIGHTNESS_OPTIMIZATION = auto()
    DISTANCE_MEASUREMENT = auto()
    FOCUS_TIMING = auto()
    POSTURE_DETECTION = auto()

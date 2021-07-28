"""
This file is path sensitive.
To make it work correctly, put under same directiory with the file which imports this file.
"""

import os


def to_abs_path(path: str) -> str:
    """Returns the absolute path."""
    cwd: str = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(cwd, path))

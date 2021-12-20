from pathlib import Path


TOP_LEVEL_DIR = Path(__file__).resolve().parents[1]


def to_abs_path(relative_path: str) -> str:
    """Returns the absolute path.

    Arguments:
        relative_path: Related to the top-level of this project.
    """
    return str(TOP_LEVEL_DIR.joinpath(relative_path))

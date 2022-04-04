from functools import partial
from typing import Callable

from PyQt5.QtCore import QThread


class TaskWorker(QThread):
    """Takes a task function and arbitrary number of that function's parameters
    and runs the task function in a new thread.
    """
    def __init__(self, task_callback: Callable, *args, **kwargs) -> None:
        super().__init__()
        self._task_callback = partial(task_callback, *args, **kwargs)

    # Override
    def run(self) -> None:
        """Runs the worker in a new thread.

        This method is called indirectly by QThread.start().
        """
        self._task_callback()

import time
from functools import partial
from typing import Optional

from PyQt5.QtCore import QObject, QThread, pyqtSignal


class TaskWorker(QThread):
    """Takes a task function and arbitrary number of that function's parameters
    and runs the task function in a new thread.
    """
    def __init__(self, task_callback, *args, **kwargs):
        super().__init__()
        self._task_callback = partial(task_callback, *args, **kwargs)

    # Override
    def run(self) -> QThread:
        """Runs the worker in a new thread.

        This is a convenient methods that allows you to not manually
        handle the boilerplate.

        Arguments:
            stop_signal:
                If provided, its emission quits the thread and stops the work.

        Returns:
            The thread which this worker is running in.
        """
        self._task_callback()

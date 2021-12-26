from functools import partial

from PyQt5.QtCore import QObject, pyqtSignal


class TaskWorker(QObject):
    """This TaskWorker is a worker class to move into QThread.
    It takes a task function and arbitrary number of that function's parameters.
    Only A simple run method is implemented, which calls the task function with
    the parameters.
    """

    # Emit after the task is finished.
    s_finished = pyqtSignal()

    def __init__(self, task_callback, *args, **kwargs):
        super().__init__()
        self._task_callback = partial(task_callback, *args, **kwargs)

    def run(self):
        self._task_callback()
        self.s_finished.emit()

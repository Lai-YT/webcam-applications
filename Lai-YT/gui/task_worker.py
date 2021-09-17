from functools import partial

from PyQt5.QtCore import QObject, pyqtSignal


class TaskWorker(QObject):
    """This TaskWorker is a worker class to move into QThread.
    It takes a task function and arbitrary number of that function's parameters.
    Only A simple run method is implemented, which calls the task function and
    pass in those parameters.
    """

    s_finished = pyqtSignal()

    def __init__(self, worker_callback, *args, **kwargs):
        super().__init__()
        self._worker_callback = partial(worker_callback, *args, **kwargs)

    def run(self):
        self._worker_callback()

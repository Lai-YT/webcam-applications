from functools import partial
from typing import Optional

from PyQt5.QtCore import QObject, QThread, pyqtSignal


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

    def run_in_thread(self, stop_signal: Optional[pyqtSignal] = None) -> QThread:
        """Runs the worker in a new thread.

        This is a convenient methods that allows you to not manually
        handle the boilerplate.

        Arguments:
            stop_signal:
                If provided, its emission quits the thread and stops the work.

        Returns:
            The thread which this worker is running in.
        """
        thread = QThread()
        self.moveToThread(thread)
        # Worker starts running after the thread is started.
        thread.started.connect(self.run)
        # The thread can be quit by the external stop signal
        # or the internal work finished signal.
        if stop_signal is not None:
            stop_signal.connect(thread.quit)
            stop_signal.connect(self.deleteLater)
        self.s_finished.connect(thread.quit)
        self.s_finished.connect(self.deleteLater)

        thread.finished.connect(thread.deleteLater)

        thread.start()
        return thread

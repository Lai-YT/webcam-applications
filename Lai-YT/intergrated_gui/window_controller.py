from PyQt5.QtCore import QObject, QThread

from gui.task_worker import TaskWorker
from intergrated_gui.panel_controller import PanelController
from lib.app_ import WebcamApplication


class WindowController(QObject):
    def __init__(self, window):
        super().__init__()

        self._window = window
        self._app = WebcamApplication()
        self._panel_controller = PanelController(window.widgets["panel"], self._app)

        self._connect_signals()
        self._start_app()

    def _start_app(self):
        self._worker = TaskWorker(self._app.start)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        # Worker starts running after the thread is started.
        self._thread.started.connect(self._worker.run)
        # The job of thread and worker is finished after the App. calls stop.
        self._app.s_stopped.connect(self._thread.quit)
        self._app.s_stopped.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _connect_signals(self):
        self._app.s_frame_refreshed.connect(self._window.widgets["frame"].set_frame)
        self._app.s_distance_refreshed.connect(self._window.widgets["information"].update_distance)
        self._app.s_posture_refreshed.connect(self._window.widgets["information"].update_posture)
        self._app.s_time_refreshed.connect(self._window.widgets["information"].update_time)

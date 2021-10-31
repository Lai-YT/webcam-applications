from PyQt5.QtCore import QObject, pyqtSignal

from lib.timer import Timer


class BlinkRatioCounter(QObject):
    """Counts times of blink per minute.

    Signals:
        s_ratio_refreshed
    """

    s_ratio_refreshed = pyqtSignal(float)

    def __init__(self) -> None:
        super().__init__()
        self._minute_timer = Timer()
        self._blink_count: int = 0

    def start(self) -> None:
        self._minute_timer.start()

    def stop(self) -> None:
        self._reset()

    def blink(self) -> None:
        self._blink_count += 1

    def check(self) -> bool:
        time: int = self._minute_timer.time()
        if time >= 60:
            # time might exceed 1 minute, normalize the ratio
            self.s_ratio_refreshed.emit(self._blink_count * 60 / time)
            self._reset()
            self._minute_timer.start()
            return True
        return False

    def _reset(self) -> None:
        self._minute_timer.reset()
        self._blink_count = 0

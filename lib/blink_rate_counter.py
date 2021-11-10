from PyQt5.QtCore import QObject, pyqtSignal

from lib.timer import Timer


class BlinkRateCounter(QObject):
    """Counts times of blink per minute.

    Signals:
        s_rate_refreshed
    """

    s_rate_refreshed = pyqtSignal(float)

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
            # If timer starts for over 1 minute, emits a signal of blinking rate,
            # restarts the timer, and return True to let main process display the
            # blinking rate on the frame.
            self.s_rate_refreshed.emit(self._blink_count * 60 / time)
            self._reset()
            self._minute_timer.start()
            return True
        return False

    def _reset(self) -> None:
        self._minute_timer.reset()
        self._blink_count = 0

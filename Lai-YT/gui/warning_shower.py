from PyQt5.QtCore import QObject, pyqtSlot

from gui.timer_widget import TimerWidget


class TimeShower(QObject):
    def __init__(self):
        super().__init__()

        self._widget = TimerWidget()
        self._widget.switch_time_mode("work")
        self._mode = "work"

    def current_mode(self):
        return self._mode

    @pyqtSlot(int)
    def update_time(self, time: int):
        """Displays current time on the clock in the form "min:sec".
        Note that the widget to show depends on the current mode.

        Arguments:
        time (int): The time in seconds to be displayed
        """
        t = f"{(time // 60):02d}:{(time % 60):02d}"

        if self._mode == "work":
            self._widget.work_time.display(t)
        elif self._mode == "break":
            self._widget.messages["Countdown"].setText(t)
        else:
            raise

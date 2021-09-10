from PyQt5.QtCore import QObject, pyqtSlot

from gui.timer_widget import TimerWidget


class TimeShower(QObject):
    """
    The layer between Widget and App.Knows the current state of time and updates
    ime to the corresponding widget.
    """
    def __init__(self):
        super().__init__()

        self._widget = TimerWidget()
        self._widget.switch_time_state("work")
        # Note that due to unknown reason, the whole app freezes if calling .show().
        self._widget.setVisible(True)

    def switch_time_state(self, state: str):
        """Switches the state of the TimerWidget."""
        self._widget.switch_time_state(state)

    @pyqtSlot(int)
    def update_time(self, time: int):
        """Displays time on the clock in the form "min:sec".
        Note that the widget to show depends on the current state of the TimerWidget.

        Arguments:
        time (int): The time in seconds to be displayed
        """
        t = f"{(time // 60):02d}:{(time % 60):02d}"

        if self._widget.current_state() == "work":
            self._widget.work_time.display(t)
        elif self._widget.current_state() == "break":
            self._widget.messages["Countdown"].setText(t)
        else:
            raise ValueError(f"{self._widget.current_state()} is not a valid state")

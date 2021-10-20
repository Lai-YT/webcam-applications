from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QApplication

from gui.popup_widget import TimerWidget


class TimeShower(QObject):
    """The layer between Widget and App.
    Knows the current state of time and updates time to the corresponding widget.
    """
    def __init__(self):
        super().__init__()

        self._widget = TimerWidget()
        self._widget.switch_time_state("work")

        self._move_timer_to_upper_right_corner()

    def show(self):
        self._widget.show()

    def hide(self):
        self._widget.hide()

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
        time_str = f"{(time // 60):02d}:{(time % 60):02d}"

        try:
            self._widget.clocks[self._widget.current_state()].display(time_str)
        except KeyError:
            raise ValueError(f"{self._widget.current_state()} is not a valid state")

    def close_timer_widget(self):
        """Closes the TimerWidget."""
        self._widget.close()

    def _move_timer_to_upper_right_corner(self):
        # A static method which returns the already existing instance; None if no.
        app = QApplication.instance()
        screen = app.primaryScreen()
        geometry = screen.availableGeometry()
        self._widget.move(geometry.width() - self._widget.width(), 50)

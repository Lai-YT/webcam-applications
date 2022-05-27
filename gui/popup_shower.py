from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QApplication

from gui.popup_widget import TimeState, TimerWidget


class TimeShower(QObject):
    """The layer between Widget and App.
    Knows the current state of time and updates time to the corresponding widget.
    """

    def __init__(self) -> None:
        super().__init__()

        self._widget = TimerWidget()
        self._widget.switch_time_state(TimeState.WORK)

        self._move_timer_to_upper_right_corner()

    def show(self) -> None:
        self._widget.show()

    def hide(self) -> None:
        self._widget.hide()

    def switch_time_state(self, state: TimeState) -> None:
        """Switches the state of the TimerWidget."""
        self._widget.switch_time_state(state)

    @pyqtSlot(int)
    def update_time(self, time: int) -> None:
        """Displays time on the clock in the form "min:sec".
        Note that the widget to show depends on the current state of the TimerWidget.

        Arguments:
            time: The time in seconds to be displayed.
        """
        time_str = f"{(time // 60):02d}:{(time % 60):02d}"
        self._widget.clocks[self._widget.current_state()].display(time_str)

    def close_timer_widget(self) -> None:
        """Closes the TimerWidget."""
        self._widget.close()

    def _move_timer_to_upper_right_corner(self) -> None:
        # A static method which returns the already existing instance; None if no.
        app = QApplication.instance()
        screen = app.primaryScreen()
        geometry = screen.availableGeometry()
        self._widget.move(geometry.width() - self._widget.width(), 50)

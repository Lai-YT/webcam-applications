from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QStackedLayout, QVBoxLayout, QWidget

import gui.img.icon
from gui.component import LCDClock, Label


class TimerWidget(QWidget):
    """TimerWidget contains different time states maintain by a QStackedLayout."""
    def __init__(self, parent=None):
        # Note that to make a Frameless Window draggable,
        # mouseMoveEvent and mousePressEvent need to be overriden to provide
        # such functionality.
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Set some basic properties.
        self.setWindowTitle("Timer")
        self.setWindowIcon(QIcon(":webcam.ico"))
        self.setFixedSize(250, 150)
        # A stacked layout is used to have multiple time states switching
        # on the same area.
        self._general_layout = QStackedLayout()
        self.setLayout(self._general_layout)
        # state (Widget) is the whole part to be switched.
        # clock (LCD Number) is the time displaying part to be controlled.
        self._states = {}
        self.clocks = {}
        self._create_work_state()
        self._create_break_state()
        # Work state is the initial state.
        self.switch_time_state("work")

    def current_state(self):
        """Returns the current state of the TimerWidget."""
        return self._current_state

    def switch_time_state(self, state: str):
        """
        Arguments:
            state ("work" | "break")
        """
        try:
            self._general_layout.setCurrentWidget(self._states[state])
        except KeyError:
            raise ValueError(f'Valid clocks are ("work" | "break") but "{state}" is passed') from None

        self._current_state = state

    # Override
    def mousePressEvent(self, event):
        """Records the position when mouse button is clicked inside the widget."""
        self._old_pos = event.globalPos()
        # Call base implementation to avoid any functionality lost.
        super().mousePressEvent(event)

    # Override
    def mouseMoveEvent(self, event):
        """If the move event is preceded by a press event, the widget moves with the mouse."""
        if event.globalPos() != self._old_pos:
            # Calculate the differences and move.
            delta = QPoint(event.globalPos() - self._old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            # Since move event is called every time the mouse moves
            # but only need to move when preceded by a press event,
            # store back the pos to make difference 0 if no preceding press.
            self._old_pos = event.globalPos()
        # Call base implementation to avoid any functionality lost.
        super().mouseMoveEvent(event)

    def _create_work_state(self):
        """The work state widget is a single Clock widget."""
        # lcd clock should be controlled under work state.
        self.clocks["work"] = LCDClock()
        self._general_layout.addWidget(self.clocks["work"])
        # state is the same as clock because the whole widget contains only the
        # clock.
        self._states["work"] = self.clocks["work"]

    def _create_break_state(self):
        """The break state widget is a single Clock widget."""
        # lcd clock should be controlled under break state.
        self.clocks["break"] = LCDClock(color="red")
        self._general_layout.addWidget(self.clocks["break"])
        # state is the same as clock because the whole widget contains only the
        # clock.
        self._states["break"] = self.clocks["break"]

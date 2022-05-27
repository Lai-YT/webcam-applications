from enum import Enum, auto
from typing import Dict

from PyQt5.QtCore import QEvent, QObject, QPoint, Qt
from PyQt5.QtGui import QIcon, QMouseEvent
from PyQt5.QtWidgets import (
    QStackedWidget,
    QVBoxLayout,
    QToolButton,
    QWhatsThis,
    QWidget,
)

from gui.component import LCDClock


class TimeState(Enum):
    WORK = auto()
    BREAK = auto()


class TimerWidget(QWidget):
    """
    This is a frameless (no title bar), stays-on-top widget with translucent background,
    it contains a whats-this button and a two-state clock.
    """

    def __init__(self, parent: QWidget = None) -> None:
        # Note that to make a Frameless Window draggable,
        # mouseMoveEvent and mousePressEvent need to be overriden to provide
        # such functionality.
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Set some basic properties.
        self.setFixedSize(250, 150)

        self._general_layout = QVBoxLayout()
        self.setLayout(self._general_layout)

        self._create_whats_this_button()
        self._create_clocks()
        # Work state is the initial state.
        self._current_state: TimeState
        self.switch_time_state(TimeState.WORK)

    def current_state(self) -> TimeState:
        """Returns the current state of the TimerWidget."""
        return self._current_state

    def switch_time_state(self, state: TimeState) -> None:
        self._clock_widget.setCurrentWidget(self.clocks[state])
        self._current_state = state

    # Override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # If is a event from QToolButton(whats-this button) and is a mouse press
        # event, record the position so a press-and-move on the button can move
        # the window just like anywhere else of the window.
        if isinstance(watched, QToolButton) and event.type() == QEvent.MouseButtonPress:
            self._old_pos = event.globalPos()
        # Since this reimplementation doesn't really filter the event, pass it
        # to the base implementation.
        return super().eventFilter(watched, event)

    # Override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Records the position when mouse button is clicked inside the widget."""
        self._old_pos = event.globalPos()
        # Call base implementation to avoid any functionality lost.
        super().mousePressEvent(event)

    # Override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """If the move event is preceded by a press event, the widget moves with the mouse."""
        if event.globalPos() != self._old_pos:
            # Calculate the differences and move.
            delta = QPoint(event.globalPos() - self._old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            # The window flies out of the screen if not storing the pos back.
            self._old_pos = event.globalPos()
        # Call base implementation to avoid any functionality lost.
        super().mouseMoveEvent(event)

    def _create_whats_this_button(self) -> None:
        self._whats_this_button = QToolButton()
        # To have the button icon-only.
        self._whats_this_button.setStyleSheet("border: none;")
        # Make this tool button a whats-this-button.
        whats_this_action = QWhatsThis.createAction(parent=self._whats_this_button)
        whats_this_action.setIcon(QIcon(":help-icon.svg"))
        # Embed html syntax to provide rich text.
        whats_this_action.setWhatsThis(
            """
            <p style="font-family: Arial; font-size: 14px;">
                The <span style="color: black; font-weight: bold;">black</span> clock is a normal timer, it shows how long the user has been focusing on the screen;<br>
                the <span style="color: red; font-weight: bold;">red</span> clock appears when the focusing time reaches the limit, it counts down the break time.
            </p>
            """
        )
        self._whats_this_button.setDefaultAction(whats_this_action)
        self._general_layout.addWidget(self._whats_this_button)
        # To make the whole window movable by press-and-move on the mouse, need
        # to install this customize event filter so the button is considered a
        # part of the window; otherwise an exception occurs when the fisrt press
        # is on the button not the clock.
        self._whats_this_button.installEventFilter(self)

    def _create_clocks(self) -> None:
        self._clock_widget = StackedClockWidget()
        self._general_layout.addWidget(self._clock_widget)
        # Forward the clocks of StackedClockWidget to provide simple access.
        self.clocks: Dict[TimeState, LCDClock] = self._clock_widget.clocks


class StackedClockWidget(QStackedWidget):
    """This widget contains a work clock and a break clock to be switched on the same area."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._create_clocks()

    def _create_clocks(self) -> None:
        self.clocks: Dict[TimeState, LCDClock] = {
            TimeState.WORK: LCDClock(),
            TimeState.BREAK: LCDClock(color="red"),
        }
        for clock in self.clocks.values():
            self.addWidget(clock)

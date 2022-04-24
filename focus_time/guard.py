from typing import Tuple

from playsound import playsound

from gui.popup_shower import TimeShower
from gui.popup_widget import TimeState
from sounds.sound_guard import SoundGuard
from util.path import to_abs_path
from util.time import Timer, min_to_sec


# FIXME: Negative time occurs under unknown condition
class TimeGuard(SoundGuard):
    """TimeGuard checks whether the time held by a Timer exceeds time limit
    and interacts with a TimeShower to show the corresponding TimerWidget.
    """
    def __init__(
            self,
            time_limit: int,
            break_time: int,
            warning_enabled: bool = True) -> None:
        """
        All arguments can be set later with their corresponding setters.

        Arguments:
            time_limit: Triggers a break if reached (minutes).
            break_time: How long the break should be (minutes).
            warning_enabled:
                Whether there's sound that plays when it's time to take a break
                and end a break. Enabled in default.
        """
        super().__init__(warning_enabled)

        self._time_limit = min_to_sec(time_limit)
        self._break_time = min_to_sec(break_time)

        self._f_break_started: bool = False
        self._end_break_sound: str = to_abs_path("sounds/break_over.wav")
        self._enter_break_sound: str = to_abs_path("sounds/break_start.wav")
        self._break_timer = Timer()
        self._time_shower = TimeShower()

    def set_time_limit(self, time_limit: int) -> None:
        """
        Arguments:
            time_limit: Triggers a break if reached (minutes).
        """
        self._time_limit = min_to_sec(time_limit)

    def set_break_time(self, break_time: int) -> None:
        """
        Arguments:
            break_time: How long the break should be (minutes).
        """
        self._break_time = min_to_sec(break_time)

    def break_time_if_too_long(self, timer: Timer) -> Tuple[int, TimeState]:
        """The timer widget switches to break mode if the time held by timer
        exceeds the time limit.

        Arguments:
            timer: Contains time record.

        Returns:
            A tuple about the time and state.
            Time of the timer if in work state, countdown time if in break state.
        """
        # Break time is over.
        if self._break_timer.time() > self._break_time:
            timer.reset()
            self._end_break()
            return 0, TimeState.WORK
        # not the time to take a break
        # NOTE: an extra flag check is to prevent state change during break
        # due to a time limit setting.
        if timer.time() < self._time_limit and not self._f_break_started:
            # The time of the normal timer is to be shown.
            self._time_shower.update_time(timer.time())
            return timer.time(), TimeState.WORK

        return self._take_break()

    def show(self) -> None:
        """Shows the TimerWidget."""
        self._time_shower.show()

    def hide(self) -> None:
        """Hides the TimerWidget."""
        self._time_shower.hide()

    def reset(self) -> None:
        """If the TimeGuard is now taking a break, this method ends the break
        and switches back to work state.
        """
        self._f_break_started = False
        self._time_shower.switch_time_state(TimeState.WORK)
        self._break_timer.reset()

    def close_timer_widget(self) -> None:
        self._time_shower.close_timer_widget()
        # If not reset, a break-time-close might keep the countdown to next start.
        # (no effect if every start is a fresh new guard)
        self.reset()

    def _take_break(self) -> Tuple[int, TimeState]:
        """Updates the time of the break timer to the timer widget.

        Returns:
            Countdown time and TimeState.BREAK.
        """
        # If is the very moment to enter the break.
        if not self._f_break_started:
            self._enter_break()
        countdown: int = self._break_time - self._break_timer.time()
        # The time (countdown) of the break timer is to be shown.
        self._time_shower.update_time(countdown)
        return countdown, TimeState.BREAK

    def _enter_break(self) -> None:
        """Sound warning is played if it's enabled.

        Call this method if is the very moment to enter the break.
        """
        self._time_shower.switch_time_state(TimeState.BREAK)
        self._f_break_started = True
        self._break_timer.start()
        if self._warning_enabled:
            # Note that using flag instead of checking time to avoid double playing
            # since the interval between time checkings is often less than 1 sec.
            playsound(self._enter_break_sound, block=False)

    def _end_break(self) -> None:
        """Sound warning is played if it's enabled.

        Call this method if is the very moment to end the break.
        """
        self.reset()
        if self._warning_enabled:
            playsound(self._end_break_sound, block=False)

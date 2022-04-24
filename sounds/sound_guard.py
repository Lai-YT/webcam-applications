from playsound import playsound

from util.time import Timer


class SoundGuard:
    """A guard that plays warning sound under certain condition.

    Only setter is implemented, all methods about sound playing needs to be
    customized.
    """
    def __init__(self, warning_enabled: bool) -> None:
        self._warning_enabled: bool = warning_enabled

    def set_warning_enabled(self, enabled: bool) -> None:
        """
        Arguments:
            enabled:
                Whether sound plays under certain condition.
        """
        self._warning_enabled = enabled


class SoundRepeatGuard(SoundGuard):
    """A SoundGuard that implements the repeated sound playing method."""
    def __init__(self, sound_file: str, interval: int, warning_enabled: bool) -> None:
        """
        Arguments:
            sound_file: The sound to play.
            interval:
                The time between start and start, which means if the interval is
                shorter than the sound, they would overlap.
            warning_enabled: Sound plays and repeats only if is enabled.
        """
        super().__init__(warning_enabled)
        self._sound_file: str = sound_file
        self._warning_repeat_timer = Timer()
        self._interval: int = interval
        # To avoid double play due to a near time check (less than 1 sec).
        self._f_played: bool = False

    def _repeat_sound_if(self, condition: bool) -> None:
        """Plays the sound repeatedly if the warning is enabled and condition is met."""
        if not (self._warning_enabled and cond):
            return

        # If this is a new start of a slumped posture interval,
        # play sound then start another interval.
        if not self._f_played:
            self._f_played = True
            self._warning_repeat_timer.start()
            playsound(self._sound_file, block=False)
        # Only after certain interval can the sound be repeated.
        elif self._warning_repeat_timer.time() > self._interval:
            # Reset the timer and flag, so can be caught as a new start of interval.
            self._f_played = False
            self._warning_repeat_timer.reset()

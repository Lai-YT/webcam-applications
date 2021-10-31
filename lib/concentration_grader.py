from PyQt5.QtCore import QObject, pyqtSignal


class ConcentrationGrader(QObject):

    s_grade_refreshed = pyqtSignal(float)

    def __init__(self, interval: int = None):
        """
        Arguments:
            interval:
            Sends grade by signal after interval times of increment.
            Not to send in default.
        """
        super().__init__()

        self._concentration: int = 0
        self._total: int = 0   # concentration + distraction
        self._interval = interval

    def increase_concentration(self) -> None:
        self._total += 1
        self._concentration += 1
        self._grade_if_interval_ends()

    def increase_distraction(self) -> None:
        # Increase of distraction is invloved by total.
        self._total += 1
        self._grade_if_interval_ends()

    def _grade_if_interval_ends(self) -> None:
        if self._interval is not None and self._total == self._interval:
            self.s_grade_refreshed.emit(self.get_grade())
            self.reset()

    def get_grade(self) -> float:
        """Returns the grade rounded to the 3rd decimal places.
        Grade is the (concentration increment / total increment).
        """
        # handle zero division
        if self._total == 0:
            return 1.0

        return round(self._concentration/self._total, 3)

    def reset(self) -> None:
        """Resets the records to start a new interval."""
        self._concentration = 0
        self._total = 0

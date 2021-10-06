import logging


logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %H:%M:%S",
                    filename="concentration_grade.log", filemode="w", level=logging.INFO)


class ConcentrationGrader:
    def __init__(self, interval=None):
        """
        Arguments:
            interval (int): Logs grade after interval times of increment. No logging in default.
        """
        self._distraction: int = 0
        self._total: int = 0   # concentration + distraction
        self._interval = interval

    def increase_concentration(self) -> None:
        self._total += 1
        if self._interval is not None and self._total == self._interval:
            self.log_grade()
            self.reset()

    def increase_distraction(self) -> None:
        self._distraction += 1
        self.increase_concentration()

    def get_grade(self) -> float:
        """Returns the grade rounded to the 3rd decimal places.
        Grade is the 1 - (distraction increment / total increment).
        """
        # handle zero division
        if self._total == 0:
            return 1.0

        return round(1 - self._distraction/self._total, 3)

    def reset(self):
        self._distraction = 0
        self._total = 0

    def log_grade(self):
        logging.info(f"{self.get_grade()}")

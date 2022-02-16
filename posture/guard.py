from typing import Optional, Tuple

import cv2
from PyQt5.QtCore import QObject, pyqtSignal
from nptyping import Float, Int, NDArray
from playsound import playsound

from concentration.grader import ConcentrationGrader
from posture.calculator import AngleCalculator, PosturePredictor
from posture.train import PostureLabel
from util.color import GREEN, RED
from util.cv_font import FONT_0
from util.image_type import ColorImage
from util.path import to_abs_path
from util.time import Timer


class PostureGuard(QObject):
    """PostureGuard checks whether the face obtained by landmarks implies a
    good or slump posture.

    Signals:
        s_posture_refreshed:
            Emits everytime a posture is checked (all attributes need to be set).
            It sents the PostureLabel and the detail string of the determination.
    """

    s_posture_refreshed = pyqtSignal(PostureLabel, str)

    def __init__(
            self,
            predictor: Optional[PosturePredictor] = None,
            calculator: Optional[AngleCalculator] = None,
            warn_angle: Optional[float] = None,
            warning_enabled: bool = True,
            grader: Optional[ConcentrationGrader] = None) -> None:
        """
        All arguments can be set later with their corresponding setters.

        Arguments:
            predictor:
                Used to predict the label of image when a clear face isn't found.
            calculator:
                Used to calculate the angle of face when a face is found.
            warn_angle:
                Face slope angle larger than this is considered to be a slump posture.
            warning_enabled:
                Whether there's sound that warns the user when a slump posture occurs.
            grader:
                Provide this optional argument if you're using the guard as
                one of the overall concentration grading components. The result
                will be send to the grader.
        """
        super().__init__()

        self._predictor: Optional[PosturePredictor] = predictor
        self._calculator: Optional[AngleCalculator] = calculator
        self._warn_angle: Optional[float] = warn_angle
        self._grader: Optional[ConcentrationGrader] = grader
        self._warning_enabled: bool = warning_enabled

        self._wavfile: str = to_abs_path("sounds/posture_slump.wav")
        self._warning_repeat_timer = Timer()
        # To avoid double play due to a near time check (less than 1 sec).
        self._f_played: bool = False

    def set_predictor(self, predictor: PosturePredictor) -> None:
        """
        Arguments:
            predictor: Used to predict the label of image when a clear face isn't found.
        """
        self._predictor = predictor

    def set_calculator(self, calculator: AngleCalculator) -> None:
        """
        Arguments:
            calculator: Used to calculate the angle of face when a face is found.
        """
        self._calculator = calculator

    def set_warn_angle(self, warn_angle: float) -> None:
        """
        Arguments:
            warn_angle: Face slope angle larger than this is considered to be a slump posture.
        """
        self._warn_angle = warn_angle

    def set_warning_enabled(self, enabled: bool) -> None:
        """
        Arguments:
            enabled: Whether there's sound that warns the user when a slump posture occurs.
        """
        self._warning_enabled = enabled

    def check_posture(
            self,
            canvas: ColorImage,
            frame: ColorImage,
            landmarks: NDArray[(68, 2), Int[32]]) -> None:
        """Sound plays if is a "slump" posture and warning is enabled.

        If the landmarks of face are clear, use AngleCalculator to calculate the
        slope precisely; otherwise use the model to predict the posture.

        Notice that this method does nothing if angle calculator or warn angle
        haven't been set yet.

        Arguments:
            canvas: The prediction will be texted on the canvas.
            frame: The image contains posture to be predicted.
            landmarks: (x, y) coordinates of the 68 face landmarks.

        Emits:
            s_posture_refreshed: Sends the posture label and result detail.

        Returns:
            The PostureLabel and the detail string of the determination.
            None if any of the necessary attributes aren't set.
        """
        if self._calculator is None or self._warn_angle is None:
            return

        # Get posture label...
        posture: PostureLabel
        detect: str
        if landmarks.any():
            posture, detail = self._do_posture_angle_check(canvas, landmarks)
        else:
            posture, detail = self._do_posture_model_predict(canvas, frame)
        self.s_posture_refreshed.emit(posture, detail)

        # sound warning logic
        if self._warning_enabled and posture is not PostureLabel.GOOD:
            # If this is a new start of a slumped posture interval,
            # play sound then start another interval.
            if not self._f_played:
                self._f_played = True
                self._warning_repeat_timer.start()
                playsound(self._wavfile, block=False)
            # Only after certain interval can the sound be repeated.
            # Note that the sound file is about 3 sec, take 5 sec as the delay.
            elif self._warning_repeat_timer.time() > 8:
                # Reset the timer and flag, so can be caught as a new start of interval.
                self._f_played = False
                self._warning_repeat_timer.reset()

        self._send_concentration_info(posture)

        text, color = ("Good", GREEN) if posture is PostureLabel.GOOD else ("Slump", RED)
        cv2.putText(canvas, text, (10, 70), FONT_0, 0.9, color, thickness=2)

    def _send_concentration_info(self, posture: PostureLabel) -> None:
        """Sends a concentration to the grader if the posture is good,
        a distraction otherwise.

        Does nothing if the grader isn't provided.

        Arguments:
            posture: The label of posture to send info about.
        """
        if self._grader is not None:
            if posture is PostureLabel.GOOD:
                self._grader.add_body_concentration()
            else:
                self._grader.add_body_distraction()

    def _do_posture_angle_check(
            self,
            canvas: ColorImage,
            landmarks: NDArray[(68, 2), Int[32]]) -> Tuple[PostureLabel, str]:
        """Puts posture and angle text on the canvas. "Good" in green if angle
        doesn't exceed the warn_angle, otherwise "Slump" in red.

        Arguments:
            canvas: The image to put text on.
            landmarks: (x, y) coordinates of the 68 face landmarks.

        Returns:
            The PostureLabel and the detail string of the determination.
        """
        if self._calculator is None:
            raise ValueError("please set a calculator before checking angles")

        angle: float = self._calculator.calculate(landmarks)
        detail: str = f"by angle: {round(angle, 1)} degrees"
        cv2.putText(canvas, detail, (15, 110), FONT_0, 0.7, (200, 200, 255), 2)

        if self._warn_angle is None:
            raise ValueError("please set the angle to warn before checking angles")
        posture: PostureLabel = PostureLabel.GOOD
        if abs(angle) >= self._warn_angle:
            posture = PostureLabel.SLUMP

        return posture, detail

    def _do_posture_model_predict(
            self,
            canvas: ColorImage,
            frame: ColorImage) -> Tuple[PostureLabel, str]:
        """Puts posture label text on the canvas.

        Arguments:
            canvas: The prediction will be texted on the canvas.
            frame: The image contains posture to be predicted.

        Returns:
            The PostureLabel and the detail string of the determination.
        """
        if self._predictor is None:
            raise ValueError("please set a predictor before checking postures")

        posture: PostureLabel
        conf: Float[32]
        posture, conf = self._predictor.predict(frame)

        detail: str = f"by model: {conf:.0%}"
        cv2.putText(canvas, detail, (15, 110), FONT_0, 0.7, (200, 200, 255), thickness=2)

        return posture, detail

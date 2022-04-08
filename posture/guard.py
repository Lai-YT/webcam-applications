# The 3-layer posture detection refers to
# https://github.com/EE-Ind-Stud-Group/posture-detection

import logging
from datetime import datetime
from typing import Optional, Tuple

import cv2
import mtcnn
from nptyping import Float, Int, NDArray
from playsound import playsound

from concentration.grader import ConcentrationGrader
from posture.calculator import (
    HogAngleCalculator, MtcnnAngleCalculator, PostureLabel, PosturePredictor
)
from util.image_type import ColorImage
from util.path import to_abs_path
from util.time import Timer


logging.basicConfig(filename=to_abs_path(f"./face-centroid-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"),
                    format="%(message)s", level=logging.INFO)

class PostureGuard:
    """PostureGuard checks whether the face obtained by landmarks implies a
    good or slump posture.
    """
    def __init__(
            self,
            predictor: PosturePredictor,
            warn_angle: float,
            warning_enabled: bool = True,
            grader: Optional[ConcentrationGrader] = None) -> None:
        """
        Arguments:
            predictor:
                Used to predict the label of image when a clear face isn't found.
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
        self._predictor: PosturePredictor = predictor
        self._hog_angle_calculator = HogAngleCalculator()
        self._mtcnn_angle_calculator = MtcnnAngleCalculator()
        self._mtcnn_detector = mtcnn.MTCNN()
        self._warn_angle: float = warn_angle
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
            frame: ColorImage,
            landmarks: NDArray[(68, 2), Int[32]]) -> Tuple[PostureLabel, str]:
        """Sound plays when is a "slump" posture if warning is enabled.

        Arguments:
            frame: The image contains posture to be predicted.
            landmarks: (x, y) coordinates of the 68 face landmarks.

        Returns:
            The PostureLabel and the detail string of the determination.
            None if any of the necessary attributes aren't set.
        """
        # The posture detection used is made up of 3 layer, where are HOG (Dlib),
        # MTCNN and self-trained model (TensorFlow).
        # HOG is accurate enough and has the fastest speed but needs front faces,
        # so it's used as the first layer; then when the angle is too large that
        # HOG fails, MTCNN takes over. It's robust but so slow that we can't have
        # it as the first layer; last, when the above 2 detections both fail on
        # face detection, we use our model.

        # Get posture label...
        angle: float
        posture: PostureLabel
        detail: str
        if landmarks.any():
            # layer 1: hog
            angle = self._hog_angle_calculator.calculate(landmarks)
            posture, detail = self._do_angle_check(angle)
            centroid = tuple((landmarks[30] + landmarks[33]) / 2)
            logging.info(f"hog {centroid}")
        else:
            # layer 2: mtcnn
            faces = self._mtcnn_detector.detect_faces(
                cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            )
            if faces:
                angle = self._mtcnn_angle_calculator.calculate(faces[0])
                posture, detail = self._do_angle_check(angle)
                centroid = faces[0]["keypoints"]["nose"]
                logging.info(f"mtcnn {centroid}")
            else:
                # layer 3: self-trained model
                posture, detail = self._do_model_predict(frame)
                # XXX: this is a hack to have all layers produce an angle
                angle = 5 if posture is PostureLabel.GOOD else 100

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

        self._send_concentration_info(angle)

        return posture, detail

    def _send_concentration_info(self, angle: float) -> None:
        """Sends a distraction to the grader if the absolute value of angle is
        too large, a concentration otherwise.

        Does nothing if the grader isn't provided.

        Arguments:
            angle: The angle to send info about.
        """
        TOO_LARGE = 9.2
        if self._grader is not None:
            if abs(angle) > TOO_LARGE:
                self._grader.add_body_distraction()
            else:
                self._grader.add_body_concentration()

    def _do_angle_check(self, angle: float) -> Tuple[PostureLabel, str]:
        """
        Arguments:
            angle: To be checked with the warn angle.

        Returns:
            The PostureLabel and the detail string of the determination.
        """
        posture: PostureLabel = PostureLabel.GOOD
        if abs(angle) >= self._warn_angle:
            posture = PostureLabel.SLUMP

        detail = f"by angle: {round(angle, 1)} degrees"

        return posture, detail

    def _do_model_predict(
            self,
            frame: ColorImage) -> Tuple[PostureLabel, str]:
        """
        Arguments:
            frame: The image contains posture to be predicted.

        Returns:
            The PostureLabel and the detail string of the determination.
        """
        posture: PostureLabel
        conf: Float[32]
        posture, conf = self._predictor.predict(frame)

        detail = f"by model: {conf:.0%}"

        return posture, detail

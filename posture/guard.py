from typing import Optional, Tuple

import cv2
import mtcnn
from nptyping import Int, NDArray

from concentration.grader import ConcentrationGrader
from posture.calculator import PostureLabel
from posture.layer import AngleLayer, HogLayer, MtcnnLayer
from sounds.sound_guard import SoundRepeatGuard
from util.image_type import ColorImage
from util.path import to_abs_path


class PostureGuard(SoundRepeatGuard):
    """PostureGuard checks whether the face obtained by landmarks implies a
    good or slump posture.
    """
    def __init__(
            self,
            warn_angle: float,
            warning_enabled: bool = True,
            grader: Optional[ConcentrationGrader] = None) -> None:
        """
        Arguments:
            warn_angle:
                Face slope angle larger than this is considered to be a slump posture.
            warning_enabled:
                Whether there's sound that warns the user when a slump posture occurs.
            grader:
                Provide this optional argument if you're using the guard as
                one of the overall concentration grading components. The result
                will be send to the grader.
        """
        super().__init__(
            sound_file=to_abs_path("sounds/posture_slump.wav"),
            interval=8,
            warning_enabled=warning_enabled
        )
        self._hog_layer = HogLayer(warn_angle)
        self._mtcnn_layer = MtcnnLayer(warn_angle)
        self._mtcnn_detector = mtcnn.MTCNN()
        self._grader: Optional[ConcentrationGrader] = grader

    def set_warn_angle(self, warn_angle: float) -> None:
        """
        Arguments:
            warn_angle: Face slope angle larger than this is considered to be a slump posture.
        """
        self._hog_layer.set_warn_angle(warn_angle)
        self._mtcnn_layer.set_warn_angle(warn_angle)

    def check_posture(
            self,
            frame: ColorImage,
            landmarks: NDArray[(68, 2), Int[32]]) -> Tuple[PostureLabel, str]:
        """Good or slump is determined by the angle of face; if there isn't a
        face, the posture is always slump.

        If warning is enabled, sound plays when is a slump posture.
        An exception is that a slump under no face will never trigger sound warning
        since it's not really because of a slump posture but the absence of user.

        Arguments:
            frame: The image contains posture to be predicted.
            landmarks: (x, y) coordinates of the 68 face landmarks.

        Returns:
            The PostureLabel and the detail string of the determination.
        """
        # The posture detection used is made up of 2 layers,
        # which are HOG (Dlib) and MTCNN.
        # HOG is accurate enough and has the fastest speed but needs front faces,
        # so it's used as the first layer; then when the angle is too large that
        # HOG fails, MTCNN takes over. It's robust but so slow that we can't have
        # it as the first layer; last, when the above 2 detections both fail on
        # face detection, we say that the user isn't concentrating since he/she
        # isn't even in front of the screen.

        layer: AngleLayer
        if landmarks.any():
            self._hog_layer.detect(landmarks)
            layer = self._hog_layer
        else:
            faces = self._mtcnn_detector.detect_faces(
                cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            )
            if faces:
                self._mtcnn_layer.detect(faces[0])
                layer = self._mtcnn_layer
            else:  # no face
                # a sufficienly large angle to be sent as distraction
                self._send_concentration_info(100)
                # No face won't trigger sound warning since it's usually because
                # of the user not in front of the screen, not really because of
                # a slump posture.
                return PostureLabel.SLUMP, "no face"

        if self._grader is not None:
            self._grader.add_face_center(layer.center)
            self._grader.add_face()

        self._repeat_sound_if(layer.posture is not PostureLabel.GOOD)
        self._send_concentration_info(layer.angle)

        return layer.posture, layer.detail

    def _send_concentration_info(self, angle: float) -> None:
        """Sends a distraction to the grader if the absolute value of angle is
        too large, a concentration otherwise.

        Does nothing if the grader isn't provided.

        Arguments:
            angle: The angle to send info about.
        """
        if self._grader is None:
            return

        # this specific large value is chosen under the experiment of 5,194
        # images labeled in good and 3,272 images labeled in slump;
        # has 95% of the goods within -9.2 ~ 9.2
        TOO_LARGE = 9.2
        if abs(angle) > TOO_LARGE:
            self._grader.add_body_distraction()
        else:
            self._grader.add_body_concentration()

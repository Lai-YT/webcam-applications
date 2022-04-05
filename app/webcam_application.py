import atexit
from configparser import ConfigParser
from copy import deepcopy
from operator import methodcaller
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import dlib
import numpy as np
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from imutils import face_utils
from nptyping import Int, NDArray
from tensorflow.keras import models

from app.app_type import ApplicationType
from brightness.calculator import BrightnessMode
from brightness.controller import BrightnessController
from concentration.fuzzy.classes import Interval
from concentration.grader import ConcentrationGrader
from distance.calculator import (
    DistanceCalculator, draw_landmarks_used_by_distance_calculator
)
from distance.guard import DistanceGuard, DistanceState
from focus_time.guard import TimeGuard
from gui.popup_widget import TimeState
from posture.calculator import (
    PostureLabel, PosturePredictor, draw_landmarks_used_by_angle_calculator
)
from posture.guard import PostureGuard
from util.color import GREEN, MAGENTA
from util.image_convert import ndarray_to_qimage
from util.image_type import ColorImage
from util.path import to_abs_path
from util.task_worker import TaskWorker
from util.time import Timer


class WebcamApplication(QObject):
    """
    The WebcamApplication provides 4 main applications:
        distance measurement,
        focus timing,
        posture detection,
        brightness optimization

    Signals:
        s_distance_refreshed:
            Emits everytime distance measurement has a new result.
            Sends the new distance.
        s_time_refreshed:
            Emits everytime the timer is updated.
            Sends the time and its state.
        s_posture_refreshed:
            Emits everytime posture detection has a new result.
            Sends the label of posture and few detection details.
        s_brightness_refreshed:
            Emits everytime the brightness of screen is updated.
            Sends the new brightness value.
        s_concent_interval_refreshed:
            Emits everytime a new grade is published.
            Sends the interval dataclass which contains the start time,
            end time and grade.
        s_frame_refreshed:
            Emits every time a new frame is captured.
            Sends the new frame.
        s_started:
            Emits after the WebcamApplication starts running.
        s_stopped:
            Emits after the WebcamApplication stops running.
    """

    SETTINGS_FILE = to_abs_path("./app/settings.ini")

    # Signals used to communicate with controller.
    s_frame_refreshed = pyqtSignal(QImage)
    s_distance_refreshed = pyqtSignal(float, DistanceState)
    s_time_refreshed = pyqtSignal(int, TimeState)
    s_posture_refreshed = pyqtSignal(PostureLabel, str)
    s_brightness_refreshed = pyqtSignal(int)
    s_concent_interval_refreshed = pyqtSignal(Interval)
    s_started = pyqtSignal()  # emits just before getting in to the while-loop of start()
    s_stopped = pyqtSignal()  # emits just before leaving start()

    def __init__(self) -> None:
        super().__init__()
        self._load_settings()
        atexit.register(self._store_settings)

        # Used to break the capturing loop inside start().
        # If the application is in progress, sets the ready
        # flag to False will stop it.
        self._f_ready: bool = False

        self._webcam = cv2.VideoCapture(0)
        self._create_face_detectors()
        self._create_concentration_grader()
        self._create_guards()
        self._create_brightness_controller()

    def _load_settings(self) -> None:
        self._settings = ConfigParser()
        self._settings.read(self.SETTINGS_FILE, encoding="utf-8")

    def get_settings(self) -> ConfigParser:
        """Returns a copy of the currents settings used by the applcations."""
        return deepcopy(self._settings)

    def _store_settings(self) -> None:
        with open(self.SETTINGS_FILE, "w", encoding="utf-8") as f:
            self._settings.write(f)

    def _create_face_detectors(self) -> None:
        """Creates face detector and shape predictor."""
        self._face: Optional[dlib.rectangle] = None
        self._landmarks: NDArray[(68, 2), Int[32]] = None
        self._face_detector: dlib.fhog_object_detector = dlib.get_frontal_face_detector()
        self._shape_predictor = dlib.shape_predictor(
            to_abs_path("dlib_model/shape_predictor_68_face_landmarks.dat")
        )

    def _create_brightness_controller(self) -> None:
        """Creates brightness calculator and initializes modes."""
        settings = self._settings[ApplicationType.BRIGHTNESS_OPTIMIZATION.name]

        self._brightness_optimize = settings.getboolean("ENABLED")
        self._brightness_controller = BrightnessController(
            settings.getint("BASE_VALUE"),
            BrightnessMode[settings["MODE"]],
        )

    def _create_concentration_grader(self) -> None:
        """Create ConcentrationGrader shared by guards."""
        self._concentration_grader = ConcentrationGrader()
        self._concentration_grader.s_concent_interval_refreshed.connect(
            self.s_concent_interval_refreshed
        )
        self._keep_grading_if_related_apps_enabled()

    def _create_guards(self) -> None:
        self._create_distance_guard()
        self._create_time_guard()
        self._create_posture_guard()

    def _create_distance_guard(self) -> None:
        self._ref_landmarks: NDArray[(68, 2), Int[32]]
        self._update_ref_landmarks()

        settings = self._settings[ApplicationType.DISTANCE_MEASUREMENT.name]

        self._distance_measure = settings.getboolean("ENABLED")
        self._distance_guard = DistanceGuard(
            DistanceCalculator(
                self._ref_landmarks,
                settings.getfloat("REFERENCE_DISTANCE")
            ),
            settings.getfloat("LIMIT"),
            settings.getboolean("WARNING"),
            self._concentration_grader
        )

    def _create_time_guard(self) -> None:
        settings = self._settings[ApplicationType.FOCUS_TIMING.name]

        self._focus_time = settings.getboolean("ENABLED")
        self._time_guard = TimeGuard(
            settings.getint("LIMIT"),
            settings.getint("BREAK_TIME"),
            settings.getboolean("WARNING")
        )
        self._timer = Timer()
        if self._focus_time:
            self._time_guard.show()
        self.s_stopped.connect(self._time_guard.close_timer_widget)

    def _create_posture_guard(self) -> None:
        settings = self._settings[ApplicationType.POSTURE_DETECTION.name]

        self._posture_detect = settings.getboolean("ENABLED")
        self._posture_guard = PostureGuard(
            PosturePredictor(
                models.load_model(to_abs_path("posture/models/self_trained_model"))
            ),
            settings.getfloat("ANGLE"),
            settings.getboolean("WARNING"),
            self._concentration_grader
        )

    def set_distance_measure(
            self, *,
            enabled: Optional[bool] = None,
            ref_img_path: Optional[str] = None,
            camera_dist: Optional[float] = None,
            warn_dist: Optional[float] = None,
            warning_enabled: Optional[bool] = None) -> None:
        settings = self._settings[ApplicationType.DISTANCE_MEASUREMENT.name]

        if camera_dist is not None or ref_img_path is not None:
            if camera_dist is not None:
                settings["REFERENCE_DISTANCE"] = str(camera_dist)
            if ref_img_path is not None:
                settings["REFERENCE_IMAGE_PATH"] = ref_img_path
                self._update_ref_landmarks()
            self._distance_guard.set_calculator(
                DistanceCalculator(
                    self._ref_landmarks,
                    settings.getfloat("REFERENCE_DISTANCE")
                )
            )
        if warn_dist is not None:
            settings["LIMIT"] = str(warn_dist)
            self._distance_guard.set_warn_dist(warn_dist)
        if warning_enabled is not None:
            settings["WARNING"] = str(warning_enabled)
            self._distance_guard.set_warning_enabled(warning_enabled)
        if enabled is not None:
            settings["ENABLED"] = str(enabled)
            self._distance_measure = enabled
            self._keep_grading_if_related_apps_enabled()

    def set_focus_time(
            self, *,
            enabled: Optional[bool] = None,
            time_limit: Optional[int] = None,
            break_time: Optional[int] = None,
            warning_enabled: Optional[bool] = None) -> None:
        settings = self._settings[ApplicationType.FOCUS_TIMING.name]

        if time_limit is not None:
            settings["LIMIT"] = str(time_limit)
            self._time_guard.set_time_limit(time_limit)
        if break_time is not None:
            settings["BREAK_TIME"] = str(break_time)
            self._time_guard.set_break_time(break_time)
        if warning_enabled is not None:
            settings["WARNING"] = str(warning_enabled)
            self._time_guard.set_warning_enabled(warning_enabled)
        if enabled is not None:
            settings["ENABLED"] = str(enabled)
            self._focus_time = enabled
            self._time_guard.reset()
            self._timer.reset()
            if enabled:
                self._time_guard.show()
            else:
                self._time_guard.hide()

    def set_posture_detect(
            self, *,
            enabled: Optional[bool] = None,
            warn_angle: Optional[float] = None,
            warning_enabled: Optional[bool] = None) -> None:
        settings = self._settings[ApplicationType.POSTURE_DETECTION.name]

        if warn_angle is not None:
            settings["LIMIT"] = str(warn_angle)
            self._posture_guard.set_warn_angle(warn_angle)
        if warning_enabled is not None:
            settings["WARNING"] = str(warning_enabled)
            self._posture_guard.set_warning_enabled(warning_enabled)
        if enabled is not None:
            settings["ENABLED"] = str(enabled)
            self._posture_detect = enabled
            self._keep_grading_if_related_apps_enabled()

    def set_brightness_optimization(
            self, *,
            enabled: Optional[bool] = None,
            slider_value: Optional[int] = None,
            mode: Optional[BrightnessMode] = None) -> None:
        settings = self._settings[ApplicationType.BRIGHTNESS_OPTIMIZATION.name]

        if slider_value is not None:
            settings["BASE_VALUE"] = str(slider_value)
            self._brightness_controller.update_base_value(slider_value)
        if mode is not None:
            settings["MODE"] = mode.name  # is enum
            self._brightness_controller.set_mode(mode)
        if enabled is not None:
            settings["ENABLED"] = str(enabled)
            self._brightness_optimize = enabled

    @pyqtSlot()
    @pyqtSlot(int)
    def start(self, refresh: int = 1) -> None:
        """Starts the applications that has been enabled.

        Arguments:
            refresh: Refresh speed in millisecond. 1ms in default.
        """
        # Set the flag to True so can start capturing.
        # Loop breaks if someone calls stop() and sets the flag to False.
        self._f_ready = True

        # focus time needs a timer to help.
        self._timer.reset()
        if self._focus_time:
            self._timer.start()

        self.s_started.emit()

        while self._f_ready:
            frame: ColorImage
            _, frame = self._webcam.read()
            # mirrors, so horizontally flip
            frame = cv2.flip(frame, flipCode=1)
            # separate detections and markings
            canvas: ColorImage = frame.copy()
            # Analyze the frame to update face landmarks.
            self._update_face_and_landmarks(canvas, frame)

            # Do applications!
            workers: List[TaskWorker] = []
            workers.append(TaskWorker(self._do_distance_measurement))
            workers.append(TaskWorker(self._do_posture_detection, canvas, frame))
            workers.append(TaskWorker(self._do_focus_timing))
            workers.append(TaskWorker(self._do_brightness_optimization, frame))
            for worker in workers:
                worker.start()

            # Do concentration gradings!
            self._concentration_grader.add_frame()
            if self._has_face():
                self._concentration_grader.add_face()
                self._concentration_grader.detect_blink(self._landmarks)

            self.s_frame_refreshed.emit(ndarray_to_qimage(canvas))
            cv2.waitKey(refresh)
        # Release resources.
        self._webcam.release()
        self.s_stopped.emit()

    @pyqtSlot()
    def stop(self) -> None:
        """Stops the execution loop by changing the flag."""
        self._f_ready = False

    def _do_distance_measurement(self) -> None:
        if self._distance_measure and self._has_face():
            dist_info = self._distance_guard.warn_if_too_close(self._landmarks)
            self.s_distance_refreshed.emit(*dist_info)

    def _do_posture_detection(self, canvas, frame) -> None:
        if self._posture_detect:
            draw_landmarks_used_by_angle_calculator(canvas, self._landmarks)
            post_info = self._posture_guard.check_posture(frame, self._landmarks)
            self.s_posture_refreshed.emit(*post_info)

    def _do_focus_timing(self) -> None:
        if self._focus_time:
            # If the landmarks doesn't contain a face, ths user is
            # considered not focusing on the screen, so the timer is paused.
            if not self._has_face():
                self._timer.pause()
            else:
                self._timer.start()
            time_info = self._time_guard.break_time_if_too_long(self._timer)
            self.s_time_refreshed.emit(*time_info)

    def _do_brightness_optimization(self, frame) -> None:
        if self._brightness_optimize:
            # Optimize brightness after passing required images.
            bright: int = self._brightness_controller.optimize_brightness(frame, self._face)
            self.s_brightness_refreshed.emit(bright)

    def _keep_grading_if_related_apps_enabled(self) -> None:
        # Need both distance measurement and posture detection to have
        # the concentration grader work.
        relate_enabled = all(
            [self._settings.getboolean(app_type.name, "ENABLED")
             for app_type in (ApplicationType.DISTANCE_MEASUREMENT,
                              ApplicationType.POSTURE_DETECTION)]
        )

        if relate_enabled:
            self._concentration_grader.start_grading()
        else:
            self._concentration_grader.stop_grading()

    def _update_face_and_landmarks(self, canvas: ColorImage, frame: ColorImage) -> None:
        """
        Arguments:
            canvas: The image to draw the landmarks on.
            frame: The image to get landmarks from.
        """
        # take the biggest face when a frame contains multiple faces
        self._face = get_biggest_face(self._face_detector(frame))
        if self._face is None:
            self._landmarks = np.zeros(shape=(68, 2), dtype=np.int32)
        else:
            self._landmarks = face_utils.shape_to_np(
                self._shape_predictor(frame, self._face)
            )
            mark_face(canvas, face_utils.rect_to_bb(self._face), self._landmarks)
            draw_landmarks_used_by_distance_calculator(canvas, self._landmarks)

    def _update_ref_landmarks(self) -> None:
        """Updates the reference landmarks with the reference image path."""
        ref_img: ColorImage = cv2.imread(
            self._settings[ApplicationType.DISTANCE_MEASUREMENT.name]["REFERENCE_IMAGE_PATH"]
        )
        faces: dlib.rectangles = self._face_detector(ref_img)
        if len(faces) != 1:
            # must have exactly one face in the reference image
            raise ValueError("should have exactly 1 face in the reference image")
        self._ref_landmarks = face_utils.shape_to_np(self._shape_predictor(ref_img, faces[0]))

    def _has_face(self) -> bool:
        """Returns whether the landmarks indicate a face."""
        return self._landmarks.any()


def get_biggest_face(faces: dlib.rectangles) -> Optional[dlib.rectangle]:
    """Returns the face with the biggest area.
    None if the input faces is empty.
    """
    # faces are compared through the area method
    return max(faces, default=None, key=methodcaller("area"))


def mark_face(
        canvas: ColorImage,
        face: Tuple[int, int, int, int],
        landmarks: NDArray[(68, 2), Int[32]]) -> None:
    """Modifies the canvas with face area framed up and landmarks dotted.

    Arguments:
        canvas: The image to mark face on.
        face: Upper-left x, y coordinates of face and it's width, height.
        landmarks: (x, y) coordinates of the 68 face landmarks.
    """
    fx, fy, fw, fh = face
    cv2.rectangle(canvas, (fx, fy), (fx+fw, fy+fh), MAGENTA, 1)
    for lx, ly in landmarks:
        cv2.circle(canvas, (lx, ly), 1, GREEN, -1)

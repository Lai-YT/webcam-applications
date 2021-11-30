import logging
import random
import time
from typing import List

import cv2
import dlib
import imutils
import numpy
from imutils import face_utils
from scipy import ndimage

from lib.angle_calculator import AngleCalculator
from lib.blink_detector import (
    AntiNoiseBlinkDetector,
    BlinkDetector,
    TailorMadeNormalEyeAspectRatioMaker,
    draw_landmarks_used_by_blink_detector,
)
from lib.concentration_grader import (
    ConcentrationGrader,
    FaceExistenceRateCounter,
)
from lib.blink_rate_counter import BlinkRateCounter


logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%I:%M:%S",
    filename="concent_interval.log",
    level=logging.DEBUG,
)

# after reading how many eye aspect ratios can a tailor-made EAR be reliable
SAMPLE_THRESHOLD: int = 500

# initialize dlib's face detector (HOG-based) and then create
# the facial landmark predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("lib/trained_models/shape_predictor_68_face_landmarks.dat")

def get_face_landmarks_from_frame(frame):
    """Gets the face landmarks if there contains exactly 1 face in the frame;
    otherwise the landmarks are filled with all 0.
    """
    # detect faces in the grayscale frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    # determine the facial landmarks for the face region, then
    # convert the facial landmark (x, y)-coordinates to a NumPy
    # array
    if len(faces) != 1:
        return numpy.zeros(shape=(68, 2), dtype=numpy.int32)
    shape = predictor(gray, faces[0])  # faces[0] is the only face
    return face_utils.shape_to_np(shape)

# adjust the normal BlinkDetector held by the AntiNoiseBlinkDetector
# ratio_adjuster = TailorMadeNormalEyeAspectRatioMaker(0.3, SAMPLE_THRESHOLD)

# to get better detection on a rotated face, use angle calculator with image rotate
# so everytime the blink detector deal with a straight face
angle_calculator = AngleCalculator()
blink_detector = AntiNoiseBlinkDetector(0.23, 2)
concentration_grader = ConcentrationGrader(0.23, 2, (15, 25))
manual_rate_counter = BlinkRateCounter()

blink_count: List[int] = [0]
def add_blink() -> None:
    blink_count[0] += 1
    manual_rate_counter.blink()
blink_detector.s_blinked.connect(add_blink)
manual_rate_counter.s_rate_refreshed.connect(lambda rate: logging.info(f"manual blink rate: {rate:.2f}/min\n"))

# start the video stream
cam = cv2.VideoCapture(0)
time.sleep(1.0)

manual_rate_counter.start()

# loop over frames from the video stream
while cam.isOpened():
    # grab the frame from the camera and resize it
    _, frame = cam.read()
    frame = imutils.resize(frame, width=600)

    concentration_grader.add_frame()

    # Simulate the body concentration grade randomly.
    # Have the expected value right at the edge (0.667),
    # so the body concentration may or may not pass the check.
    if random.choice((True, True, False)):
        concentration_grader.add_body_concentration()
    else:
        concentration_grader.add_body_distraction()

    landmarks = get_face_landmarks_from_frame(frame)

    # only process on frame which contains exactly 1 face
    if not landmarks.any():
        continue
    concentration_grader.add_face()

    manual_rate_counter.check()

    # Reset the EAR threshold if the tailor-made normal EAR is ready.
    # ratio_adjuster.read_sample(landmarks)
    # num_of_samples, normal_ratio = ratio_adjuster.get_normal_ratio()
    # if num_of_samples >= SAMPLE_THRESHOLD:
    #     blink_detector.ratio_threshold = normal_ratio * 0.8
    #     concentration_grader.set_ratio_threshold_of_blink_detector(normal_ratio * 0.8)
    # print(blink_detector.ratio_threshold)

    # sometime the landmarks of face don't fit well when the slope of face
    # exceeds 10 degress, so rotate the frame to keep one's face straight
    angle_calculator.calculate(landmarks)
    if angle_calculator.angle() is None:
        continue
    if abs(angle_calculator.angle()) > 10:  # type: ignore
        frame = ndimage.rotate(frame, angle_calculator.angle(), reshape=False)
        landmarks = get_face_landmarks_from_frame(frame)
        # might not able to detect a face after rotation
        if not landmarks.any():
            continue

    concentration_grader.detect_blink(landmarks)
    blink_detector.detect_blink(landmarks)
    ratio: float = BlinkDetector.get_average_eye_aspect_ratio(landmarks)

    frame = draw_landmarks_used_by_blink_detector(frame, landmarks)
    # display the total number of blinks on the frame along with
    # the computed eye aspect ratio for the frame
    cv2.putText(frame, f"Blinks: {blink_count[0]}", (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.putText(frame, f"EAR: {ratio:.2f}", (450, 30),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # show the frame
    cv2.imshow("Frame", frame)
    # delay 25 ms to prevent the frame count from fluctuating
    key = cv2.waitKey(25) & 0xFF

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break

# do a bit of clean-up
cv2.destroyAllWindows()
cam.release()
manual_rate_counter.stop()

# reference:
#   eye aspect ratio (2016):
#   https://www.pyimagesearch.com/2017/04/24/eye-blink-detection-opencv-python-dlib/
#
# blink rate (2017):
#   https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6118863/
#   The mean ± standard deviation blink rate was 19.74 ± 9.12/min at baseline.
#   A mean blink rate of up to 22 blinks/min has been reported under relaxed conditions.
#   The blink rate decreased significantly under both reading conditions
#   (to 11.35 ± 10.20 and 14.93 ± 10.90/min when reading from a book and a tablet, respectively).
#   There was no significant difference in the blink rate over 15 min during either type of reading.

import logging
import random
import time
from typing import List

import cv2
import dlib
import imutils
from imutils import face_utils

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

# adjust the normal BlinkDetector held by the AntiNoiseBlinkDetector
# ratio_adjuster = TailorMadeNormalEyeAspectRatioMaker(0.3, SAMPLE_THRESHOLD)

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
    # grab the frame from the camera, resize
    # it, and convert it to grayscale channels
    _, frame = cam.read()
    frame = imutils.resize(frame, width=600)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # detect faces in the grayscale frame
    faces = detector(gray)

    # Simulate the body concentration grade randomly.
    # Have the expected value right at the edge (0.667),
    # so the body concentration may or may not pass the check.
    if random.choice((True, True, False)):
        concentration_grader.add_body_concentration()
    else:
        concentration_grader.add_body_distraction()

    manual_rate_counter.check()

    concentration_grader.add_frame()
    # loop over the face detections
    for face in faces:
        concentration_grader.add_face()
        # determine the facial landmarks for the face region, then
        # convert the facial landmark (x, y)-coordinates to a NumPy
        # array
        shape = predictor(gray, face)
        landmarks = face_utils.shape_to_np(shape)

        # Reset the EAR threshold if the tailor-made normal EAR is ready.
        # ratio_adjuster.read_sample(landmarks)
        # num_of_samples, normal_ratio = ratio_adjuster.get_normal_ratio()
        # if num_of_samples >= SAMPLE_THRESHOLD:
        #     blink_detector.ratio_threshold = normal_ratio * 0.8
        #     concentration_grader.set_ratio_threshold_of_blink_detector(normal_ratio * 0.8)
        # print(blink_detector.ratio_threshold)

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

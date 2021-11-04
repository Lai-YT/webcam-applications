# reference:
# 	eye aspect ratio (2016):
# 	https://www.pyimagesearch.com/2017/04/24/eye-blink-detection-opencv-python-dlib/
#
#	blink rate (2017):
# 	https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6118863/
# 	The mean ± standard deviation blink rate was 19.74 ± 9.12/min at baseline.
# 	A mean blink rate of up to 22 blinks/min has been reported under relaxed conditions.
# 	The blink rate decreased significantly under both reading conditions
# 	(to 11.35 ± 10.20 and 14.93 ± 10.90/min when reading from a book and a tablet, respectively).
# 	There was no significant difference in the blink rate over 15 min during either type of reading.

import logging
import time
from typing import List, Optional

import cv2
import dlib
import imutils
from imutils import face_utils
from nptyping import Int, NDArray

from lib.blink_detector import (
	AntiNoiseBlinkDetector,
	BlinkDetector,
	GoodBlinkRateIntervalDetector,
	TailorMadeNormalEyeAspectRatioMaker,
	draw_landmarks_used_by_blink_detector,
)
from lib.blink_rate_counter import BlinkRateCounter


logging.basicConfig(
	format="%(asctime)s %(message)s",
	datefmt="%I:%M:%S",
	filename="blink_rate.log",
	level=logging.DEBUG,
)


# if the number of consecutive frames exceeds, the user may be
# fatigue and sleepy.
# CONSEC_FATIGUE_THRESH: int = 10
# after reading how many eye aspect ratios can a tailor-made EAR be reliable
SAMPLE_THRESHOLD: int = 500

# initialize dlib's face detector (HOG-based) and then create
# the facial landmark predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("lib/trained_models/shape_predictor_68_face_landmarks.dat")

# count and log the blink rate (blinks per minute)
rate_counter = BlinkRateCounter()
rate_counter.s_rate_refreshed.connect(lambda rate: logging.info(f"blink: {rate}/min"))

good_interval_detector = GoodBlinkRateIntervalDetector((15, 25))
good_interval_detector.s_good_interval_detected.connect(
		lambda t_s, t_e: logging.info(f"good interval: {t_s} ~ {t_e}, {t_e - t_s} sec"))

blink_count: int = 0  # increase when a new blink is detected
frame_count: int = 0  # increase every loop
face_count: int = 0  # increase every face

def count_blink() -> None:
	global blink_count
	blink_count += 1
	rate_counter.blink()
	good_interval_detector.add_blink()

# counts the total number of blinks
blink_detector = AntiNoiseBlinkDetector()
blink_detector.s_blinked.connect(count_blink)
# adjust the normal BlinkDetector held by the AntiNoiseBlinkDetector
ratio_adjuster = TailorMadeNormalEyeAspectRatioMaker(0.3, SAMPLE_THRESHOLD)

# start the video stream
cam = cv2.VideoCapture(0)
time.sleep(1.0)

rate_counter.start()

# loop over frames from the video stream
while cam.isOpened():
	# grab the frame from the camera, resize
	# it, and convert it to grayscale channels
	_, frame = cam.read()
	frame = imutils.resize(frame, width=600)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	# detect faces in the grayscale frame
	faces = detector(gray)

	frame_count += 1
	# loop over the face detections
	for face in faces:
		face_count += 1
		# determine the facial landmarks for the face region, then
		# convert the facial landmark (x, y)-coordinates to a NumPy
		# array
		shape = predictor(gray, face)
		landmarks = face_utils.shape_to_np(shape)

		ratio = BlinkDetector.get_average_eye_aspect_ratio(landmarks)
		ratio = round(ratio, 3)
		# Reset the EAR threshold if the tailor-made normal EAR is ready.
		ratio_adjuster.read_sample(landmarks)
		num_of_samples, normal_ratio = ratio_adjuster.get_normal_ratio()
		if num_of_samples >= SAMPLE_THRESHOLD:
			blink_detector.blink_detector.ratio_threshold = normal_ratio * 0.85

		blink_detector.detect_blink(landmarks)

		frame = draw_landmarks_used_by_blink_detector(frame, landmarks)
		# draw the total number of blinks on the frame along with
		# the computed eye aspect ratio for the frame
		cv2.putText(frame, f"Blinks: {blink_count}", (10, 30),
			cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
		cv2.putText(frame, f"EAR: {ratio:.2f}", (450, 30),
			cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

	details: List[str] = [f"ratio threshold: {round(blink_detector.blink_detector.ratio_threshold, 2)}"]
	if rate_counter.check():
		details.append(f"face: {face_count}/min")
		details.append(f"frame: {frame_count}/min")
		# face equals frame means the face sticks to the screen
		# so there's always a face with a frame.
		if face_count < frame_count * 0.7:
			details.append(f"low face existence, not reliable")
		logging.info(", ".join(details) + "\n")
		# resets the counts for a new interval
		face_count = 0
		frame_count = 0

	# show the frame
	cv2.imshow("Frame", frame)
	# delay 25 to prevent the frame count from fluctuating
	key = cv2.waitKey(25) & 0xFF

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break

# do a bit of clean-up
cv2.destroyAllWindows()
cam.release()
rate_counter.stop()

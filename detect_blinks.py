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

import cv2
import dlib
import imutils
from imutils import face_utils

from lib.blink_detector import (
	BlinkDetector,
	TailorMadeNormalEyeAspectRatioMaker,
	draw_landmarks_used_by_blink_detector,
)
from lib.blink_rate_counter import BlinkRateCounter


# define two constants, one for the eye aspect ratio to indicate
# blink and then a second constant for the number of consecutive
# frames the eye must be below the threshold
EYE_AR_THRESH: float = 0.24
EYE_AR_CONSEC_FRAMES: int = 3
# if the number of consecutive frames exceeds, the user may be
# fatigue and sleepy.
CONSEC_FATIGUE_THRESH: int = 10
# after reading how many eye aspect ratios can a tailor-made EAR be reliable
# SAMPLE_THRESHOLD: int = 500

# initialize the frame counts and the total number of blinks
count: int = 0
total: int = 0

# initialize dlib's face detector (HOG-based) and then create
# the facial landmark predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("lib/trained_models/shape_predictor_68_face_landmarks.dat")

blink_detector = BlinkDetector(EYE_AR_THRESH)
# ratio_adjuster = TailorMadeNormalEyeAspectRatioMaker(0.28, SAMPLE_THRESHOLD)
rate_counter = BlinkRateCounter()

frame_count: int = 0  # increase every loop
face_count: int = 0  # increase every face

# start the video stream
cam = cv2.VideoCapture(0)
time.sleep(1.0)

logging.basicConfig(
	format="%(asctime)s %(message)s",
	datefmt="%I:%M:%S",
	filename="blink_rate.log",
	# filemode="w+",
	level=logging.DEBUG,
)

rate_counter.s_rate_refreshed.connect(lambda rate: logging.info(f"blink: {rate}/min"))
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
		# determine the facial landmarks for the face region, then
		# convert the facial landmark (x, y)-coordinates to a NumPy
		# array
		shape = predictor(gray, face)
		landmarks = face_utils.shape_to_np(shape)

		ratio = BlinkDetector.get_average_eye_aspect_ratio(landmarks)
		ratio = round(ratio, 3)
		# Reset the EAR threshold if the tailor-made normal EAR is ready.
		# ratio_adjuster.read_sample(landmarks)
		# num_of_samples, normal_ratio = ratio_adjuster.get_normal_ratio()
		# if num_of_samples >= SAMPLE_THRESHOLD:
		# 	blink_detector.set_ratio_threshold(normal_ratio * 0.85)
		blinked = blink_detector.detect_blink(landmarks)

		# check to see if the eye aspect ratio is below the blink
		# threshold, and if so, increment the blink frame count
		if blinked:
			count += 1
		# otherwise, the eye aspect ratio is not below the blink threshold
		else:
			# if the eyes were closed for a sufficient number of
			# then increment the total number of blinks
			if count >= EYE_AR_CONSEC_FRAMES:
				total += 1
				rate_counter.blink()

			# reset the eye frame count
			count = 0

		face_count += 1

		frame = draw_landmarks_used_by_blink_detector(frame, landmarks)

		# draw the total number of blinks on the frame along with
		# the computed eye aspect ratio for the frame
		cv2.putText(frame, f"Blinks: {total}", (10, 30),
			cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
		cv2.putText(frame, f"EAR: {ratio:.2f}", (450, 30),
			cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

	if rate_counter.check():
		# face equals frame means the face sticks to the screen
		# so there's always a face with a frame.
		logging.info(f"face: {face_count}/min")
		logging.info(f"frame: {frame_count}/min\n")
		face_count = 0
		frame_count = 0

	# show the frame
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break

# do a bit of cleanup
cv2.destroyAllWindows()
cam.release()
rate_counter.stop()

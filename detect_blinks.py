# reference:
# https://www.pyimagesearch.com/2017/04/24/eye-blink-detection-opencv-python-dlib/

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


# define two constants, one for the eye aspect ratio to indicate
# blink and then a second constant for the number of consecutive
# frames the eye must be below the threshold
EYE_AR_THRESH = 0.24
EYE_AR_CONSEC_FRAMES = 3
# if the number of consecutive frames exceeds, the user may be
# fatigue and sleepy.
CONSEC_FATIGUE_THRESH = 10
# after reading how many eye aspect ratios can a tailor-made EAR be reliable
SAMPLE_THRESHOLD = 500

# initialize the frame counters and the total number of blinks
counter = 0
total = 0

# initialize dlib's face detector (HOG-based) and then create
# the facial landmark predictor
print("[INFO] loading facial landmark predictor...")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("lib/trained_models/shape_predictor_68_face_landmarks.dat")

print("[INFO] preparing blink detector...")
blink_detector = BlinkDetector(EYE_AR_THRESH)
ratio_adjuster = TailorMadeNormalEyeAspectRatioMaker(0.28, SAMPLE_THRESHOLD)

# start the video stream
print("[INFO] starting video stream...")
cam = cv2.VideoCapture(0)
time.sleep(1.0)

logging.basicConfig(
	format="%(message)s",
	filename="eye_aspect_ratio.log",
	filemode="w+",
	level=logging.DEBUG,
)

# loop over frames from the video stream
while cam.isOpened():
	# grab the frame from the camera, resize
	# it, and convert it to grayscale channels
	_, frame = cam.read()
	frame = imutils.resize(frame, width=600)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	# detect faces in the grayscale frame
	faces = detector(gray)

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
		ratio_adjuster.read_sample(landmarks)
		num_of_samples, normal_ratio = ratio_adjuster.get_normal_ratio()
		if num_of_samples >= SAMPLE_THRESHOLD:
			blink_detector.set_ratio_threshold(normal_ratio * 0.85)
		blinked = blink_detector.detect_blink(landmarks)

		# check to see if the eye aspect ratio is below the blink
		# threshold, and if so, increment the blink frame counter
		if blinked:
			counter += 1

			# the user has its eyes closed over a certain time threshold
			if counter >= CONSEC_FATIGUE_THRESH:
				logging.info(f"{ratio} (sleepy)")
			else:
				logging.info(f"{ratio} (blink)")

		# otherwise, the eye aspect ratio is not below the blink threshold
		else:
			logging.info(f"{ratio}")

			# if the eyes were closed for a sufficient number of
			# then increment the total number of blinks
			if counter >= EYE_AR_CONSEC_FRAMES:
				total += 1

			# reset the eye frame counter
			counter = 0

		frame = draw_landmarks_used_by_blink_detector(frame, landmarks)

		# draw the total number of blinks on the frame along with
		# the computed eye aspect ratio for the frame
		cv2.putText(frame, f"Blinks: {total}", (10, 30),
			cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
		cv2.putText(frame, f"EAR: {ratio:.2f}", (450, 30),
			cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

	# show the frame
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break

# do a bit of cleanup
cv2.destroyAllWindows()
cam.release()

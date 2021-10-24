# reference:
# https://www.pyimagesearch.com/2017/04/24/eye-blink-detection-opencv-python-dlib/

import cv2
import dlib
import imutils
import numpy as np
import time
from imutils import face_utils
from scipy.spatial import distance as dist


def eye_aspect_ratio(eye):
	# compute the euclidean distances between the two sets of
	# vertical eye landmarks (x, y)-coordinates
	A = dist.euclidean(eye[1], eye[5])
	B = dist.euclidean(eye[2], eye[4])

	# compute the euclidean distance between the horizontal
	# eye landmark (x, y)-coordinates
	C = dist.euclidean(eye[0], eye[3])

	# compute the eye aspect ratio
	ear = (A + B) / (2.0 * C)

	# return the eye aspect ratio
	return ear


# define two constants, one for the eye aspect ratio to indicate
# blink and then a second constant for the number of consecutive
# frames the eye must be below the threshold
EYE_AR_THRESH = 0.25
EYE_AR_CONSEC_FRAMES = 3

# initialize the frame counters and the total number of blinks
COUNTER = 0
TOTAL = 0

# initialize dlib's face detector (HOG-based) and then create
# the facial landmark predictor
print("[INFO] loading facial landmark predictor...")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("lib/trained_models/shape_predictor_68_face_landmarks.dat")

# grab the indexes of the facial landmarks for the left and
# right eye, respectively
(l_start, l_end) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(r_start, r_end) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

# start the video stream
print("[INFO] starting video stream...")
cam = cv2.VideoCapture(0)
time.sleep(1.0)


cam = cv2.VideoCapture(0)
# ear logging file
with open("eye_aspect_ratio.log", "w+") as f:
	# loop over frames from the video stream
	while cam.isOpened():

		# grab the frame from the camera, resize
		# it, and convert it to grayscale channels
		_, frame = cam.read()
		frame = imutils.resize(frame, width=450)
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		# detect faces in the grayscale frame
		rects = detector(gray, 0)

		# loop over the face detections
		for rect in rects:
			# determine the facial landmarks for the face region, then
			# convert the facial landmark (x, y)-coordinates to a NumPy
			# array
			shape = predictor(gray, rect)
			shape = face_utils.shape_to_np(shape)

			# extract the left and right eye coordinates, then use the
			# coordinates to compute the eye aspect ratio for both eyes
			left_eye = shape[l_start:l_end]
			right_eye = shape[r_start:r_end]
			left_ear = eye_aspect_ratio(left_eye)
			right_ear = eye_aspect_ratio(right_eye)

			# average the eye aspect ratio together for both eyes
			ear = (left_ear + right_ear) / 2.0

			# compute the convex hull for the left and right eye, then
			# visualize each of the eyes
			for eye in (left_eye, right_eye):
				hull = cv2.convexHull(eye)
				cv2.drawContours(frame, [hull], -1, (0, 255, 0), 1)

			# check to see if the eye aspect ratio is below the blink
			# threshold, and if so, increment the blink frame counter
			if ear < EYE_AR_THRESH:
				f.write(f"{ear} --\n")

				COUNTER += 1

			# otherwise, the eye aspect ratio is not below the blink
			# threshold
			else:
				f.write(f"{ear}\n")

				# if the eyes were closed for a sufficient number of
				# then increment the total number of blinks
				if COUNTER >= EYE_AR_CONSEC_FRAMES:
					TOTAL += 1

				# reset the eye frame counter
				COUNTER = 0

			# draw the total number of blinks on the frame along with
			# the computed eye aspect ratio for the frame
			cv2.putText(frame, f"Blinks: {TOTAL}", (10, 30),
				cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
			cv2.putText(frame, f"EAR: {ear:.2f}", (300, 30),
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

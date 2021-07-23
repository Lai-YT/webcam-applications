import cv2
import numpy as np
import tkinter as tk
import os
from pathlib import Path
from playsound import playsound
from sklearn.utils import class_weight
from tensorflow.keras import layers, models
from typing import Dict, List, Tuple

from .color import *
from .cv_font import *
from .face_distance_detector import FaceDistanceDetector
from .gaze_tracking import GazeTracking
from .path import to_abs_path
from .timer import Timer

# type hints
Image = np.ndarray

# window position config
root = tk.Tk()
screen_width:  int = root.winfo_screenwidth()
screen_height: int = root.winfo_screenheight()
screen_center: Tuple[int, int] = (
int(screen_width/2 - 245.5), int(screen_height/2 - 80.5))

# for eye focus timing
timer_width:  int = 192
timer_height: int = 85
timer_bg: Image = cv2.imread(to_abs_path("../img/timer_bg.jpg"))
timer_bg = cv2.resize(timer_bg, (timer_width, timer_height))
timer_window_name: str = "timer"
timer_window_pos: Tuple[int, int] = (screen_width - timer_width, 0)  # upper right

# break countdown
break_width:  int = 580
break_height: int = 315
break_bg: Image = cv2.imread(to_abs_path("../img/break_bg.jpg"))
break_bg = cv2.resize(break_bg, (break_width, break_height))
break_window_name: str = "break time"

# for distance measurement
message_width:  int = 490
message_height: int = 160
warning_message: Image = cv2.imread(to_abs_path("../img/warning.jpg"))
warning_message = cv2.resize(warning_message, (message_width, message_height))
warning_window_name: str = "warning"

# for posture watching
training_dir: str = to_abs_path("train")
model_path: str = to_abs_path("trained_models/posture_model.h5")
mp3file: str = to_abs_path("sounds/what.mp3")
image_dimensions: Tuple[int, int] = (224, 224)
epochs: int = 10
keyboard_spacebar: int = 32


def update_time(timer: Timer, face_detector: FaceDistanceDetector, gaze: GazeTracking) -> None:
    """Update time in the timer and show a window at the upper right corner of the screen.
    The timer wil keep timing if there's a face or pair of eyes, otherwise stops.

    Arguments:
        timer (Timer): Contains time to be updated
        face_detector (FaceDistanceDetector): Tells whether there's a face or not
        gaze (GazeTracking): Tells whether there's a pair of eyes or not
    """
    if not face_detector.has_face and not gaze.pupils_located:
        timer.pause()
    else:
        timer.start()
    timer_window: Image = timer_bg.copy()
    time: int = timer.time()  # sec
    time_duration: str = f"{(time // 60):02d}:{(time % 60):02d}"
    cv2.putText(timer_window, time_duration, (2, 70), FONT_3, 2, WHITE, 2)

    cv2.namedWindow(timer_window_name)
    cv2.moveWindow(timer_window_name, *timer_window_pos)
    cv2.imshow(timer_window_name, timer_window)


def break_time_if_too_long(timer: Timer, time_limit: int, break_time: int, camera: cv2.VideoCapture) -> None:
    """If the time record in the Timer object exceeds time limit, a break time countdown window shows in the center of screen.
    Camera turned off and all detections stop during the break. Also the Timer resets after it.

    Arguments:
        timer (Timer): Contains time record
        time_limit (int): Triggers a break if reached (minutes)
        break_time (int): How long the break should be (minutes)
        camera (cv2.VideoCapture): Turns off during break time, reopens after the break
    """
    time_limit *= 60 # minute to second
    # not the time to take a break
    if timer.time() < time_limit:
        return
    # stops camera and all detections
    camera.release()
    timer.reset()
    cv2.destroyAllWindows()
    # break time timer
    break_timer = Timer()
    break_timer.start()
    bt = break_time # break time that will display on the window
    break_time *= 60  # minute to second
    # break time countdown window
    cv2.namedWindow(break_window_name)
    cv2.moveWindow(break_window_name, *screen_center)
    while break_timer.time() < break_time:
        break_time_window: Image = break_bg.copy()
        # in sec
        countdown: int = break_time - break_timer.time()
        time_left: str = f"{(countdown // 60):02d}:{(countdown % 60):02d}"
        cv2.putText(break_time_window, str(bt), (100, 175), FONT_3, 1.5, BLACK, 2)
        cv2.putText(break_time_window, time_left, (165, 287), FONT_3, 0.9, BLACK, 1)
        cv2.imshow(break_window_name, break_time_window)
        cv2.waitKey(200)  # wait since only have to update once per second
    # break time over
    cv2.destroyWindow(break_window_name)
    camera.open(0)


def warn_if_too_close(face_distance_detector: FaceDistanceDetector, warn_dist: float) -> None:
    """Warning message shows in the center of screen when the distance measured by FaceDistanceDetector is less than warn dist.

    Arguments:
        face_distance_detector (FaceDistanceDetector)
        warn_dist (float)
    """
    text: str = ""
    if face_distance_detector.has_face:
        distance = face_distance_detector.distance()
        text = str(int(distance))
        if distance < warn_dist:
            cv2.namedWindow(warning_window_name)
            cv2.moveWindow(warning_window_name, *screen_center)
            cv2.imshow(warning_window_name, warning_message)
        elif cv2.getWindowProperty(warning_window_name, cv2.WND_PROP_VISIBLE):
            cv2.destroyWindow(warning_window_name)


def load_posture_model():
    """Returns the model trained by do_training()"""
    return models.load_model(model_path)


def warn_if_slumped(frame: Image, mymodel) -> None:
    """mp3 will be played when posture slumpled.

    Arguments:
        frame (numpy.ndarray): Contains posture to be watched
        mymodel (tensorflow.keras.Model): Predicts the label of frame
    """
    im: Image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    im = cv2.resize(im, image_dimensions)
    im = im / 255  # Normalize the image
    im = im.reshape(1, *image_dimensions, 1)

    predictions: np.ndarray = mymodel.predict(im)
    class_pred: np.int64 = np.argmax(predictions)
    conf: np.float32 = predictions[0][class_pred]

    # slumped
    if class_pred == 1:
        playsound(mp3file)


def capture_action(action_n: int, action_label: str) -> None:
    """Capture an image per second and put them under training_dir with name action_{action_n:02}.

    Arguments:
        action_n (str): Folder name of the images
        action_label (str): Label of the images
    """
    img_count: int = 0
    output_folder: str = f'{training_dir}/action_{action_n:02}'
    print(f'Capturing samples for {action_n} into folder {output_folder}...')
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    videocapture = cv2.VideoCapture(0)

    while videocapture.isOpened():
        _, frame = videocapture.read()
        filename: str = f'{output_folder}/{img_count:08}.jpg'
        cv2.imwrite(filename, frame)
        img_count += 1
        key: int = cv2.waitKey(100)
        cv2.imshow('sample capturing...', frame)

        if key == keyboard_spacebar:
            break
    else:
        raise IOError('Cannot open webcam')

    videocapture.release()
    cv2.destroyAllWindows()


def train() -> None:
    """The images captured by do_capture_action() will be used to train a model."""
    train_images:  List[Image] = []
    train_labels:  List[int] = []
    class_folders: List[str] = os.listdir(training_dir)

    class_label_indexer: int = 0
    for c in class_folders:
        print(f'Training with class {c}')
        for f in os.listdir(f'{training_dir}/{c}'):
            im: Image = cv2.imread(f'{training_dir}/{c}/{f}', cv2.IMREAD_GRAYSCALE)
            im = cv2.resize(im, image_dimensions)
            train_images.append(im)
            train_labels.append(class_label_indexer)
        class_label_indexer += 1

    train_images: np.ndarray = np.array(train_images)
    train_labels: np.ndarray = np.array(train_labels)

    indices: np.ndarray = np.arange(train_labels.shape[0])
    np.random.shuffle(indices)
    images: np.ndarray = train_images[indices]
    labels: np.ndarray = train_labels[indices]
    train_images = np.array(train_images)
    train_images = train_images / 255  # Normalize image
    train_images = train_images.reshape(len(train_images), *image_dimensions, 1)

    class_weights: np.ndarray = class_weight.compute_sample_weight('balanced', train_labels)
    weights: Dict[int, float] = {i : weight for i, weight in enumerate(class_weights)}
    model = models.Sequential()
    model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=(*image_dimensions, 1)))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(64, (3, 3), activation='relu'))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(64, (3, 3), activation='relu'))
    model.add(layers.Flatten())
    model.add(layers.Dense(64, activation='relu'))
    model.add(layers.Dense(len(class_folders), activation='softmax'))
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy',  metrics=['accuracy'])
    model.fit(train_images, train_labels, epochs=epochs, class_weight=weights)
    model.save(model_path)

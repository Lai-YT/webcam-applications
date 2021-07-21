import cv2
import numpy as np
import os
from pathlib import Path
from playsound import playsound
from sklearn.utils import class_weight
from tensorflow.keras import layers, models
from typing import Dict, List, Tuple

from .application import *
from .color import *
from .cv_font import *
from .draw import *
from .face_distance_detector import FaceDistanceDetector
from .gaze_tracking import GazeTracking
from .timer import Timer

# Config settings
training_dir: str = "train"
model_path:   str = "trained_models/posture_model.h5"
mp3file:      str = "sounds/what.mp3"
image_dimensions: Tuple[int, int] = (224, 224)
epochs: int = 10
keyboard_spacebar: int = 32

# type hints
Image = np.ndarray


def do_distance_measurement(frame: Image, distance_detector: FaceDistanceDetector, *, face_only: bool = False) -> Tuple[Image, FaceDistanceDetector]:
    """
    Estimates the distance in the frame by FaceDistanceDetector.
    Returns the frame with distance text and the FaceDistanceDetector that contains data of frame.

    Arguments:
        face_only (bool): No distance text on frame if True
    """
    frame = frame.copy()
    distance_detector.estimate(frame)
    frame = distance_detector.annotated_frame()
    if not face_only:
        text: str = ""
        if distance_detector.has_face:
            distance = distance_detector.distance()
            text = "dist. " + str(int(distance))
        else:
            text = "No face detected."
        cv2.putText(frame, text, (60, 30), FONT_3, 0.9, MAGENTA, 1)

    return frame, distance_detector


def do_gaze_tracking(frame: Image, gaze: GazeTracking) -> Tuple[Image, GazeTracking]:
    frame = frame.copy()
    # We send this frame to GazeTracking to analyze it
    gaze.refresh(frame)
    frame = gaze.annotated_frame()
    return frame, gaze


def do_focus_time_record(frame: Image, timer: Timer, distance_detector: FaceDistanceDetector, gaze: GazeTracking) -> Tuple[Image, Timer]:
    frame = frame.copy()
    if not distance_detector.has_face and not gaze.pupils_located:
        timer.pause()
        cv2.putText(frame, "timer paused", (432, 40), FONT_3, 0.6, RED, 1)
    else:
        timer.start()
    time_duration: str = f"t. {(timer.time() // 60):02d}:{(timer.time() % 60):02d}"
    cv2.putText(frame, time_duration, (500, 20), FONT_3, 0.8, BLUE, 1)

    return frame, timer


def load_posture_model():
    return models.load_model(model_path)


def do_posture_watch(frame: Image, mymodel, soundson: bool = False) -> Image:
    """Returns the frame with posture label text.
    mymodel is used to predict the label of frame.
    If soundson is True, sound will be played when posture slumpled.
    """
    im_color: Image = frame.copy()
    im: Image = cv2.cvtColor(im_color, cv2.COLOR_BGR2GRAY)

    im = cv2.resize(im, image_dimensions)
    im = im / 255  # Normalize the image
    im = im.reshape(1, *image_dimensions, 1)

    predictions: np.ndarray = mymodel.predict(im)
    class_pred: np.int64 = np.argmax(predictions)
    conf: np.float32 = predictions[0][class_pred]

    im_color = cv2.resize(im_color, (640, 480), interpolation=cv2.INTER_AREA)

    if class_pred == 1:
        # Slumped
        im_color = cv2.putText(im_color, 'Slumped', (10, 70), FONT_0, 1, RED, thickness=3)
        if soundson:
            playsound(mp3file)
    else:
        im_color = cv2.putText(im_color, 'Good', (10, 70), FONT_0, 1, GREEN, thickness=2)

    msg: str = f'Confidence {round(int(conf*100))}%'
    im_color = cv2.putText(im_color, msg, (15, 110), FONT_0, 0.6, (200, 200, 255), thickness=2)
    return im_color


def do_capture_action(action_n: int, action_label: str) -> None:
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
        key: int = cv2.waitKey(1000)
        cv2.imshow('sample capturing...', frame)

        if key == keyboard_spacebar:
            break
    else:
        raise IOError('Cannot open webcam')

    videocapture.release()
    cv2.destroyAllWindows()

def do_training() -> None:
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

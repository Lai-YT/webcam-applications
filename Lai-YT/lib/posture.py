import cv2
import numpy as np
import os
from sklearn.utils import class_weight
from tensorflow.keras import layers, models
from typing import Dict, List, Tuple
from pathlib import Path

from .color import *
from .cv_font import *

# Add this in if you require sounds
from playsound import playsound

# Config settings
image_dimensions: Tuple[int, int] = (224, 224)
epochs: int = 10
keyboard_spacebar: int = 32

# type hints
Image = np.ndarray


def load_model(model_path: str):
    return models.load_model(model_path)

def do_posture_watch(im_color: Image, mymodel , soundson: bool, mp3file: str) -> Image:
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

    # Video capture stuff
    videocapture = cv2.VideoCapture(0)
    if not videocapture.isOpened():
        raise IOError('Cannot open webcam')

    while True:
        _, frame = videocapture.read()
        filename: str = f'{output_folder}/{img_count:08}.jpg'
        cv2.imwrite(filename, frame)
        img_count += 1
        key: int = cv2.waitKey(1000)
        cv2.imshow('sample capturing...', frame)

        if key == keyboard_spacebar:
            break

    videocapture.release()
    cv2.destroyAllWindows()


def do_training(training_dir: str, model_path: str) -> None:
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

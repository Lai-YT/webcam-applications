import cv2
import numpy
import os
import shutil
from enum import Enum, unique
from nptyping import Float, Int, NDArray, UInt8
from pathlib import Path
from sklearn.utils import class_weight
from tensorflow.keras import layers, models
from typing import Any, Dict, List, Tuple

from .image_type import ColorImage, GrayImage
from .path import to_abs_path


@unique
class PostureLabel(Enum):
    # The values should start from 0 and be consecutive,
    # since they're also used to represent the result of prediction.
    good:  int = 0
    slump: int = 1


SAMPLE_DIR: str = to_abs_path("train_sample")
MODEL_PATH: str = to_abs_path("trained_models/write_model.h5")
IMAGE_DIMENSIONS: Tuple[int, int] = (224, 224)
EPOCHS: int = 10
KEYBOARD_SPACEBAR: int = 32

def capture_writing_action(label: PostureLabel) -> None:
    """Capture images for train_model().

    Arguments:
        label (PostureLabel): Label of the posture, good or slump
    """
    output_folder: str = f'{SAMPLE_DIR}/{label.name}'
    print(f'Capturing samples into folder {output_folder}...')
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    # get the number of the last image, img_count follows behind
    img_count: int = 0
    exist_images: List[str] = os.listdir(output_folder)
    # not empty
    if exist_images:
        img_count = int(''.join(n for n in exist_images[-1] if n.isdigit())) + 1

    videocapture = cv2.VideoCapture(0)
    while videocapture.isOpened():
        _, frame = videocapture.read()

        filename: str = f'{output_folder}/{img_count:04d}.jpg'
        cv2.imwrite(filename, frame)
        img_count += 1
        key: int = cv2.waitKey(300)  # ms, approximately the capture period
        cv2.imshow('sample capturing...', frame)

        if key == KEYBOARD_SPACEBAR:
            break
    else:
        raise IOError('Cannot open webcam')

    videocapture.release()
    cv2.destroyAllWindows()


def train_writing_model() -> None:
    """The images captured by capture_action() will be used to train a writing model."""
    train_images: List[GrayImage] = []
    train_labels: List[int] = []

    # The order(index) of the class is the order of the ints that PostureLabels represent.
    # i.e., good.value = 0, slump.value = 1
    # So is clear when the result of the prediction is 1, we now it's slump.
    class_folders: List[PostureLabel] = [PostureLabel.good, PostureLabel.slump]
    class_label_indexer: int = 0
    for c in class_folders:
        print(f'Training with label {c.name}...')
        for f in os.listdir(f'{SAMPLE_DIR}/{c.name}'):
            image: GrayImage = cv2.imread(f'{SAMPLE_DIR}/{c.name}/{f}', cv2.IMREAD_GRAYSCALE)
            image = cv2.resize(image, IMAGE_DIMENSIONS)
            train_images.append(image)
            train_labels.append(class_label_indexer)
        class_label_indexer += 1

    # numpy array with GrayImages
    images: NDArray[(Any, Any, Any), UInt8] = numpy.array(train_images)
    labels: NDArray[(Any,), Int[32]] = numpy.array(train_labels)
    images = images / 255  # Normalize image
    images = images.reshape(len(images), *IMAGE_DIMENSIONS, 1)

    class_weights: NDArray[(Any,), Float[64]] = class_weight.compute_sample_weight('balanced', labels)
    weights: Dict[int, float] = {i : weight for i, weight in enumerate(class_weights)}
    model = models.Sequential()
    model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=(*IMAGE_DIMENSIONS, 1)))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(64, (3, 3), activation='relu'))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(64, (3, 3), activation='relu'))
    model.add(layers.Flatten())
    model.add(layers.Dense(64, activation='relu'))
    model.add(layers.Dense(len(class_folders), activation='softmax'))
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy',  metrics=['accuracy'])
    model.fit(images, labels, epochs=EPOCHS, class_weight=weights)
    model.save(MODEL_PATH)


def remove_sample_images() -> None:
    """Removes the train folder under directory lib.
    Ignore errors when folder not exist.
    """
    shutil.rmtree(SAMPLE_DIR, ignore_errors=True)

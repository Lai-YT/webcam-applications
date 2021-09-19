import os
import shutil
from enum import Enum, unique
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from nptyping import Float, Int, NDArray, UInt8
from sklearn.utils import class_weight
from tensorflow.keras import layers, models

from lib.color import RED
from lib.cv_font import FONT_3
from lib.image_type import ColorImage, GrayImage
from lib.path import to_abs_path


@unique
class PostureLabel(Enum):
    # The values should start from 0 and be consecutive,
    # since they're also used to represent the result of prediction.
    good:  int = 0
    slump: int = 1


SAMPLE_DIR: str = to_abs_path("train_sample")
MODEL_PATH: str = to_abs_path("trained_models/write_model.h5")
IMAGE_DIMENSIONS: Tuple[int, int] = (224, 224)


class ModelTrainer(QObject):
    s_train_finished = pyqtSignal()

    def __init__(self, img_count: int):
        super().__init__()
        self._img_count = img_count

    def capture_sample_images(self, label: PostureLabel, capture_period: int = 50) -> None:
        """Capture images for train_model().

        Arguments:
            label (PostureLabel): Label of the posture, good or slump
            capture_period (bool): Captures 1 image per capture_period (ms). 300 in default
        """
        output_folder: str = f"{SAMPLE_DIR}/{label.name}"
        print(f"Capturing samples into folder {output_folder}...")
        Path(output_folder).mkdir(parents=True, exist_ok=True)

        self._capture_flag = True

        img_count: int = 0
        videocapture = cv2.VideoCapture(0)
        while img_count < self._img_count / 2:
            _, frame = videocapture.read()

            filename: str = f"{output_folder}/{img_count:04d}.jpg"
            img_count += 1
            # Make sure the frame is stored before putting text on, so samplea aren't poluted.
            # Also the img_count increases before putting text.
            # Start from 1 is the normal perspective (from 0 is computer science perspective)
            cv2.imwrite(filename, frame)
            cv2.putText(frame, f"Image Count: {img_count}", (5, 25), FONT_3, 0.8, RED, 2)
            cv2.imshow("sample capturing...", frame)
            cv2.waitKey(capture_period)

        videocapture.release()
        cv2.destroyAllWindows()

    def stop_capturing(self):
        """This will stops the capturing of capture_sample_images().
        No effect if already stopped.
        """
        self._capture_flag = False

    @pyqtSlot()
    @pyqtSlot(int)
    def train_model(self, epochs: int = 10) -> None:
        """The images captured by capture_sample_images() will be used to train a writing model."""
        train_images: List[GrayImage] = []
        train_labels: List[int] = []

        # The order(index) of the class is the order of the ints that PostureLabels represent.
        # i.e., good.value = 0, slump.value = 1
        # So is clear when the result of the prediction is 1, we now it's slump.
        class_folders: List[PostureLabel] = [PostureLabel.good, PostureLabel.slump]
        class_label_indexer: int = 0
        for label in class_folders:
            image_paths = os.listdir(f"{SAMPLE_DIR}/{label.name}")

            if not image_paths:
                print(f"No images in folder '{label.name}'.")
            else:
                print(f"Training with label {label.name}...")
                for path in image_paths:
                    image: GrayImage = cv2.imread(f"{SAMPLE_DIR}/{label.name}/{path}", cv2.IMREAD_GRAYSCALE)
                    image = cv2.resize(image, IMAGE_DIMENSIONS)
                    train_images.append(image)
                    train_labels.append(class_label_indexer)
            class_label_indexer += 1

        # Both folders are empty / folder "good" is empty / folder "slump" is empty.
        # The first one in train_labels is 1 mean there's no label good (0);
        # the last one is 0 means there's no label slump (1).
        if (not train_images
                or train_labels[0] == PostureLabel.slump.value
                or train_labels[-1] == PostureLabel.good.value):
            print("Training failed.")
            return

        # numpy array with GrayImages
        images: NDArray[(Any, Any, Any), UInt8] = numpy.array(train_images)
        labels: NDArray[(Any,), Int[32]] = numpy.array(train_labels)
        images = images / 255  # Normalize image
        images = images.reshape(len(images), *IMAGE_DIMENSIONS, 1)

        class_weights: NDArray[(Any,), Float[64]] = class_weight.compute_sample_weight("balanced", labels)
        weights: Dict[int, float] = {i : weight for i, weight in enumerate(class_weights)}
        model = models.Sequential()
        model.add(layers.Conv2D(32, (3, 3), activation="relu", input_shape=(*IMAGE_DIMENSIONS, 1)))
        model.add(layers.MaxPooling2D((2, 2)))
        model.add(layers.Conv2D(64, (3, 3), activation="relu"))
        model.add(layers.MaxPooling2D((2, 2)))
        model.add(layers.Conv2D(64, (3, 3), activation="relu"))
        model.add(layers.Flatten())
        model.add(layers.Dense(64, activation="relu"))
        model.add(layers.Dense(len(class_folders), activation="softmax"))
        model.compile(optimizer="adam", loss="sparse_categorical_crossentropy",  metrics=["accuracy"])
        model.fit(images, labels, epochs=epochs, class_weight=weights)
        model.save(MODEL_PATH)

        print("Training finished.")
        self.s_train_finished.emit()

    def remove_sample_images(self) -> None:
        """Removes the train folder under directory lib.
        Ignore errors when folder not exist.
        """
        shutil.rmtree(SAMPLE_DIR, ignore_errors=True)

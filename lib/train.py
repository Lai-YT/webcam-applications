import os
import copy
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


class ModelPath(Enum):
    default = to_abs_path("trained_models/default_model.h5")
    custom = to_abs_path("trained_models/custom_model.h5")


class ModelTrainer(QObject):
    SAMPLE_DIR: str = to_abs_path("train_sample")
    IMAGE_DIMENSIONS: Tuple[int, int] = (224, 224)

    s_train_finished = pyqtSignal()  # Emit when the train_model() is finished (or failed).
    s_train_failed = pyqtSignal(str)  # Emit if the train_model() fails, str is the message.
    s_capture_finished = pyqtSignal([PostureLabel, int])  # int is the number of sample images.

    def __init__(self):
        super().__init__()

        self._count_images()

    def capture_sample_images(self, label: PostureLabel, capture_period: int = 50) -> None:
        """Capture images for train_model().

        Arguments:
            label (PostureLabel): Label of the posture, good or slump
            capture_period (bool): Captures 1 image per capture_period (ms). 300 in default
        """
        output_folder: str = f"{ModelTrainer.SAMPLE_DIR}/{label.name}"
        print(f"Capturing samples into folder {output_folder}...")
        # mkdir anyway to make sure the label folders exist.
        Path(output_folder).mkdir(parents=True, exist_ok=True)

        self._capture_flag = True

        image_count: int = 0
        videocapture = cv2.VideoCapture(0)
        while self._capture_flag:
            _, frame = videocapture.read()

            filename: str = f"{output_folder}/{image_count:04d}.jpg"
            image_count += 1
            # Make sure the frame is stored before putting text on, so samplea aren't poluted.
            # Also the image_count increases before putting text.
            # Start from 1 is the normal perspective (from 0 is computer science perspective)
            cv2.imwrite(filename, frame)
            cv2.putText(frame, f"Image Count: {image_count}", (5, 25), FONT_3, 0.8, RED, 2)
            cv2.imshow("sample capturing...", frame)
            cv2.waitKey(capture_period)
        # e.g., If there were N images, and M images are captured this time,
        # where N > M.
        # Then after this capture, there are still N images, but the leading M
        # images are new.
        self._image_count[label] = max(self._image_count[label], image_count)
        videocapture.release()
        cv2.destroyAllWindows()
        self.s_capture_finished.emit(label, self._image_count[label])

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
        fail_message: str = ""  # Will be sent if the training fails.

        # The order(index) of the class is the order of the ints that PostureLabels represent.
        # i.e., good.value = 0, slump.value = 1
        # So is clear when the result of the prediction is 1, we now it's slump.
        class_folders: List[PostureLabel] = [PostureLabel.good, PostureLabel.slump]
        class_label_indexer: int = 0
        for label in class_folders:
            if self._image_count[label] == 0:
                print(f"No image of label '{label.name}'.")
                fail_message += f"No image of label '{label.name}'.\n"
            else:
                print(f"Training with label {label.name}...")

                image_paths = os.listdir(f"{ModelTrainer.SAMPLE_DIR}/{label.name}")
                for path in image_paths:
                    image: GrayImage = cv2.imread(f"{ModelTrainer.SAMPLE_DIR}/{label.name}/{path}", cv2.IMREAD_GRAYSCALE)
                    image = cv2.resize(image, ModelTrainer.IMAGE_DIMENSIONS)
                    train_images.append(image)
                    train_labels.append(class_label_indexer)
            class_label_indexer += 1

        # If not all values aren't 0 => If any of the value is 0.
        if not all(self._image_count.values()):
            print("Training failed.")
            self.s_train_failed.emit(fail_message)
            self.s_train_finished.emit()
            return

        # numpy array with GrayImages
        images: NDArray[(Any, Any, Any), UInt8] = numpy.array(train_images)
        labels: NDArray[(Any,), Int[32]] = numpy.array(train_labels)
        images = images / 255  # Normalize image
        images = images.reshape(len(images), *ModelTrainer.IMAGE_DIMENSIONS, 1)

        class_weights: NDArray[(Any,), Float[64]] = class_weight.compute_sample_weight("balanced", labels)
        weights: Dict[int, float] = {i : weight for i, weight in enumerate(class_weights)}
        model = models.Sequential()
        model.add(layers.Conv2D(32, (3, 3), activation="relu", input_shape=(*ModelTrainer.IMAGE_DIMENSIONS, 1)))
        model.add(layers.MaxPooling2D((2, 2)))
        model.add(layers.Conv2D(64, (3, 3), activation="relu"))
        model.add(layers.MaxPooling2D((2, 2)))
        model.add(layers.Conv2D(64, (3, 3), activation="relu"))
        model.add(layers.Flatten())
        model.add(layers.Dense(64, activation="relu"))
        model.add(layers.Dense(len(class_folders), activation="softmax"))
        model.compile(optimizer="adam", loss="sparse_categorical_crossentropy",  metrics=["accuracy"])
        model.fit(images, labels, epochs=epochs, class_weight=weights)
        model.save(ModelPath.custom.value)

        print("Training finished.")
        self.s_train_finished.emit()

    def remove_sample_images(self, label: PostureLabel) -> None:
        """Removes the sample images of ModelTrainer.
        Ignore errors when folder not exist.
        """
        # Remove the entire label folder and set count to 0.
        shutil.rmtree(f"{ModelTrainer.SAMPLE_DIR}/{label.name}", ignore_errors=True)
        self._image_count[label] = 0

    def get_image_count(self):
        return copy.deepcopy(self._image_count)

    @staticmethod
    def load_model(model_path: ModelPath):
        return models.load_model(model_path.value)

    def _count_images(self):
        self._image_count: Dict[PostureLabel, int] = {}
        for label in PostureLabel:
            # The label file might not exist if haven't trained yet.
            try:
                count = len(os.listdir(f"{ModelTrainer.SAMPLE_DIR}/{label.name}"))
            except FileNotFoundError:
                count = 0
            self._image_count[label] = count

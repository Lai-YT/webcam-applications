import cv2
import numpy as np
import os
import shutil
from enum import Enum, unique
from nptyping import Float, Int, NDArray, UInt8
from pathlib import Path
from sklearn.utils import class_weight
from tensorflow.keras import layers, models
from typing import Any, Dict, List, Tuple, Union

from .face_distance_detector import FaceDetector
from .image_type import ColorImage, GrayImage
from .path import to_abs_path


@unique
class PostureMode(Enum):
    # The values should start from 0 and be consecutive,
    # since they're also used to represent the result of prediction.
    gaze:  int = 0
    write: int = 1

@unique
class PostureLabel(Enum):
    # The values should start from 0 and be consecutive,
    # since they're also used to represent the result of prediction.
    good:  int = 0
    slump: int = 1


sample_dir: str = to_abs_path("train_sample")
model_paths: Dict[PostureMode, str] = {}
model_paths[PostureMode.gaze]  = to_abs_path("trained_models/gaze_model.h5")
model_paths[PostureMode.write] = to_abs_path("trained_models/write_model.h5")
image_dimensions: Tuple[int, int] = (224, 224)
epochs: int = 10
keyboard_spacebar: int = 32

def capture_action(mode: PostureMode, label: PostureLabel) -> None:
    """Capture images for train_model().

    Arguments:
        mode (PostureMode): Mode of the posture, gaze or write
        label (PostureLabel): Label of the posture,  good or slump
    """
    output_folder: str = f'{sample_dir}/{mode.name}/{label.name}'
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

        has_face: bool = True if FaceDetector.face_data(frame) else False
        # to increse the accuracy prediction
        # only face image in gaze mode and no face image in write mode
        if (mode == PostureMode.gaze and has_face or
            mode == PostureMode.write and not has_face):
            filename: str = f'{output_folder}/{img_count:08}.jpg'
            cv2.imwrite(filename, frame)
            img_count += 1
        key: int = cv2.waitKey(300)  # ms, approximately the capture period
        cv2.imshow('sample capturing...', frame)

        if key == keyboard_spacebar:
            break
    else:
        raise IOError('Cannot open webcam')

    videocapture.release()
    cv2.destroyAllWindows()


def train_model() -> None:
    """The images captured by capture_action() will be used to train 2 models.
    First is the gaze-mode model; second is the write-mode model.
    """
    train_images: Dict[PostureMode, List[GrayImage]] = {PostureMode.gaze: [], PostureMode.write: []}
    train_labels: Dict[PostureMode, List[int]] = {PostureMode.gaze: [], PostureMode.write: []}

    # The order(index) of the class is the order of the ints that PostureLabels represent.
    # i.e., good.value = 0, slump.value = 1
    # So is clear when the result of the prediction is 1, we now it's slump.
    class_folders: Dict[PostureMode, List[PostureLabel]] = {}
    class_folders[PostureMode.gaze]  = [PostureLabel.good, PostureLabel.slump]
    class_folders[PostureMode.write] = [PostureLabel.good, PostureLabel.slump]

    def train(mode: PostureMode) -> None:
        """
        The outer train method does the classification
        and this inner method does the real training.
        """
        # The second type is a numpy array with GrayImages.
        images: Union[List[GrayImage], NDArray[(Any, Any, Any), UInt8]] = train_images[mode]
        labels: Union[List[int], NDArray[(Any,), Int[32]]] = train_labels[mode]
        classes: List[PostureLabel] = class_folders[mode]
        print(f'For {mode.name} mode:')
        class_label_indexer: int = 0
        for c in classes:
            print(f'Training with label {c.name}...')
            for f in os.listdir(f'{sample_dir}/{mode.name}/{c.name}'):
                im: GrayImage = cv2.imread(f'{sample_dir}/{mode.name}/{c.name}/{f}', cv2.IMREAD_GRAYSCALE)
                im = cv2.resize(im, image_dimensions)
                images.append(im)
                labels.append(class_label_indexer)
            class_label_indexer += 1

        images = np.array(images)
        labels = np.array(labels)
        images = images / 255  # Normalize image
        images = images.reshape(len(images), *image_dimensions, 1)

        class_weights: NDArray[(Any,), Float[64]] = class_weight.compute_sample_weight('balanced', labels)
        weights: Dict[int, float] = {i : weight for i, weight in enumerate(class_weights)}
        model = models.Sequential()
        model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=(*image_dimensions, 1)))
        model.add(layers.MaxPooling2D((2, 2)))
        model.add(layers.Conv2D(64, (3, 3), activation='relu'))
        model.add(layers.MaxPooling2D((2, 2)))
        model.add(layers.Conv2D(64, (3, 3), activation='relu'))
        model.add(layers.Flatten())
        model.add(layers.Dense(64, activation='relu'))
        model.add(layers.Dense(len(classes), activation='softmax'))
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy',  metrics=['accuracy'])
        model.fit(images, labels, epochs=epochs, class_weight=weights)
        model.save(model_paths[mode])

    train(PostureMode.gaze)
    train(PostureMode.write)


def load_posture_model() -> Dict:
    """Returns the dictionary of models trained by train_model().
    Key of the dictionary (Dict[PostureMode, tensorflow.keras.Model]) is the PostureMode,
    their corresponding model is the value.
    """
    model: Dict = {}
    model[PostureMode.gaze] = models.load_model(model_paths[PostureMode.gaze])
    model[PostureMode.write] = models.load_model(model_paths[PostureMode.gaze])
    return model


def remove_sample_images() -> None:
    """Removes the train folder under directory lib.
    Ignore errors when folder not exist.
    """
    shutil.rmtree(sample_dir, ignore_errors=True)

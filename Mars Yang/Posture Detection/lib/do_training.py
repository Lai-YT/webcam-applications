import numpy as np
import os
import cv2
from tensorflow.keras import layers, models
from sklearn.utils import class_weight
from typing import Dict

# Config settings
image_dimensions = (224, 224) 
epochs = 10
model_name = 'posture_model.h5'
training_dir = 'train'

def do_training():
    train_images = []
    train_labels = []
    class_folders = os.listdir(training_dir)

    class_label_indexer = 0
    for c in class_folders:
        print('Training with class {}'.format(c))
        for f in os.listdir('{}/{}'.format(training_dir, c)):
            im = cv2.imread('{}/{}/{}'.format(training_dir, c, f), 0)
            im = cv2.resize(im, image_dimensions)
            train_images.append(im)
            train_labels.append(class_label_indexer)
        class_label_indexer = class_label_indexer + 1

    train_images = np.array(train_images)
    train_labels = np.array(train_labels)

    indices = np.arange(train_labels.shape[0])
    np.random.shuffle(indices)
    images = train_images[indices]
    labels = train_labels[indices]
    train_images = np.array(train_images)
    train_images = train_images / 255  # Normalize image
    n = len(train_images)
    train_images = train_images.reshape(n, image_dimensions[0], image_dimensions[1], 1)

    class_weights: np.ndarray = class_weight.compute_sample_weight('balanced', train_labels)
    weights: Dict[int, float] = {i: weight for i, weight in enumerate(class_weights)}
    model = models.Sequential()
    model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=(image_dimensions[0], image_dimensions[1], 1)))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(64, (3, 3), activation='relu'))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(64, (3, 3), activation='relu'))
    model.add(layers.Flatten())
    model.add(layers.Dense(64, activation='relu'))
    model.add(layers.Dense(len(class_folders), activation='softmax'))
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy',  metrics=['accuracy'])
    model.fit(train_images, train_labels, epochs=epochs, class_weight = weights)
    model.save(model_name)
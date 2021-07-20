import numpy as np
import cv2
from tensorflow.keras import models

# Add this in if you require sounds
from playsound import playsound

# Config settings
image_dimensions = (224, 224) 
model_name = 'posture_model.h5'
keyboard_spacebar = 32

mp3file = 'sounds/what.mp3'

def do_live_view(soundson):
    mymodel = models.load_model(model_name)

    # Video capture stuff
    videocapture = cv2.VideoCapture(0)
    if not videocapture.isOpened():
        raise IOError('Cannot open webcam')

    while True:
        _, frame = videocapture.read()
        cv2.imwrite('thisframe.png', frame)
        im_color = cv2.imread('thisframe.png')
        im = cv2.cvtColor(im_color, cv2.COLOR_BGR2GRAY)

        im = cv2.resize(im, image_dimensions)
        im = im / 255  # Normalize the image
        im = im.reshape(1, image_dimensions[0], image_dimensions[1], 1)

        predictions = mymodel.predict(im)
        class_pred = np.argmax(predictions) 
        conf = predictions[0][class_pred]

        if (soundson and class_pred==1):
            # If slumped with sounds on
            playsound(mp3file)

        im_color = cv2.resize(im_color, (800, 480), interpolation = cv2.INTER_AREA)
        im_color = cv2.flip(im_color, flipCode=1) # flip horizontally

        if (class_pred == 1):
            # Slumped
            im_color = cv2.putText(im_color, 'Slumped posture', (10, 70),  cv2.FONT_HERSHEY_SIMPLEX, 2,  (0, 0, 255), thickness = 3)
        elif (class_pred == 2):
            # Writing
            im_color = cv2.putText(im_color, 'Writing', (10, 70),  cv2.FONT_HERSHEY_SIMPLEX, 2,  (255, 0, ), thickness = 3)
        else:
            # Good
            im_color = cv2.putText(im_color, 'Good posture', (10, 70),  cv2.FONT_HERSHEY_SIMPLEX, 2,  (0, 255, 0), thickness = 2)

        msg = 'Confidence {}%'.format(round(int(conf*100)))
        im_color = cv2.putText(im_color, msg, (15, 110),  cv2.FONT_HERSHEY_SIMPLEX, 1,  (200, 200, 255), thickness = 2)

        cv2.imshow('', im_color)
        cv2.moveWindow('', 20, 20)
        key = cv2.waitKey(20)

        if key == keyboard_spacebar:
            break

    videocapture.release()
    cv2.destroyAllWindows()
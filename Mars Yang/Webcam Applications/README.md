# Webcam Application

Thanks to the contributors of libraries, we try to make all applications require \
only 1 camera, which is the webcam.

## Adjustions (110/9/16) by Mars Yang

1. At the beginning, no ratio button is toggled, so the "Capture" button is disabled. The "Capture" button will be set enabled when one of the ratio buttons is toggled.
2. Put **Image Count** on the frame after saved in the folder but before imshow().
3. If one of the folders in train_sample is empty, put a *training failed* text on the terminal. Otherwise, put a *training finished* text.

## Settings

1. Put a front-face picture of yours named **ref_img.jpg** in folder **img**.
1. Set the parameters in **parameters.txt**.
1. Also run train_posture.py to set the model.
  - First, run the "Capture" modes whilst moving a bit in space to give a variety amongst the images. \
  Press the "Finish" button to stop capture after about 30 seconds.
  - Then, press the "Train" button to train model with images.

## main

It's the visualized version that shows the detection result and warnings. \
Using a friendly *Graphical User Interface* instead of Command Line Interface.

## demo

*This file is a non-GUI version, we will have it updated in the near future.*

This is what we want to bring into practice. \
All detections process in the background. Warnings pop when conditions meet. \
Press "esc" to end the program.

```
usage: demo.py [-h] [-d] [-t] [-p]

Webcam applications with distance measurement, eye focus timing and posture watching.
Press "esc" to end the program.

optional arguments:
  -h, --help      show this help message and exit
  -d, --distance  warning shows if the user gets too close to the screen
  -t, --time      reminds when it's time to take a break
  -p, --posture   sound plays when the user has bad posture
```

## Topics

### Distance Measurement

Based on [Asadullah-Dal17/Distance_measurement_using_single_camera](https://github.com/Asadullah-Dal17/Distance_measurement_using_single_camera).

### Posture Watch

Base on [saubury/posture-watch](https://github.com/saubury/posture-watch).

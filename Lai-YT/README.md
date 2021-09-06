# Webcam Application

Thanks to the contributors of libraries, we try to make all applications require \
only 1 camera, which is the webcam.

## Settings

1. Put a front-face picture of yours named **ref_img.jpg** in folder **img**.
1. Set the parameters in **parameters.txt**.
1. Also run train_posture.py to set the model.
  - First, run the capture modes whilst moving a bit in space to give a variety amongst the images. \
  Press the "space" bar to stop capture after about 30 seconds.
  - Then, run the train mode to train model with images.

```
usage: train_posture.py [-h] [-cg | -cs | -t | -r]

Capture images and train the model before using the functon of posture watching (in demo.py and alpha.py).

optional arguments:
  -h, --help            show this help message and exit
  -cg, --capture-good   capture sample images of good, healthy posture when writing in front of the screen
  -cs, --capture-slump  capture sample images of poor, slumped posture when writing in front of the screen
  -t, --train           train model with captured images
  -r, --reset           remove sample images before starting a new series of capture
```

## demo

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

## main

It's the visualized version that shows the detection result and warnings. \
Using a friendly *Graphical User Interface* instead of Command Line Interface.

## Topics

### Distance Measurement

Based on [Asadullah-Dal17/Distance_measurement_using_single_camera](https://github.com/Asadullah-Dal17/Distance_measurement_using_single_camera).

### Posture Watch

Base on [saubury/posture-watch](https://github.com/saubury/posture-watch).

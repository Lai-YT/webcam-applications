# Webcam Application

Thanks to the contributors of libraries, we try to make all applications require \
only 1 camera, which is the webcam.

## Settings

1. Put a front-face picture of yours named **ref_img.jpg** in folder **img**.
2. Set the parameters in **parameters.txt**.
3. Also run train_posture.py to set the model.
  - First, run the capture modes whilst moving a bit in space to give a variety amongst the images. \
  Press the "space" bar to stop capture after about 30 seconds.
  - Then, run the train mode to train model with images.

```
usage: train_posture.py [-h] [-gg | -gs | -wg | -ws | -t | -r]

Capture images and train the model before using the functon of posture watching (in demo.py and alpha.py).


optional arguments:
  -h, --help            show this help message and exit
  -gg, --capture-gaze-good
                        capture sample images of good, healthy posture when gazing the screen
  -gs, --capture-gaze-slump
                        capture sample images of poor, slumped posture when gazing the screen
  -wg, --capture-write-good
                        capture sample images of good, healthy posture when writing in front of the screen
  -ws, --capture-write-slump
                        capture sample images of poor, slumped posture when writing in front of the screen
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

## alpha

It's the visualized version that shows the detection result without warnings. \
Press "esc" to end the program. \
Use for detection adjustments.

```
usage: alpha.py [-h] [-d] [-t] [-p]

visualized ver. of webcam applications with distance measurement, eye focus
timing and posture watching

optional arguments:
  -h, --help      show this help message and exit
  -d, --distance  enable distance measurement
  -t, --time      enable eye focus timing
  -p, --posture   enable posture watching
```

## Topics

### Distance Measurement

Based on [Asadullah-Dal17/Distance_measurement_using_single_camera](https://github.com/Asadullah-Dal17/Distance_measurement_using_single_camera).

### Gaze Tracking

Using the library provided at [antoinelame/GazeTracking](https://github.com/antoinelame/GazeTracking).

### Posture Watch

Base on [saubury/posture-watch](https://github.com/saubury/posture-watch).

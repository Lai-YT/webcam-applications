# Webcam Application

Thanks to the contributors of libraries, we try to make all applications require \
only 1 camera, which is the webcam.

## Settings

Put a front-face picture of yours named **ref_img.jpg** in folder **img** \
and set the parameters in **parameters.txt**. \
Also run train_posture.py to set the model.

```
usage: train_posture.py [-h] [-cg | -cs | -t]

Capture images and train the model before using the functon of posture
watching (demo.py and real.py).

optional arguments:
  -h, --help            show this help message and exit
  -cg, --capture-good   capture example of good, healthy posture
  -cs, --capture-slump  capture example of poor, slumped posture
  -t, --train           train model with captured images
```

## demo

It's the visualized version that shows the detection result without warnings.

```
usage: demo.py [-h] [-d] [-t] [-p]

visualized ver. of webcam applications with distance measurement, eye focus
timing and posture watch

optional arguments:
  -h, --help      show this help message and exit
  -d, --distance  enable distance measurement
  -t, --time      enable eye focus timing
  -p, --posture   enable posture watching
```

## Applications

Command `python real.py` to see what we want to bring in practice. \
All detections process in the background. Warnings pop when conditions meet. \
Note that posture watch aren't ready.

## Topics

### Distance Measurement

Based on [Asadullah-Dal17/Distance_measurement_using_single_camera](https://github.com/Asadullah-Dal17/Distance_measurement_using_single_camera).

### Gaze Tracking

Using the library provided at [antoinelame/GazeTracking](https://github.com/antoinelame/GazeTracking).

### Posture Watch

Base on [saubury/posture-watch](https://github.com/saubury/posture-watch).

# Webcam Application

Thanks to the contributors of libraries, we try to make all applications require \
only 1 camera, which is the webcam.

## Settings

Put a front-face picture of yours named **ref_img.jpg** in folder **img** \
and set the parameters in **parameters.txt**. \
For posture watching, provide some samples and train the model. \
Please check out the usage of **demo.py**.

## demo

It's the visualized version that shows the detection result without warnings.

```
usage: demo.py [-h] [-cg] [-cs] [-t] [-a]

webcam applications with distance measurement, eye focus timing and posture watch

optional arguments:
  -h, --help            show this help message and exit
  -cg, --capture-good   capture example of good, healthy posture
  -cs, --capture-slump  capture example of poor, slumped posture
  -t, --train           train model with captured images
  -a, --applications    visualized detection with all applications
```

## Applications

Command `python real.py` to see what we want to bring in practice. \
All detections process in the background. Warnings pop when conditions meet.

## Topics

### Distance Measurement

Based on [Asadullah-Dal17/Distance_measurement_using_single_camera](https://github.com/Asadullah-Dal17/Distance_measurement_using_single_camera).

### Gaze Tracking

Using the library provided at [antoinelame/GazeTracking](https://github.com/antoinelame/GazeTracking).

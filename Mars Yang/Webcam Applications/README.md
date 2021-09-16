# Webcam Application

Thanks to the contributors of libraries, we try to make all applications require \
only 1 camera, which is the webcam.

* This README file only reports the adjustions I made. The general README is in the folder "Lai-YT".

## Adjustions (110/9/16) by Mars Yang

1. At the beginning, no ratio button is toggled, so the "Capture" button is disabled. The "Capture" button will be set enabled when one of the ratio buttons is toggled.
2. Put **Image Count** on the frame after saved in the folder but before imshow().
3. If one of the folders in train_sample is empty, output a ***"training failed"*** text on the terminal. Otherwise, output ***"training finished"***.
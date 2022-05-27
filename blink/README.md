# blink module: detecting blinks

## Basics

We've obtained the 64 face landmarks with *Dlib* before this module; in this module, `BlinkDetector` extracts 6 landmarks from each eyes (fig. 1) and tracks the changes on **Eye Aspect Ratio**s (*EAR*), which is
defined by (|P<sub>2</sub>-P<sub>6</sub>| + |P<sub>3</sub>-P<sub>5</sub>|) / (2|P<sub>1</sub>-P<sub>4</sub>|). *EAR* shows shape of the eye. When an eye closed, its *EAR* drops and approaches 0 theoretically.

![6 face landmarks around an eye](./assets/landmarks-around-eye.png) \
fig. 1

## Tracking change points

A **sliding window** is used to track the changes of **standard deviation** on current *EAR*s (fig. 2), if the standard deviation increases dramatically, there's a possible blink.

![Animation of change point detection via sliding window](https://www.iese.fraunhofer.de/blog/wp-content/uploads/2021/08/illustration_of_change_point_detectopn_via_sliding-window.gif) \
fig. 2

See more details at [EE-Ind-Stud-Group/blink-detection#change-point-detection](https://github.com/EE-Ind-Stud-Group/blink-detection#change-point-detection).

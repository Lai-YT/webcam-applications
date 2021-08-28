from sys import pycache_prefix
import alpha

# Model knows nothing about View.
# It takes the options and parameters from Controller,
# organize them and call methods to do the real work.
class WebcamApplication:
    def __init__(self):
        self._distance_detection = False
        self._parameters_of_distance_detection = {"Face Width": 0, "Distance": 0,}
        self._timer = False
        self._posture_detection = False

    def start(self):
        self.set_parameters()
        self.alpha()
        print(self.__dict__)

    def close(self):
        print("app closed")

    def enable_distance_detection(self, enable, face_width, distance):
        self._distance_detection = enable
        self._parameters_of_distance_detection["Face Width"] = face_width
        self._parameters_of_distance_detection["Distance"] = distance

    def enable_timer(self, enable):
        self._timer = enable

    def enable_posture_detection(self, enable):
        self._posture_detection = enable

    def set_parameters(self):
        '''Put parameters entered by user in parameters.txt'''
        file = open("./parameters.txt", "w")
        file.write(f'The distance(cm) between your face and the webcam when taking the picture: {self._parameters_of_distance_detection["Distance"]}\n')
        file.write(f'Your actual width(cm) of face: {self._parameters_of_distance_detection["Face Width"]}\n')
        file.close()

    def alpha(self):
        '''Start the process with chosen features.'''
        alpha.do_applications(self._distance_detection, 
                              self._timer, 
                              self._posture_detection)
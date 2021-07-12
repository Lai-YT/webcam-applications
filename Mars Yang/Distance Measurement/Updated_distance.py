import cv2
# variables
# distance from camera to object(face) measured
Known_distance = 60 # cm
Known_width = 15 # cm
Near_distance = 50 # cm
# Colors  >>> BGR Format(BLUE, GREEN, RED)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
BLACK = (0, 0, 0)
YELLOW = (0, 255, 255)
WHITE = (255, 255, 255)
CYAN = (255, 255, 0)
MAGENTA = (255, 0, 242)
GOLDEN = (32, 218, 165)
LIGHT_BLUE = (255, 9, 2)
PURPLE = (128, 0, 128)
CHOCOLATE = (30, 105, 210)
PINK = (147, 20, 255)
ORANGE = (0, 69, 255)

fonts = cv2.FONT_HERSHEY_COMPLEX
fonts2 = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX
fonts3 = cv2.FONT_HERSHEY_COMPLEX_SMALL
fonts4 = cv2.FONT_HERSHEY_TRIPLEX
# Camera Object
cap = cv2.VideoCapture(0)  # Number According to your Camera
Distance_level = 0

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'XVID')
# out = cv2.VideoWriter('output.mp4', fourcc, 30.0, (640, 480))

# face detector object
face_detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
# focal length finder function


def FocalLength(measured_distance, real_width, width_in_rf_image):
    # Function Discrption (Doc String)
    '''
    This Function Calculate the Focal Length(distance between lens to CMOS sensor), it is simple constant we can find by using 
    MEASURED_DISTACE, REAL_WIDTH(Actual width of object) and WIDTH_OF_OBJECT_IN_IMAGE 
    :param1 Measure_Distance(int): It is distance measured from object to the Camera while Capturing Reference image

    :param2 Real_Width(int): It is Actual width of object, in real world (like My face width is = 5.7 Inches)
    :param3 Width_In_Image(int): It is object width in the frame /image in our case in the reference image(found by Face detector) 
    :retrun Focal_Length(Float):
    '''
    focal_length = (width_in_rf_image * measured_distance) / real_width
    return focal_length
# distance estimation function


def Distance_finder(Focal_Length, real_face_width, face_width_in_frame):
    '''
    This Function simply Estimates the distance between object and camera using arguments(Focal_Length, Actual_object_width, Object_width_in_the_image)
    :param1 Focal_length(float): return by the Focal_Length_Finder function

    :param2 Real_Width(int): It is Actual width of object, in real world (like My face width is = 5.7 Inches)
    :param3 object_Width_Frame(int): width of object in the image(frame in our case, using Video feed)
    :return Distance(float) : distance Estimated  

    '''
    distance = (real_face_width * Focal_Length)/face_width_in_frame
    return distance

# face detection Fauction


def face_data(image, CallOut, Distance_level):
    '''

    This function Detect face and Draw Rectangle and display the distance over Screen

    :param1 Image(Mat): simply the frame 
    :param2 Call_Out(bool): If want show Distance and Rectangle on the Screen or not
    :param3 Distance_Level(int): which change the line according the Distance changes(Intractivate)
    :return1  face_width(int): it is width of face in the frame which allow us to calculate the distance and find focal length
    :return2 face(list): length of face and (face paramters)
    :return3 face_center_x: face centroid_x coordinate(x)
    :return4 face_center_y: face centroid_y coordinate(y)

    '''

    face_width = 0
    face_x, face_y = 0, 0
    face_center_x = 0
    face_center_y = 0
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray_image, 1.3, 5)
    for (x, y, w, h) in faces:
        line_thickness = 2
        LLV = int(h*0.12)
    
        cv2.line(image, (x, y+LLV), (x+LLV, y+LLV), (GREEN), line_thickness)
        cv2.line(image, (x+w-LLV, y+LLV), (x+w, y+LLV), (GREEN), line_thickness)
        cv2.line(image, (x, y+h), (x+LLV, y+h), (GREEN), line_thickness)
        cv2.line(image, (x+w-LLV, y+h), (x+w, y+h), (GREEN), line_thickness)

        cv2.line(image, (x, y+LLV), (x, y+LLV+LLV), (GREEN), line_thickness)
        cv2.line(image, (x+w, y+LLV), (x+w, y+LLV+LLV),
                 (GREEN), line_thickness)
        cv2.line(image, (x, y+h), (x, y+h-LLV), (GREEN), line_thickness)
        cv2.line(image, (x+w, y+h), (x+w, y+h-LLV), (GREEN), line_thickness)

        face_width = w
        face_center = []
        # Drwaing circle at the center of the face
        face_center_x = int(w/2)+x
        face_center_y = int(h/2)+y
        if Distance_level < 10:
            Distance_level = 10

        if CallOut == True:
            cv2.line(image, (x, y-11), (x+180, y-11), (ORANGE), 28)
            cv2.line(image, (x, y-11), (x+180, y-11), (YELLOW), 20)
            if Distance_level < Near_distance:
                cv2.line(image, (x, y-45), (x+100, y-45), (RED), 22)
                cv2.line(image, (x, y-11), (x+180, y-11), (RED), 18)
            else:
                cv2.line(image, (x, y-11), (max(x, int(x+(120-Distance_level)*180/(120-Near_distance))), y-11), (GREEN), 18)

    return face_width, faces, face_center_x, face_center_y


# reading reference image from directory
ref_image = cv2.imread("Ref_image.png")

ref_image_face_width, _, _, _ = face_data(ref_image, False, Distance_level)
Focal_length_found = FocalLength(
    Known_distance, Known_width, ref_image_face_width)
print(Focal_length_found)

while True:
    _, frame = cap.read()

    face_width_in_frame, Faces, FC_X, FC_Y = face_data(
        frame, True, Distance_level)
    # finding the distance by calling function Distance finder
    for (face_x, face_y, face_w, face_h) in Faces:
        if face_width_in_frame != 0:

            Distance = Distance_finder(
                Focal_length_found, Known_width, face_width_in_frame)
            Distance = round(Distance)

            # Drwaing Text on the screen
            Distance_level = int(Distance)
            cv2.putText(frame, f"Distance {Distance} cm",
                        (face_x-3, face_y-6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (BLACK), 1)
            
            # Warning when user is too near to the screen
            if Distance_level < Near_distance:
                cv2.putText(frame, f"TOO NEAR!!",
                            (face_x-3, face_y-40), cv2.FONT_HERSHEY_DUPLEX, 0.6, (WHITE), 1)
                cv2.putText(frame, f"STAY FARTHER, PLEASE.",
                            (0, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (RED), 2)
            else:
                cv2.putText(frame, f"PROPER DISTANCE",
                        (0, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (BLACK), 2)
            
    cv2.imshow("frame", frame)
    # out.write(frame)

    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
# out.release()
cv2.destroyAllWindows()
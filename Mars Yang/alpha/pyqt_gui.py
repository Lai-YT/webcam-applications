from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox, QLabel
from gui.LineEdit import Ui_MainWindow

import alpha
import sys


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # check box
        self.dist_checkbox = QCheckBox("Distance Measure", self)
        self.dist_checkbox.setGeometry(150, 10, 200, 45)
        self.dist_checkbox.setFont(QtGui.QFont('Arial', 12))
        self.timer_checkbox = QCheckBox("TImer", self)
        self.timer_checkbox.setGeometry(150, 55, 200, 45)
        self.timer_checkbox.setFont(QtGui.QFont('Arial', 12))
        self.post_checkbox = QCheckBox("Posture Detection", self)
        self.post_checkbox.setGeometry(150, 100, 200, 45)
        self.post_checkbox.setFont(QtGui.QFont('Arial', 12))

        # entries of face width and distance from the screen
        self.face_width_label = QLabel(self.ui.centralwidget)
        self.face_width_label.setText("Face width(cm): ")
        self.face_width_label.setFont(QtGui.QFont('Arial', 12))
        self.face_width_label.setGeometry(150, 155, 150, 20)
        self.face_width_entry = QtWidgets.QLineEdit(self.ui.centralwidget)
        self.face_width_entry.setText("15") # default
        self.face_width_entry.setGeometry(300, 155, 50, 25)
        self.face_width_entry.setAlignment(Qt.AlignCenter) # align center

        self.dist_label = QLabel(self.ui.centralwidget)
        self.dist_label.setText("Distance from screen(cm): ")
        self.dist_label.setFont(QtGui.QFont('Arial', 12))
        self.dist_label.setGeometry(105, 185, 240, 20)
        self.dist_entry = QtWidgets.QLineEdit(self.ui.centralwidget)
        self.dist_entry.setText("60") # default
        self.dist_entry.setGeometry(345, 185, 50, 25)
        self.dist_entry.setAlignment(Qt.AlignCenter) # align center
    
        # start button
        self.start_button = QtWidgets.QPushButton(self.ui.centralwidget)
        self.start_button.setGeometry(QtCore.QRect(125, 225, 250, 50))
        self.start_button.setText("Start Capturing")
        self.start_button.setFont(QtGui.QFont('Arial', 20))
        self.start_button.clicked.connect(self.alpha)
        self.quit_button = QtWidgets.QPushButton(self.ui.centralwidget)
        self.quit_button.setGeometry(QtCore.QRect(185, 290, 130, 50))
        self.quit_button.setText("Quit")
        self.quit_button.setFont(QtGui.QFont('Arial', 20))
        self.quit_button.clicked.connect(self.quit)

    def set_parameters(self) -> None:
        self.face_width = self.face_width_entry.text()
        self.dist = self.dist_entry.text()
        file = open("parameters.txt", "w")
        file.write(f'The distance(cm) between your face and the webcam when taking the picture: {self.face_width}\n')
        file.write(f'Your actual width(cm) of face: {self.dist}\n')
        file.close()

    def alpha(self) -> None:
        # put parameters entered by user in parameters.txt
        self.set_parameters()
        # start the process with chosen features
        alpha.do_applications(dist_measure=self.dist_checkbox.isChecked(), 
                              focus_time=self.timer_checkbox.isChecked(), 
                              post_watch=self.post_checkbox.isChecked())

    def quit(self) -> None:
        # finish the process and close all windows
        sys.exit(0)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
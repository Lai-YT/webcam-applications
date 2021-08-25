from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QCheckBox
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

        # start button
        self.ui.pushButton.setText("Start Capturing")
        self.ui.pushButton.setFont(QtGui.QFont('Arial', 20))
        self.ui.pushButton.clicked.connect(self.alpha)

    def alpha(self) -> None:
        # start the process with chosen features
        alpha.do_applications(dist_measure=self.dist_checkbox.isChecked(), 
                              focus_time=self.timer_checkbox.isChecked(), 
                              post_watch=self.post_checkbox.isChecked())
        sys.exit(0)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
from gui.component import ActionButton
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget,QVBoxLayout,QFormLayout
from PyQt5.QtGui import QPixmap, QImage,QFont
from PyQt5.QtCore import QTimer

class window(QWidget):
    def __init__(self):
        super().__init__()
        self.label = QLabel(self)
        self.label.setGeometry(50,0,500,200)
        self.label.setFont(QFont("Roman times",100,QFont.Bold)) #設訂字體
        self.setGeometry(500,300,600,400)
        self.setWindowTitle("PyQT Timer Demo")

        self._general_layout = QVBoxLayout()
        self.setLayout(self._general_layout)
        self.pause = ActionButton("Pause")
        self.resume = ActionButton("Resume")
        self.button_layout = QFormLayout()
        self.button_layout.addRow(self.pause)
        self.button_layout.addRow(self.resume)
        self._general_layout.addLayout(self.button_layout)

        self.pause.clicked.connect(self.pause_time)
        self.pause.clicked.connect(self.resume_time)


        self.timer=QTimer(self) # 呼叫 QTimer 
        self.timer.timeout.connect(self.run) #當時間到時會執行 run
        self.timer.start(1000) #啟動 Timer .. 每隔1000ms 會觸發 run
        self.time = 0 #初始 total


    def run(self):

        self.label.setText(f"t. {(self.time // 60):02d}:{(self.time % 60):02d}") # 顯示 total
        self.time+=1 #Total 加 1 

    def pause_time(self):
        self.timer.stop()

    def resume_time(self):
        self.timer.start(1000)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = window()
    ex.show()
    sys.exit(app.exec_()) 
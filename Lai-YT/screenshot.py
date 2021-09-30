"""Creates a screenshot folder under current working directory and takes 10
screenshots in 1 minutes.
"""

from pathlib import Path
from time import sleep

from PyQt5.QtWidgets import QApplication


app = QApplication([])

folder_name = "screenshot"
# Prepare the folder to put screenshots.
Path(folder_name).mkdir(exist_ok=True)
# Have a QScreen instance to grabWindow with.
screen = QApplication.primaryScreen()

# Take 10 shots in 1 min.
for i in range(10):
    screenshot = screen.grabWindow(QApplication.desktop().winId())
    screenshot.save(f"{folder_name}\shot_{i}.jpg")
    sleep(6)

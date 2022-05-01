from enum import Enum

from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QComboBox

import gui.img.icon


class Language(Enum):
    ENGLISH = 0
    CHINESE = 1


class LanguageComboBox(QComboBox):
    def __init__(self) -> None:
        super().__init__()
        self.setFont(QFont("Arial", 12))
        self.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self._add_languages()

    def _add_languages(self) -> None:
        # have the order match the value of enum Language
        self.addItem(QIcon(":us-flag.ico"), Language.ENGLISH.name.capitalize())
        self.addItem(QIcon(":taiwan-flag.ico"), Language.CHINESE.name.capitalize())

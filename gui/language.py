import json
from enum import Enum

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QWidget

import gui.img.icon
from gui.component import Label
from util.path import to_abs_path


class Language(Enum):
    ENGLISH = 0
    CHINESE = 1


class LanguageWidget(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._layout = QHBoxLayout()
        self.setLayout(self._layout)

        self.combox = LanguageComboBox()
        self._layout.addWidget(Label("Language"))
        self._layout.addWidget(self.combox, alignment=Qt.AlignLeft)
        # This sufficiently large stretch makes the combobox stick to the label
        # no matter how the window is streched in width.
        self._layout.setStretch(1, 15)

    def change_language(self, lang: Language) -> None:
        lang_file = to_abs_path(f"./gui/lang/{lang.name.lower()}.json")
        with open(lang_file, mode="r", encoding="utf-8") as f:
            lang_map = json.load(f)[type(self).__name__]

        self._layout.itemAt(0).widget().setText(lang_map["title"])
        for lang_ in Language:
            self.combox.setItemText(lang_.value, lang_map[lang_.name.lower()])


class LanguageComboBox(QComboBox):
    def __init__(self) -> None:
        super().__init__()
        self.setFont(QFont("Arial", 12))
        self._add_languages()

    def _add_languages(self) -> None:
        # have the order match the value of enum Language
        self.addItem(QIcon(":us-flag.ico"), Language.ENGLISH.name.capitalize())
        self.addItem(QIcon(":taiwan-flag.ico"), Language.CHINESE.name.capitalize())

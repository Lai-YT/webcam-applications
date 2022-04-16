import json

from PyQt5.QtCore import QRegExp, Qt
from PyQt5.QtGui import QFont, QIcon, QRegExpValidator
from PyQt5.QtWidgets import QComboBox, QGridLayout, QWidget

import gui.img.icon
from gui.component import Label, LineEdit
from gui.language import Language
from util.path import to_abs_path


class ConfigWidget(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._layout = QGridLayout()
        self.setLayout(self._layout)

        self._create_configs()

    def _create_configs(self) -> None:
        self._create_student_id_line()
        self._create_language_combox()
        # This sufficiently large stretch makes the field stick to the label
        # no matter how the window is streched in width.
        self._layout.setColumnStretch(1, 10)

    def _create_student_id_line(self) -> None:
        self.id = LineEdit("enter your student id")
        # 1 ~ 10 digits, uppercase letter and numbers are allowed
        self.id.setValidator(QRegExpValidator(QRegExp(r"^[A-Z0-9]+$")))
        self.id.setMaxLength(10)
        self._layout.addWidget(Label("Id:"), 0, 0)
        self._layout.addWidget(self.id, 0, 1, alignment=Qt.AlignLeft)

    def _create_language_combox(self) -> None:
        self.combox = LanguageComboBox()
        self._layout.addWidget(Label("Language:"), 1, 0)
        self._layout.addWidget(self.combox, 1, 1, alignment=Qt.AlignLeft)

    def change_language(self, lang: Language) -> None:
        lang_file = to_abs_path(f"./gui/lang/{lang.name.lower()}.json")
        with open(lang_file, mode="r", encoding="utf-8") as f:
            lang_map = json.load(f)[type(self).__name__]

        self._layout.itemAtPosition(0, 0).widget().setText(lang_map["id"])
        self.id.setPlaceholderText(lang_map["id_hint"])
        self._layout.itemAtPosition(1, 0).widget().setText(lang_map["language"])
        for lang_ in Language:
            self.combox.setItemText(lang_.value, lang_map[lang_.name.lower()])


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

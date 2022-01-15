import unittest
from typing import List

from PyQt5.QtCore import QObject, pyqtSignal


class SignalSender(QObject):
    signal = pyqtSignal(str)

    def send(self, content: str) -> None:
        self.signal.emit(content)


class PyQtSignalTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.sender = SignalSender()

    def test_signal_order(self) -> None:
        """Tests whether the order of signals changes under massive emits."""
        contents: List[str] = []
        self.sender.signal.connect(contents.append)

        for _ in range(1_000_000):
            self.sender.send("0")
            self.sender.send("1")
            self.sender.send("0")
            self.sender.send("1")

        for i in range(1_000_000):
            self.assertEqual(contents[i*4:(i+1)*4], ["0", "1", "0", "1"])


if __name__ == "__main__":
    unittest.main()

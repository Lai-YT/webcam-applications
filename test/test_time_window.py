import time
import unittest

from lib.sliding_window import TimeWindow


class TimeWindowTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.time_window = TimeWindow(60)

    def test_str(self) -> None:
        self.assertEqual(str(self.time_window), "TimeWindow([])")

    def test_append_time_not_exceed(self) -> None:
        times = []
        for i in range(50):
            self.time_window.append_time()
            times.append(int(time.time()))
            time.sleep(1)
        self.assertLessEqual(abs(self.time_window.front - times[0]), 1)
        self.assertLessEqual(abs(self.time_window.back - times[-1]), 1)
        self.assertEqual(len(self.time_window), len(times))

    def test_append_time_exceed(self) -> None:
        times = []
        for _ in range(5):
            self.time_window.append_time()
            times.append(int(time.time()))
            time.sleep(25)
            if len(times) > 3:
                times.pop(0)
            self.assertLessEqual(abs(self.time_window.front - times[0]), 1)
            self.assertLessEqual(abs(self.time_window.back - times[-1]), 1)

    def test_empty_error(self) -> None:
        with self.assertRaises(IndexError):
            self.time_window.front
        with self.assertRaises(IndexError):
            self.time_window.back

    def test_clear(self) -> None:
        for _ in range(4):
            self.time_window.append_time()
        self.time_window.clear()
        self.assertEqual(str(self.time_window), "TimeWindow([])")
        self.assertEqual(len(self.time_window), 0)


if __name__ == "__main__":
    unittest.main()

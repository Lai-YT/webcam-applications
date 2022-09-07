import time
import unittest

from util.time_window import DoubleTimeWindow, TimeWindow, WindowType
from util.time import now


class TimeWindowTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.time_window = TimeWindow(60)

    def test_str(self) -> None:
        self.assertEqual(str(self.time_window), "TimeWindow([])")

    def test_append_time_not_exceed(self) -> None:
        times = []
        for _ in range(50):
            self.time_window.append_time()
            times.append(now())
            time.sleep(1)

        self.assertEqual(len(self.time_window), len(times))
        for t, ans_t in zip(times, self.time_window.times()):
            self.assertLessEqual(abs(t - ans_t), 1)

    def test_append_time_exceed(self) -> None:
        times = []
        for _ in range(5):
            self.time_window.append_time()
            times.append(now())
            time.sleep(25)
            if len(times) > 3:
                times.pop(0)
            for t, ans_t in zip(times, self.time_window.times()):
                self.assertLessEqual(abs(t - ans_t), 1)

    def test_time_catch_callback(self) -> None:
        length_count = 0
        self.time_window.set_time_catch_callback(
            lambda: self.assertEqual(len(self.time_window), length_count)
        )
        while length_count != 5:
            length_count += 1
            self.time_window.append_time()

    def test_clear(self) -> None:
        for _ in range(4):
            self.time_window.append_time()
        self.time_window.clear()
        self.assertEqual(str(self.time_window), "TimeWindow([])")
        self.assertEqual(len(self.time_window), 0)


class DoubleTimeWindowTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.time_window = DoubleTimeWindow(60)

    def test_str(self) -> None:
        self.assertEqual(str(self.time_window), "DoubleTimeWindow{previous([]), ([])}")

    def test_len(self) -> None:
        for _ in range(16):
            self.time_window.append_time()
            time.sleep(4.5)

        self.assertEqual(len(self.time_window), 16)
        self.assertEqual(len(self.time_window.prev_times()), 2)

    def test_append_time_not_exceed(self) -> None:
        times = []
        for _ in range(50):
            self.time_window.append_time()
            times.append(now())
            time.sleep(1)

        self.assertEqual(len(self.time_window), len(times))
        for t, ans_t in zip(times, self.time_window.times()):
            self.assertLessEqual(abs(t - ans_t), 1)

    def test_append_time_exceed(self) -> None:
        times = []
        sep_pos = 0
        for _ in range(16):
            self.time_window.append_time()
            times.append(now())
            time.sleep(4.5)
            if len(times) - sep_pos > 14:
                sep_pos += 1
            for t, ans_t in zip(times[sep_pos:], self.time_window.times()):
                self.assertLessEqual(abs(t - ans_t), 1)
            for t, ans_t in zip(times[:sep_pos], self.time_window.prev_times()):
                self.assertLessEqual(abs(t - ans_t), 1)

    def test_time_catch_callback(self) -> None:
        length_count = 0
        self.time_window.set_time_catch_callback(
            lambda: self.assertEqual(len(self.time_window), length_count)
        )
        while length_count != 5:
            length_count += 1
            self.time_window.append_time()

    def test_clear_individual(self) -> None:
        for _ in range(16):
            self.time_window.append_time()
            time.sleep(4.5)

        self.time_window.clear(WindowType.PREVIOUS)
        self.assertEqual(len(self.time_window), 14)

        self.time_window.clear(WindowType.CURRENT)
        self.assertEqual(len(self.time_window), 0)

    def test_clear_both(self) -> None:
        for _ in range(16):
            self.time_window.append_time()
            time.sleep(4.5)

        self.time_window.clear()
        self.assertEqual(len(self.time_window), 0)


if __name__ == "__main__":
    unittest.main()

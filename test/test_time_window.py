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

        self.assertEqual(len(self.time_window), len(times))
        for t, ans_t in zip(times, self.time_window):
            self.assertLessEqual(abs(t - ans_t), 1)

    def test_append_time_exceed(self) -> None:
        times = []
        for _ in range(5):
            self.time_window.append_time()
            times.append(int(time.time()))
            time.sleep(25)
            if len(times) > 3:
                times.pop(0)
            for t, ans_t in zip(times, self.time_window):
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


if __name__ == "__main__":
    unittest.main()

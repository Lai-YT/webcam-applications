import unittest

from concentration.fuzzy.parse import read_intervals_from_json
from concentration.grader import ConcentrationGrader
from util.path import to_abs_path
from util.time import Timer


class ConcentrationGraderTestCase(unittest.TestCase):
    JSON_FILE = to_abs_path("intervals.json")

    def setUp(self) -> None:
        """Sets up a concentration grader as the testing target and a timer for
        the manual adds.
        """
        self.grader = ConcentrationGrader()
        self.timer = Timer()

    def test_racing_between_low_face_and_blink(self) -> None:
        """Test whether low existence is checked first.

        Even though the blink is add first, low face existence check should
        prior to the normal one; otherwise you'll have the interval good due to
        the normal fuzzy grade.

        Scenario:
        A single minute with
            blink: 1     per 7 secs,
            body:  0.67  instantaneously,
            face:  0     instantaneously.

        Expected Result:
        A 60 seconds interval with grade 0.67, which is the grade of body.

        Notice that this test may be false-positive since the emission order
        various and is uncontrollable.
        """
        delays = [7 for i in range(9)]  # The delay between blinks in a minute.
        def single_test_cycle(min_no: int) -> None:
            """This is a single minute test of the racing scenario, have it
            called in subTests to reduce the false-positive condition.

            Arguments:
                min_no: The current number of the single test cycle.
            """
            # The outer loop goes for blinks, inner for face and body.
            for t, delay in enumerate(delays):
                # No matter which one (face and interval) emits first, the low
                # face should be accepted as the grade.
                self.grader._blink_detector.s_blinked.emit()

                i = 0
                self.timer.start()
                while self.timer.time() < delay:
                    self.grader.add_frame()
                    if i % 3:
                        self.grader.add_body_concentration()
                    else:
                        self.grader.add_body_distraction()
                    i = (i + 1) % 3
                self.timer.reset()

                self.grader._interval_detector.check_blink_rate()
            # The grade should be 0.67, not 0.83.
            intervals = read_intervals_from_json(self.JSON_FILE)
            self.assertEqual(len(intervals), min_no)

            interval = intervals[min_no - 1]
            self.assertEqual(interval.end - interval.start, 60)
            self.assertAlmostEqual(interval.grade, 0.67, places=2,
                                   msg="Should use the grade of body in a low face interval.")

        for min_no in range(1, 4):
            with self.subTest(min_no=min_no):
                single_test_cycle(min_no)

    def test_grading_continuity_of_previous(self) -> None:
        """The grading on previous should be right after the next interval.

        The look-up mechanism should fill the bad interval "right before" the
        good 60 seconds interval.

        Scenario:
        The 1st minute with
            blink: 1     per 7 secs,
            body:  0     instantaneously,
            face:  1     instantaneously,
        to provide low grade.
        The 2nd minute with
            blink: 1     per 7 secs,
            body:  0.8   instantaneously,
            face:  1     instantaneously.

        Expected Result:
        So we'll have the
            1st 35s: 0.47 (blink 5 extend to 8, body 0),
            2nd 60s: 0.61 (blink 9, body 0.45).
            The last 25s provides no interval.
        """
        delays = [7 for i in range(18)]
        for t, delay in enumerate(delays):
            self.grader._blink_detector.s_blinked.emit()

            self.timer.start()
            if t < 9:  # 1st min
                while self.timer.time() < delay:
                    self.grader.add_frame()
                    self.grader.add_face()
                    self.grader.add_body_distraction()
            else:  # last min
                i = 0
                while self.timer.time() < delay:
                    self.grader.add_frame()
                    self.grader.add_face()

                    if i % 5:
                        self.grader.add_body_concentration()
                    else:
                        self.grader.add_body_distraction()
                    i = (i + 1) % 5
            self.timer.reset()

        intervals = read_intervals_from_json(self.JSON_FILE)
        self.assertEqual(len(intervals), 2)

        first_interval, second_interval = intervals

        self.assertEqual(first_interval.end - first_interval.start, 35)
        self.assertAlmostEqual(first_interval.grade, 0.47, places=2)
        # We want the intervals to be concatenated.
        self.assertEqual(second_interval.start, first_interval.end,
                         msg="The intervals should be continuous.")

        self.assertEqual(second_interval.end - second_interval.start, 60)
        self.assertAlmostEqual(second_interval.grade, 0.61, places=2)

    def test_grading_interval_width_of_previous(self) -> None:
        """The grading on previous should be as long as possible.

        Grading of the previous window should also be blocked when the
        "likely" good interval nearby isn't a truly good interval;
        seeking for a 60 seconds interval if possible.

        Scenario:
        A leading 30 seconds with
            blink: 1    per 6 secs,
            body:  0    instantaneously,
            face:  1    instantaneously,
        """
        pass
        
    # def test_two_min_low_face(self) -> None:
    #     """
    #     Scenario:
    #     The 1st minute are with
    #         blink: 1     per 7 secs,
    #         body:  0.66  instantaneously,
    #         face:  0     instantaneously.
    #     To provide low face existence.
    #     The 2nd minute are with
    #         blink: 1     per 7 secs,
    #         body:  0     instantaneously,
    #         face:  1     instantaneously.
    #     To provide low grade.
    #     The 3rd minute comes with
    #         blink: 1     per 7 secs,
    #         body:  0.8   instantaneously,
    #         face:  1     instantaneously.
    #
    #     Expected Result:
    #     So we'll have the
    #         1st 60s: 0.66 (blink 9, body 0.66, low face),
    #         2nd 34s: 0.83 (blink 4 extend to 8, body 0.66),
    #         3rd 60s: 0.6  (blink 9, body 0.45).
    #         The last 26s provides no interval, so it's removed to save time.
    #     """
    #     delays = [7 for i in range(23)]
    #     for t, delay in enumerate(delays):
    #         # Notice that even though the blink is add first,
    #         # low face existence check should prior to the normal one.
    #         # If not, you'll have the 1st min good due to the normal fuzzy grade.
    #         self.grader._blink_detector.s_blinked.emit()
    #
    #         self.timer.start()
    #         if t < 9:  # 1st min
    #             i = 0
    #             while self.timer.time() < delay:
    #                 self.grader.add_frame()
    #                 if i % 3:
    #                     self.grader.add_body_concentration()
    #                 else:
    #                     self.grader.add_body_distraction()
    #                 i = (i + 1) % 3
    #         elif t < 18:  # 2nd min
    #             while self.timer.time() < delay:
    #                 self.grader.add_frame()
    #                 self.grader.add_face()
    #                 self.grader.add_body_distraction()
    #         elif t < 23:  # last min
    #             i = 0
    #             while self.timer.time() < delay:
    #                 self.grader.add_frame()
    #                 if i % 5:
    #                     self.grader.add_body_concentration()
    #                 else:
    #                     self.grader.add_body_distraction()
    #                 i = (i + 1) % 5
    #         else:
    #             raise ValueError(f"unexpected time: {t * 7}")
    #         self.timer.reset()

    # def test_two_min_body_distraction(self) -> None:
    #     delays = [7 for i in range(20)]
    #     for i, delay in enumerate(delays):
    #         grader._blink_detector.s_blinked.emit()
    #
    #         odd = False
    #         timer.start()
    #         while timer.time() < delay:
    #             grader.add_frame()
    #             grader.add_face()
    #             if odd:
    #                 grader.add_body_distraction()
    #             else:
    #                 grader.add_body_concentration()
    #             grader.add_body_distraction()
    #             odd = not odd
    #         timer.reset()


if __name__ == "__main__":
    unittest.main()
import unittest

from lib.concentration_grader import ConcentrationGrader


class ConcentrationGraderTestCase(unittest.TestCase):
    def setUp(self):
        self.grader = ConcentrationGrader()

    def test_full_concentration(self):
        for _ in range(10):
            self.grader.increase_concentration()
            self.assertAlmostEqual(1.0, self.grader.get_grade(), places=2)

    def test_half_concentration(self):
        """Counts 10 times from 1 to 9, increase concentration if odd, otherwise distraction."""
        
        answers = [1/1, 1/2, 2/3, 2/4, 3/5, 3/6, 4/7, 4/8, 5/9]
        for i, ans in zip(range(1, 10), answers):
            if i % 2:
                self.grader.increase_concentration()
            else:
                self.grader.increase_distraction()

            self.assertAlmostEqual(ans, self.grader.get_grade(), places=2)

    def test_no_increase(self):
        self.assertAlmostEqual(1.0, self.grader.get_grade(), places=2)


if __name__ == "__main__":
    unittest.main()

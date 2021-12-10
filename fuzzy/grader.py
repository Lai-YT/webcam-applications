# Please read the example of tipping problem before playing with this file.
# https://pythonhosted.org/scikit-fuzzy/auto_examples/plot_tipping_problem_newapi.html

from typing import List, Tuple

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


class FuzzyGrader:
    """A fuzzy-based grader which takes blink rate and body concentration value
    into consideration.
    """
    def __init__(self) ->  None:
        self._create_membership_func_of_blink()
        self._create_membership_func_of_body()
        self._create_membership_func_of_grade()

        rules: List[ctrl.Rule] = self._create_fuzzy_rules()
        self._grader = ctrl.ControlSystemSimulation(ctrl.ControlSystem(rules))

    def compute_grade(self, blink_rate: int, body_concent: float, *, normalized=True) -> float:
        """Computes the grade base on fuzzy logics.

        The grade is rounded to two decimal places.
        Arguments:
            blink_rate: The blink rate, which should be in range [0, 21].
            blink_concent: The body concentration value, which should be in range [0, 1].
            normalized: Normalize the grade into [0, 1] or not. True in default.
        """
        self._grader.input["blink"] = FuzzyGrader._map_blink_rate_to_membership_value(blink_rate)
        self._grader.input["body"] = FuzzyGrader._map_body_concent_to_membership_value(body_concent)
        self._grader.compute()

        grade: float = self._grader.output["grade"]
        if normalized:
            grade = FuzzyGrader._to_normalized_grade(grade)
        return round(grade, 2)

    def view(self) -> None:
        """Plots the membership function of blink rate, blink concentration value
        and unnormalized grade.
        """
        self._blink.view()
        self._body.view()
        self._grade.view()

    def _create_membership_func_of_blink(self) -> None:
        self._blink = ctrl.Antecedent(np.arange(22), "blink")
        self._blink["good"] = fuzz.trapmf(self._blink.universe, [0, 0, 8, 15])
        self._blink["average"] = fuzz.trimf(self._blink.universe, [8, 15, 21])
        self._blink["poor"] = fuzz.trimf(self._blink.universe, [15, 21, 21])

    def _create_membership_func_of_body(self) -> None:
        # The greater the values is, the better the grade of body concentration is,
        # so we simply use .automf(3) to generate equally-divided triangular membership
        # function.
        self._body = ctrl.Antecedent(np.arange(11), "body")
        self._body.automf(3)

    def _create_membership_func_of_grade(self) -> None:
        self._grade = ctrl.Consequent(np.arange(11), "grade")
        # a trapezoidal part is used to slightly pull up the intermediate group
        self._grade["high"] = fuzz.trapmf(self._grade.universe, [5, 8, 10, 10])
        self._grade["medium"] = fuzz.trimf(self._grade.universe, [0, 5, 8])
        self._grade["low"] = fuzz.trimf(self._grade.universe, [0, 0, 5])

    def _create_fuzzy_rules(self) -> List[ctrl.Rule]:
        """Returns the fuzzy rule that control the grade."""
        rule1 = ctrl.Rule(self._blink["poor"] | self._body["poor"], self._grade["low"])
        rule2 = ctrl.Rule(self._blink["average"] | self._body["average"], self._grade["medium"])
        rule3 = ctrl.Rule(self._blink["good"] | self._body["good"], self._grade["high"])
        return [rule1, rule2, rule3]

    @staticmethod
    def _map_blink_rate_to_membership_value(blink_rate: int) -> int:
        """Returns the membership value of the blink rate.

        Arguments:
            blink_rate
        """
        # they're equivalent
        return blink_rate

    # The body concentration (BC) sent by the ConcentrationGrader is between 0 and 1,
    # maps them to the membership values (MV) through an easy function: MV = BC * 10
    # since skfuzzy does better on generating membership functions with non-floating
    # point intervals.
    @staticmethod
    def _map_body_concent_to_membership_value(body_concent: float) -> float:
        """Returns the membership value of the body concentration.

        Arguments:
            body_concent
        """
        return body_concent * 10

    @staticmethod
    def _to_normalized_grade(raw_grade: float) -> float:
        """Normalizes the grade interval to [0, 1].

        Normalized grade is rounded to two decimal places.
        Arguments:
            raw_grade: The unnormalized grade in [1.67, 8.14].
        """
        # Raw grade interval is (1.67, 8.14), we expand the grade interval to (0, 10)
        # first, then normalize it.
        normalized_grade = 1.55 * (raw_grade - 1.67)
        return round(normalized_grade / 10, 2)


if __name__ == "__main__":
    fuzzy_grader = FuzzyGrader()
    fuzzy_grader.view()
    # go for a single graph check
    blink_rate = int(input("blink rate: "))
    body_concent = float(input("body concent: "))
    raw_grade: float = fuzzy_grader.compute_grade(blink_rate, body_concent,
                                                  normalized=False)
    norm_grade: float = fuzzy_grader.compute_grade(blink_rate, body_concent)
    print(f"raw: {raw_grade}")
    print(f"grade: {norm_grade}")

    # grade.view(sim=grading)

    input("(press any key to exit)")

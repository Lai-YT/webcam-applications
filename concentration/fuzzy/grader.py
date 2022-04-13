# Please read the example of tipping problem before playing with this file.
# https://pythonhosted.org/scikit-fuzzy/auto_examples/plot_tipping_problem_newapi.html

from typing import List

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
        self._create_membership_func_of_center()
        self._create_membership_func_of_grade()

        rules: List[ctrl.Rule] = self._create_fuzzy_rules()
        self._grader = ctrl.ControlSystemSimulation(ctrl.ControlSystem(rules))

    def compute_grade(
            self,
            blink_rate: float,
            body_concent: float,
            center_dist: float,
            *, normalized: bool = True) -> float:
        """Computes the grade base on fuzzy logics.

        The grade is rounded to two decimal places.

        Arguments:
            blink_rate: The blink rate, which should be in range [0, 21].
            blink_concent: The body concentration value, which should be in range [0, 1].
            normalized: Normalize the grade into [0, 1] or not. True in default.
        """
        self._grader.input["blink"] = FuzzyGrader._map_blink_rate_to_membership_value(blink_rate)
        self._grader.input["body"] = FuzzyGrader._map_body_concent_to_membership_value(body_concent)
        self._grader.input["center"] = center_dist
        self._grader.compute()

        grade: float = self._grader.output["grade"]
        if normalized:
            grade = FuzzyGrader._to_modified_grade(grade)
        # if grade < 0.3:
        #     print(grade, blink_rate, body_concent, center_dist)
        return round(grade, 2)

    def view_membership_func(self) -> None:
        """Plots the membership function of blink rate, blink concentration
        value and unnormalized grade.
        """
        self._blink.view()
        self._body.view()
        self._center.view()
        self._grade.view()

    def view_grading_result(self) -> None:
        self._grade.view(sim=self._grader)

    def _create_membership_func_of_blink(self) -> None:
        self._blink = ctrl.Antecedent(np.arange(22), "blink")
        self._blink["good"] = fuzz.trapmf(self._blink.universe, [0, 0, 8, 15])
        self._blink["average"] = fuzz.trimf(self._blink.universe, [8, 15, 21])
        self._blink["poor"] = fuzz.trimf(self._blink.universe, [15, 21, 21])

    def _create_membership_func_of_body(self) -> None:
        # The greater the values is, the better the grade of body concentration is.
        self._body = ctrl.Antecedent(np.arange(11), "body")
        self._body["good"] = fuzz.trimf(self._body.universe, [0, 10, 10])
        self._body["poor"] = fuzz.trimf(self._body.universe, [0, 0, 10])

    def _create_membership_func_of_center(self) -> None:
        """Only takes the distance betweeen centers into consideration."""
        self._center = ctrl.Antecedent(np.arange(61), "center")
        self._center["good"] = fuzz.trapmf(self._center.universe, [0, 0, 5, 10])
        self._center["average"] = fuzz.trapmf(self._center.universe, [5, 10, 15, 40])
        self._center["poor"] = fuzz.trapmf(self._center.universe, [15, 40, 60, 60])

    def _create_membership_func_of_grade(self, defuzzify_method: str = "centroid") -> None:
        """
        Arguments:
            defuzzify_method:
                Controls which defuzzification method will be used.
                There are 5 methods to choose
                    centroid (default): centroid of area
                    bisector: bisector of area
                    mom: mean of maximum
                    som: min of maximum
                    lom: max of maximum
        """
        self._grade = ctrl.Consequent(np.arange(11), "grade")
        self._grade.defuzzify_method = defuzzify_method

        self._grade["high"] = fuzz.trimf(self._grade.universe, [6, 10, 10])
        self._grade["medium"] = fuzz.trimf(self._grade.universe, [0, 6, 10])
        self._grade["low"] = fuzz.trimf(self._grade.universe, [0, 0, 6])

    def _create_fuzzy_rules(self) -> List[ctrl.Rule]:
        """Returns the fuzzy rule that control the grade."""
        rule1 = ctrl.Rule(self._center["poor"] | self._body["poor"] | self._blink["poor"], self._grade["low"])
        rule2 = ctrl.Rule(self._blink["average"] | self._center["average"], self._grade["medium"])
        rule3 = ctrl.Rule(self._center["good"] & self._body["good"] & ~self._blink["poor"], self._grade["high"])
        return [rule1, rule2, rule3]

    @staticmethod
    def _map_blink_rate_to_membership_value(blink_rate: float) -> float:
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
    def _to_modified_grade(raw_grade: float) -> float:
        return 0.1499 * raw_grade - 0.2999
        # """Normalizes the grade interval to [0, 1] and do linear modification
        #    to fine-tune the grade distribution.
        #
        # Modified grade is rounded to two decimal places.
        #
        # Arguments:
        #     raw_grade: The unnormalized grade in [2, 6].
        # """
        # normalized_grade = (raw_grade - 2) / 4
        #
        # if normalized_grade > 0.75:
        #     modified_grade = 0.6 + (normalized_grade - 0.75) * (0.4 / 0.25)
        # else:
        #     modified_grade = normalized_grade * (0.6 / 0.75)
        #
        # return round(modified_grade, 2)


if __name__ == "__main__":
    fuzzy_grader = FuzzyGrader()
    # fuzzy_grader.view_membership_func()

    import matplotlib.pyplot as plt
    import numpy as np

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    x, y, z, c = [], [], [], []
    for blink_rate in np.arange(0, 20):
        for body_concent in np.linspace(0.2, 1, num=8):
            for center_dist in np.linspace(0, 60, num=60):
                x.append(blink_rate)
                y.append(body_concent)
                z.append(center_dist)
                c.append(fuzzy_grader.compute_grade(blink_rate, body_concent, center_dist))
    ax.set_xlabel("blink")
    ax.set_ylabel("body")
    ax.set_zlabel("center")

    img = ax.scatter(x, y, z, c=c, cmap=plt.hot(), vmin=0, vmax=1)
    fig.colorbar(img)
    plt.show()
    # # go for a single graph check
    # blink_rate = float(input("blink rate: "))
    # body_concent = float(input("body concent: "))
    # center_dist = float(input("center dist: "))
    # raw_grade: float = fuzzy_grader.compute_grade(blink_rate, body_concent, center_dist,
    #                                               normalized=False)
    # norm_grade: float = fuzzy_grader.compute_grade(blink_rate, body_concent, center_dist)
    # print(f"raw: {raw_grade}")
    # print(f"grade: {norm_grade}")
    #
    # fuzzy_grader.view_grading_result()
    #
    # input("(press any key to exit)")

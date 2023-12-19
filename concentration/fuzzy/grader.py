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

    def __init__(self) -> None:
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
        center_value: float,
        *,
        normalized: bool = True,
    ) -> float:
        """Computes the grade base on fuzzy logics.

        The grade is rounded to two decimal places.

        Arguments:
            blink_rate: The blink rate, which should be in range [0, 21].
            blink_concent: The body concentration value, which should be in range [0, 1].
            center_value: The face center value, which should be in range [0, 1].
            normalized: Normalize the grade into [0, 1] or not. True in default.
        """
        self._grader.input["blink"] = blink_rate
        self._grader.input["body"] = body_concent
        self._grader.input["center"] = center_value
        self._grader.compute()

        grade: float = self._grader.output["grade"]
        if normalized:
            grade = FuzzyGrader._normalize_grade(grade)
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
        self._body = ctrl.Antecedent(np.arange(2), "body")
        self._body["good"] = fuzz.trimf(self._body.universe, [0, 1, 1])
        self._body["poor"] = fuzz.trimf(self._body.universe, [0, 0, 1])

    def _create_membership_func_of_center(self) -> None:
        self._center = ctrl.Antecedent(np.arange(0, 1, 0.01), "center")
        self._center["good"] = fuzz.trapmf(self._center.universe, [0, 0, 0.2, 0.27])
        self._center["average"] = fuzz.trapmf(
            self._center.universe, [0.2, 0.27, 0.34, 0.67]
        )
        self._center["poor"] = fuzz.trapmf(self._center.universe, [0.34, 0.67, 1, 1])

    def _create_membership_func_of_grade(
        self, defuzzify_method: str = "centroid"
    ) -> None:
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
        """Returns the fuzzy rule that controls the grade."""
        rule1 = ctrl.Rule(
            # at least two poors to lead to poor
            antecedent=(self._blink["poor"] & self._body["poor"])
            | (self._body["poor"] & self._center["poor"])
            | (self._center["poor"] & self._blink["poor"]),
            consequent=self._grade["low"],
        )
        rule2 = ctrl.Rule(
            # medium if not all good
            antecedent=~(
                self._blink["good"] & self._body["good"] & self._center["good"]
            ),
            consequent=self._grade["medium"],
        )
        rule3 = ctrl.Rule(
            # two goods are sufficient for a high grade
            # NOTE: blink is a loose constraint, good & average is both enough
            antecedent=(~self._blink["poor"] & self._body["good"])
            | (self._body["good"] & self._center["good"])
            | (self._center["good"] & ~self._blink["poor"]),
            consequent=self._grade["high"],
        )
        return [rule1, rule2, rule3]

    @staticmethod
    def _normalize_grade(raw_grade: float) -> float:
        """Normalizes the raw grade into [0, 1].

        The lowest possible raw grade 4.33 is expanded to 0.4 (not 0), and
        the highest 8.67 is expanded to 1.
        """
        # The advantage over expanding both sides to 0 and 1 is that since
        # there's always a gap between the lowest raw grade and 0, the expansion
        # on the lower side pulls down relatively high grades.
        # For example, blink 5, body 0.8 and center 0.2 is a good combination
        # with raw grade 6.77, but has only 0.56 after normalization if we do
        # expansion on both sides; 0.74 when expansion only on higher side,
        # which better shows the concentration.
        return 0.1382 * raw_grade - 0.1986


# The following code is not necessary for the grading system.
# It is included for interactive visualization purposes.

import argparse
from enum import Enum, auto, unique

import matplotlib.pyplot as plt


@unique
class _InteractiveMode(Enum):
    MEMBERSHIP = auto()
    DISTRIBUTION = auto()
    DISTRIBUTION_SLICE = auto()
    INPUT = auto()


def interact(mode: _InteractiveMode) -> None:
    fuzzy_grader = FuzzyGrader()

    if mode is _InteractiveMode.MEMBERSHIP:
        fuzzy_grader.view_membership_func()
        input("(press any key to exit)")
    elif mode is _InteractiveMode.DISTRIBUTION:
        # show distribution over all possible values, which makes the plot 4D
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")

        x, y, z, c = [], [], [], []
        for blink_rate in np.arange(0, 20):
            for body_concent in np.linspace(0, 1, num=20):
                for center_value in np.linspace(0, 1, num=20):
                    x.append(blink_rate)
                    y.append(body_concent)
                    z.append(center_value)
                    c.append(
                        fuzzy_grader.compute_grade(
                            blink_rate, body_concent, center_value
                        )
                    )
        ax.set_xlabel("blink")
        ax.set_ylabel("body")
        ax.set_zlabel("center")

        img = ax.scatter(x, y, z, c=c, cmap=plt.hot())
        fig.colorbar(img)
        plt.show()
    elif mode is _InteractiveMode.DISTRIBUTION_SLICE:
        # show distribution under specific blink rate, which makes the plot 3D
        fixed_blink_rate = int(input("fixed blink rate: "))

        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        x, y, z = [], [], []
        for body_concent in np.linspace(0, 1, num=20):
            for center_value in np.linspace(0, 1, num=20):
                x.append(body_concent)
                y.append(center_value)
                z.append(
                    fuzzy_grader.compute_grade(
                        fixed_blink_rate, body_concent, center_value
                    )
                )
        ax.set_xlabel("body")
        ax.set_ylabel("center")
        ax.set_zlabel("grade")

        img = ax.scatter(x, y, z)
        plt.show()
    elif mode is _InteractiveMode.INPUT:
        # compute for a single case of grade
        blink_rate = float(input("blink rate: "))
        body_concent = float(input("body concent: "))
        center_value = float(input("center value: "))
        raw_grade: float = fuzzy_grader.compute_grade(
            blink_rate, body_concent, center_value, normalized=False
        )
        norm_grade: float = fuzzy_grader.compute_grade(
            blink_rate, body_concent, center_value
        )
        print(f"raw: {raw_grade}")
        print(f"grade: {norm_grade}")

        fuzzy_grader.view_grading_result()
        input("(press any key to exit)")
    else:
        raise NotImplementedError(f"unknown mode {mode}")


def main() -> None:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "mode",
        metavar="MODE",
        choices=[mode for mode in _InteractiveMode],
        type=lambda x: _InteractiveMode[x.upper()],
        help="interactive modes: membership, distribution, distribution_slice, input",
    )
    args: argparse.Namespace = parser.parse_args()

    interact(args.mode)


if __name__ == "__main__":
    main()

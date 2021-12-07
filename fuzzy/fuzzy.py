# Please read the example of tipping problem before playing with this file.
# https://pythonhosted.org/scikit-fuzzy/auto_examples/plot_tipping_problem_newapi.html

from typing import List, Tuple

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


blink = ctrl.Antecedent(np.arange(22), "blink")
blink["good"] = fuzz.trapmf(blink.universe, [0, 0, 8, 15])
blink["average"] = fuzz.trimf(blink.universe, [8, 15, 21])
blink["poor"] = fuzz.trimf(blink.universe, [15, 21, 21])


def map_blink_rate_to_membership_value(blink_rate: int) -> int:
    """Returns the membership value of the blink rate."""
    # there equivalent
    return blink_rate

# The body concentration (BC) sent by the ConcentrationGrader is between 0 and 1,
# maps them to the membership values (MV) through an easy function: MV = BC * 10
# since skfuzzy does better on generating membership functions with non-floating
# point intervals.
# The greater the values is, the better the grade of body concentration is,
# so we simply use .automf(3) to generate equally-divided triangular membership
# function.
body = ctrl.Antecedent(np.arange(11), "body")
body.automf(3)

def map_body_concent_to_membership_value(body_concent: float) -> float:
    """Returns the membership value of the body concentration."""
    return body_concent * 10


grade = ctrl.Consequent(np.arange(11), "grade")
# a trapezoidal part is used to slightly pull up the intermediate group
grade["high"] = fuzz.trapmf(grade.universe, [5, 8, 10, 10])
grade["medium"] = fuzz.trimf(grade.universe, [0, 5, 8])
grade["low"] = fuzz.trimf(grade.universe, [0, 0, 5])


rule1 = ctrl.Rule(body["poor"] | blink["poor"], grade["low"])
rule2 = ctrl.Rule(blink["average"], grade["medium"])
rule3 = ctrl.Rule(blink["good"] | body["good"], grade["high"])

grading_ctrl = ctrl.ControlSystem([rule1, rule2, rule3])
grading = ctrl.ControlSystemSimulation(grading_ctrl)

def to_normalized_grade(raw_grade: float) -> float:
    """Normalizes the grade interval to [0, 1].

    Normalized grade is rounded to two decimal places.
    Arguments:
        raw_grade: The unnormalized grade in [3.49, 8.14].
    """
    # Raw grade interval is (1.67, 8.14), we expand the grade interval to (0, 10)
    # first, then normalize it.
    normalized_grade = 1.55 * (raw_grade - 1.67)
    return round(normalized_grade / 10, 2)


def compute_grade(blink_rate: int, body_concent: float) -> float:
    grading.input["blink"] = map_blink_rate_to_membership_value(blink_rate)
    grading.input["body"] = map_body_concent_to_membership_value(body_concent)
    grading.compute()

    return to_normalized_grade(grading.output["grade"])

def output_fuzzy_grades() -> None:
    # grade, blink rate, body concent
    concent_grades: List[Tuple[float, int, float]] = []
    for blink_rate in range(22):
        for body_value in range(11):
            blink_value: int = map_blink_rate_to_membership_value(blink_rate)
            grading.input["blink"] = blink_value
            grading.input["body"] = body_value
            grading.compute()

            concent_grades.append(
                (to_normalized_grade(grading.output["grade"]), blink_rate, body_value/10)
            )


    with open("fuzzy_grades.txt", mode="w+") as f:
        for grade, blink, body in concent_grades:
            f.write(f"{blink}\n"
                    + f"{body}\n"
                    + f"{grade}\n"
                    + "---\n")


if __name__ == "__main__":
    # if input("Output fuzzy grades? (Y/N): ").lower() == "y":
        # output_fuzzy_grades()

    # blink.view()
    # body.view()
    # grade.view()

    # go for a single graph check
    grading.input["blink"] = map_blink_rate_to_membership_value(int(input("blink rate: ")))
    grading.input["body"] = map_body_concent_to_membership_value(float(input("body concent: ")))

    grading.compute()
    grade.view(sim=grading)
    raw_grade = round(grading.output["grade"], 2)
    print(f"raw_grade: {raw_grade}")
    print(f"grade: {to_normalized_grade(raw_grade):.2f}")

    input("(press any key to exit)")

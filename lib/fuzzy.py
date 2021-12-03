# Please read the example of tipping problem before playing with this file.
# https://pythonhosted.org/scikit-fuzzy/auto_examples/plot_tipping_problem_newapi.html

from typing import List, Tuple

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


# The membership value of blink rate (BR) is its absolute value of difference
# between 10, the median of the good BR rate range (5, 15).
blink = ctrl.Antecedent(np.arange(0, 16), "blink")
# There exist no poor blink since they were filtered out by
# ConcentrationGrader with GoodBlinkRateIntervalDetector.
blink["good"] = fuzz.trapmf(blink.universe, [0, 0, 5, 10])  # 1.0 good at 0 ~ 5
blink["average"] = fuzz.trapmf(blink.universe, [5, 10, 20, 20])

def map_blink_rate_to_membership_value(blink_rate: int) -> int:
    """Returns the membership value of the blink rate."""
    # 10 is the nedian of good BR interval.
    return abs(blink_rate - 10)

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


rule1 = ctrl.Rule(body["poor"], grade["low"])
rule2 = ctrl.Rule(blink["average"] | body["average"], grade["medium"])
rule3 = ctrl.Rule(blink["good"] | body["good"], grade["high"])

grading_ctrl = ctrl.ControlSystem([rule1, rule2, rule3])
grading = ctrl.ControlSystemSimulation(grading_ctrl)

def to_modified_grade(raw_grade: float) -> float:
    """Normalizes the grade interval to [0, 1].

    Modified grade is rounded to two decimal places.
    Arguments:
        raw_grade: The unmodified grade in [3.49, 8.14].
    """
    # Raw grade interval is (3.49, 8.14), we expand the grade interval to (0, 10)
    # first, then normalize it.
    modified_grade = 2.15 * (raw_grade - 3.49)
    return round(modified_grade / 10, 2)


def compute_grade(blink_rate: int, body_concent: float) -> float:
    grading.input["blink"] = map_blink_rate_to_membership_value(blink_rate)
    grading.input["body"] = map_body_concent_to_membership_value(body_concent)
    grading.compute()

    return to_modified_grade(grading.output["grade"])


def output_fuzzy_grades() -> None:
    concent_grades: List[Tuple[float, List[str]]] = []
    for blink_rate in range(1, 21):
        for body_value in range(0, 11):
            data: List[str] = []
            blink_value: int = map_blink_rate_to_membership_value(blink_rate)
            data.append(f"blink rate   = {blink_rate}, (blink value = {blink_value})")
            grading.input["blink"] = blink_value
            data.append(f"body concent = {body_value/10}, (body value = {body_value})")
            grading.input["body"] = body_value

            grading.compute()
            concent_grade: float = round(grading.output["grade"], 2)
            data.append(f"Concentration grade: {concent_grade} "
                        + f"({to_modified_grade(concent_grade):.0%})")
            concent_grades.append((concent_grade, data))


    with open("../fuzzy_grades.txt", mode="w+") as f:
        f.write("***Data are sorted by concentration grade in descending order***\n---\n")
        concent_grades.sort(reverse=True, key=lambda e: e[0])
        for concent_grade, data in concent_grades:
            f.write("\n".join(data))
            f.write("\n---\n")


if __name__ == "__main__":
    if input("Output fuzzy grades? (Y/N): ").lower() == "y":
        output_fuzzy_grades()

    blink.view()
    body.view()
    grade.view()
    # go for a single graph check
    grading.input["blink"] = map_blink_rate_to_membership_value(int(input("blink rate: ")))
    grading.input["body"] = map_body_concent_to_membership_value(float(input("body concent: ")))

    grading.compute()
    grade.view(sim=grading)
    print(f"grade: {to_modified_grade(grading.output['grade']):.2f}")

    input("(press any key to exit)")

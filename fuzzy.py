# Please read the example of tipping problem before playing with this file.
# https://pythonhosted.org/scikit-fuzzy/auto_examples/plot_tipping_problem_newapi.html

from typing import List, Tuple

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


blink = ctrl.Antecedent(np.arange(0, 16), "blink")
# There exist no poor blink since they were filtered out by
# ConcentrationGrader with GoodBlinkRateIntervalDetector.
#
# Goods:
# We take only the blink rate (BR) between 1 and 20.
# BR 5 ~ 15 are all considered as 1.0 good, which is achieved by a trapezoidal
# membership. Directly maps them to the membership value (MV) 5 ~ 15.
# Averages:
# We have BR 10 be the center. Take the difference (DF) between center and those
# not good, which are BR 1 ~ 4 and 16 ~ 20.
# The possible values of DF are 6 ~ 10, 5 values in total. We map them to the
# remaining MVs. The greater the DF is, the more average the BR is.
# Shape them by a triangular membership function.

blink["good"] = fuzz.trapmf(blink.universe, [0, 5, 20, 20])
blink["average"] = fuzz.trimf(blink.universe, [0, 0, 5])

def map_blink_rate_to_membership_value(blink_rate: int) -> int:
    """Returns the membership value of the blink rate.

    Maps the blink rate between [1, 20] to the membership value [0, 15].
    Arguments:
        blink_rate: In the range [1, 20].
    """
    if blink_rate < 1 or blink_rate > 20:
        raise ValueError("only blink rates between [1, 20] are in the fuzzy set")
    # the crisp good region (MV 5 ~ 15)
    if 5 <= blink_rate <= 15:
        return blink_rate + 5
    # the oblique fuzzy region (MV 0 ~ 4)
    center: int = 10
    # possible values: 6 ~ 10, map to 1 ~ 4
    diff: int = abs(blink_rate - center)
    # lower diff should map to greater value
    return 10 - diff


# In comparison with blink, body is a lot more simple.
# The body concentration (BC) sent by the ConcentrationGrader is between 0 and 1,
# maps them to the membership values (MV) through an easy function: MV = BC * 10
# since skfuzzy does better on generating membership functions with non-floating
# point intervals.
# The greater the values is, the better the grade of body concentration is,
# so we simply use .automf(3) to generate equally-divided triangular membership
# function.
body = ctrl.Antecedent(np.arange(11), "body")
body.automf(3)


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
            data.append(f"Concentration grade: {concent_grade}")
            concent_grades.append((concent_grade, data))


    with open("fuzzy_grades.txt", mode="w+") as f:
        f.write("***Data are sorted by concentration grade in descending order***\n---\n")
        concent_grades.sort(reverse=True, key=lambda e: e[0])
        for concent_grade, data in concent_grades:
            f.write("\n".join(data))
            f.write("\n---\n")


if __name__ == "__main__":
    if input("output fuzzy grades? (Y/N): ").lower() == "y":
        output_fuzzy_grades()

    blink.view()
    body.view()
    grade.view()
    # go for a single graph check
    grading.input["blink"] = map_blink_rate_to_membership_value(int(input("blink rate: ")))
    grading.input["body"] = float(input("body concent: ")) * 10
    grading.compute()
    print(f"grade: {grading.output['grade']:.2f}")
    grade.view(sim=grading)

    input("press any key to exit")

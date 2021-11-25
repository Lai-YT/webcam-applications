# Please read the example of tipping problem before playing with this file.
# https://pythonhosted.org/scikit-fuzzy/auto_examples/plot_tipping_problem_newapi.html

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


# New Antecedent/Consequent objects hold universe variables and membership
# functions.
blink = ctrl.Antecedent(np.arange(31), "blink")
body = ctrl.Antecedent(np.arange(11), "body")
grade = ctrl.Consequent(np.arange(11), "grade")

# Custom membership functions can be built interactively with a familiar,
# Pythonic API.
blink["poor"] = fuzz.trapmf(blink.universe, [0, 0, 10, 20])
blink["average"] = fuzz.trapmf(blink.universe, [0, 10, 20, 30])
blink["good"] = fuzz.trapmf(blink.universe, [10, 20, 30, 30])

body["poor"] = fuzz.trapmf(body.universe, [0, 0, 3, 6])
body["average"] = fuzz.trapmf(body.universe, [0, 3, 6, 9])
body["good"] = fuzz.trapmf(body.universe, [3, 6, 10, 10])

grade["low"] = fuzz.trapmf(grade.universe, [0, 0, 3, 3])
grade["medium"] = fuzz.trapmf(grade.universe, [3, 3, 6, 6])
grade["high"] = fuzz.trapmf(grade.universe, [6, 6, 10, 10])

# See how they look like.
blink.view()
body.view()
grade.view()

# fuzzy rules
rule1 = ctrl.Rule(body["poor"] | blink["poor"], grade["low"])
rule2 = ctrl.Rule(blink["average"], grade["medium"])
rule3 = ctrl.Rule(blink["good"] | body["good"], grade["high"])

grading_ctrl = ctrl.ControlSystem([rule1, rule2, rule3])
grading = ctrl.ControlSystemSimulation(grading_ctrl)


while True:
    grading.input["blink"] = float(input("blink (0 ~ 30) = "))
    grading.input["body"] = float(input("body (0 ~ 10) = "))

    grading.compute()

    print(f"Your concentration grade is {round(grading.output['grade'], 2)}. (0 ~ 10)\n")
    grade.view(sim=grading)

    command = input("Continue? (Y/N): ").lower()
    if command != "y":
        break

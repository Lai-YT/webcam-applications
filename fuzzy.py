# Please read the example of tipping problem before playing with this file.
# https://pythonhosted.org/scikit-fuzzy/auto_examples/plot_tipping_problem_newapi.html

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


blink = ctrl.Antecedent(np.arange(31), "blink")
body = ctrl.Antecedent(np.arange(11), "body")
grade = ctrl.Consequent(np.arange(11), "grade")

blink.automf(3)
body.automf(3)

grade["low"] = fuzz.trimf(grade.universe, [0, 0, 5])
grade["medium"] = fuzz.trimf(grade.universe, [0, 5, 10])
grade["high"] = fuzz.trimf(grade.universe, [5, 10, 10])

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

    command = input("Continue? (Y/N): ")
    if command == "N":
        break

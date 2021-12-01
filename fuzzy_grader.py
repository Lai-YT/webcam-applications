import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


blink = ctrl.Antecedent(np.arange(0, 16), "blink")
blink["good"] = fuzz.trapmf(blink.universe, [0, 0, 5, 10])
blink["average"] = fuzz.trapmf(blink.universe, [5, 10, 20, 20])

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

def print_blink_member_func_value(blink_rate):
    """Print the value of `average` and `good` section."""
    rate_abs = abs(blink_rate - 10)

    if rate_abs <= 5:
        print("averge: 0, good: 1")
    elif rate_abs < 10:
        print(f"averge: {round((rate_abs - 5) * 0.2, 1)}, good: {round(1 - (rate_abs - 5) * 0.2, 1)}")
    else:
        print("averge: 1, good: 0")


def print_body_member_func_value(body_concent):
    """Print the value of `poor`, `average`, and `good` section."""
    if body_concent < 5:
        print(f"poor: {round(1 - body_concent * 0.2, 1)}, average: {round(body_concent * 0.2, 1)}, good: 0")
    else:
        print(f"poor: 0, average: {round(1 - (body_concent - 5) * 0.2, 1)}, good: {round((body_concent - 5) * 0.2, 1)}")

if __name__ == "__main__":

    while True:
        blink_rate = int(input("Enter blink rate: "))
        print_blink_member_func_value(blink_rate)
        body_concent = int(input("Enter body concent (0 ~ 10): "))
        print_body_member_func_value(body_concent)

        grading.input["blink"] = abs(blink_rate - 10)
        grading.input["body"] = body_concent
        grading.compute()

        init_grade = grading.output['grade']
        # Init grade interval is (3.49, 8.14), we expand the grade interval to (0, 10).
        modified_grade = round(2.15 * (init_grade - 3.49), 2)
        print(f"grade: {modified_grade}")
        # grade.view(sim=grading)

        command = input("Continue? (Y/N): ")
        if command.lower() == "n":
            break

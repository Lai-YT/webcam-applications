import copy
import openpyxl

import fuzzy.grader as grader
import fuzzy.parse as parse


def output_grade_text() -> None:
    fuzzy_grader = grader.FuzzyGrader()
    # grade, blink rate, body concent
    concent_grades: List[Tuple[float, int, float]] = []
    for blink_rate in range(22):
        for body_concent in (round(0.1 * i, 1) for i in range(11)):
            grade = fuzzy_grader.compute_grade(blink_rate, body_concent)
            concent_grades.append((grade, blink_rate, body_concent))

    with open("fuzzy_grades.txt", mode="w+") as f:
        for grade, blink, body in concent_grades:
            f.write(f"{blink}\n"
                    + f"{body}\n"
                    + f"{grade}\n"
                    + "---\n")


def output_grade_spreadsheet() -> None:
    workbook = openpyxl.Workbook()
    sheet = workbook.active

    grades = parse.parse_grades("fuzzy_grades.txt")

    titles = [
        [None] + [i for i in range(22)],
        *([i/10] for i in range(11))
    ]

    for row in titles:
        sheet.append(row)

    for grade in grades:
        row = chr(grade.blink + 66)
        col = str(int(grade.body * 10 + 2))
        sheet[row + col] = grade.grade

    workbook.save(filename="fuzzy_grades.xlsx")


def output_grade_chart() -> None:
    workbook = openpyxl.load_workbook(filename="fuzzy_grades.xlsx")
    sheet = workbook.active

    # Contour chart
    contour = openpyxl.chart.SurfaceChart()
    data = openpyxl.chart.Reference(sheet, min_col=2, max_col=23, min_row=1, max_row=12)
    labels = openpyxl.chart.Reference(sheet, min_col=1, min_row=2, max_row=12)
    contour.add_data(data, titles_from_data=True)
    contour.set_categories(labels)
    contour.title = "Contour"
    sheet.add_chart(contour, "A15")

    # 2D Wireframe chart
    wire_frame = copy.deepcopy(contour)
    wire_frame.wireframe = True
    wire_frame.title = "2D Wireframe"
    sheet.add_chart(wire_frame, "L15")

    # Surface chart
    surface = openpyxl.chart.SurfaceChart3D()
    surface.add_data(data, titles_from_data=True)
    surface.set_categories(labels)
    surface.title = "Surface"
    sheet.add_chart(surface, "A31")

    # 3D Wireframe chart
    wire_frame_3d = copy.deepcopy(surface)
    wire_frame_3d.wireframe = True
    wire_frame_3d.title = "3D Wireframe"
    sheet.add_chart(wire_frame_3d, "L31")

    workbook.save(filename="fuzzy_grades.xlsx")


if __name__ == "__main__":
    output_grade_text()
    output_grade_spreadsheet()
    output_grade_chart()

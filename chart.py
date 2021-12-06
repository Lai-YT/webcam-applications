import copy
import openpyxl

import fuzzy.classes as classes
import fuzzy.parse as parse


if __name__ == "__main__":
    workbook = openpyxl.Workbook()
    sheet = workbook.active

    grades = parse.parse_grades("fuzzy_grades.txt")

    titles = [[i/10] for i in range(11)]
    titles.insert(0, [None] + [i for i in range(1, 21)])
    for row in titles:
        sheet.append(row)

    for grade in grades:
        row = chr(grade.blink + 65)
        col = str(int(grade.body * 10 + 2))
        sheet[row + col] = grade.grade


    contour = openpyxl.chart.SurfaceChart()
    data = openpyxl.chart.Reference(sheet, min_col=2, max_col=21, min_row=1, max_row=12)
    labels = openpyxl.chart.Reference(sheet, min_col=1, min_row=2, max_row=12)
    contour.add_data(data, titles_from_data=True)
    contour.set_categories(labels)
    contour.title = "Contour"
    sheet.add_chart(contour, "A15")

    wire_frame = copy.deepcopy(contour)
    wire_frame.wireframe = True
    wire_frame.title = "2D Wireframe"
    sheet.add_chart(wire_frame, "L15")

    surface = openpyxl.chart.SurfaceChart3D()
    surface.add_data(data, titles_from_data=True)
    surface.set_categories(labels)
    surface.title = "Surface"
    sheet.add_chart(surface, "A31")

    wire_frame_3d = copy.deepcopy(surface)
    wire_frame_3d.wireframe = True
    wire_frame_3d.title = "3D Wireframe"
    sheet.add_chart(wire_frame_3d, "L31")


    workbook.save(filename="fuzzy_grades.xlsx")

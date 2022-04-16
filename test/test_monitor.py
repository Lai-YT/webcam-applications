import unittest

from teacher.monitor import Col, ColumnHeader, Row


class ColTestCase(unittest.TestCase):
    def test_porperties(self) -> None:
        col = Col(100, "Willy", "30")
        self.assertEqual(col.no, 100)
        self.assertEqual(col.label, "Willy")
        self.assertEqual(col.value, "30")


class ColumnHeaderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.col_header = ColumnHeader((
            ("name", str), ("budget", int), ("list", list)
        ))

    def test_col_count(self) -> None:
        self.assertEqual(self.col_header.col_count, 3)

    def test_labels(self) -> None:
        """Get labels in order from the header."""
        labels = ("name", "budget", "list")
        self.assertEqual(labels, self.col_header.labels())

    def test_to_row(self) -> None:
        data = {
            "name": "Willy",
            "budget": 100_000,
            "list": ["shoes", ["computer", "headphone"]],
        }
        expected_row = [
            Col(0, "name", "Willy"),
            Col(1, "budget", 100_000),
            Col(2, "list", ["shoes", ["computer", "headphone"]]),
        ]
        row: Row = self.col_header.to_row(data)

        self.assertTrue(len(row), len(expected_row))
        # we can't simply compare Cols with "==" since __eq__ isn't implemented
        for col, expected_col in zip(row, expected_row):
            self.assertEqual((col.no, col.label, col.value),
                             (expected_col.no, expected_col.label, expected_col.value))

    def test_to_row_wrong_type(self) -> None:
        """TypeError should be raised when value doesn't match the declared type."""
        data = {
            "name": "Willy",
            "budget": "100_000",  # this should be int
            "list": ["shoes", ["computer", "headphone"]],
        }
        self.assertRaises(TypeError, self.col_header.to_row, data)

    def test_to_row_missing_label(self) -> None:
        """KeyError should be raised when label is missing."""
        data = {
            "name": "Willy",
            # the "budget" label is missing
            "list": ["shoes", ["computer", "headphone"]],
        }
        self.assertRaises(KeyError, self.col_header.to_row, data)

    def test_to_row_extra_label(self) -> None:
        """Extra labels should be ignored."""
        data = {
            "name": "Willy",
            "age": 25,  # this label is extra
            "budget": 100_000,
            "list": ["shoes", ["computer", "headphone"]],
        }
        expected_row = [
            Col(0, "name", "Willy"),
            Col(1, "budget", 100_000),
            Col(2, "list", ["shoes", ["computer", "headphone"]]),
        ]
        row: Row = self.col_header.to_row(data)

        self.assertTrue(len(row), len(expected_row))
        for col, expected_col in zip(row, expected_row):
            self.assertEqual((col.no, col.label, col.value),
                             (expected_col.no, expected_col.label, expected_col.value))


if __name__ == "__main__":
    unittest.main()

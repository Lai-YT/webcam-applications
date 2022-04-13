from typing import Any, Iterable, List, Mapping, Tuple, TypeVar

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QAbstractItemView, QTableWidget, QTableWidgetItem, QMainWindow, QPushButton


T = TypeVar("T")

class Col:
    """A single cell which carries the information of its column number,
    corresponding label and value.
    """
    def __init__(self, no: int, label: str, value: T) -> None:
        self._no = no
        self._label = label
        self._value = value

    @property
    def no(self) -> int:
        return self._no

    @property
    def label(self) -> str:
        return self._label

    @property
    def value(self) -> T:
        return self._value


class Row(List[Col]):
    """Rows should only be constructed by ColumnHeaders to have the Cols in the
    right order which fits the Monitor.

    Inherits List[Col] to provide expressive signature.
    """


class ColumnHeader:
    """The header labels for columns of a Monitor."""

    def __init__(self, headers: Iterable[Tuple[str, type]]) -> None:
        """headers should be in the exact mapping order with respect to column.

        For example, a monitor of students:
            ------------------------
            |id  |name  |class no. |
            ------------------------
            |1   |Chris |102       |
            ------------------------
            |2   |Bill  |102       |
            ------------------------
        Should has its headers in the form of
            ("id", int), ("name", str), ("class no.", int)
        """
        self._headers = tuple(headers)

    @property
    def col_count(self) -> int:
        """Returns the number of columns (labels)."""
        return len(self._headers)

    def labels(self) -> Tuple[str, ...]:
        """Returns the labels of the header in column order."""
        return tuple(label for label, _ in self._headers)

    def types(self) -> Tuple[type, ...]:
        """Returns the corresponding value type of the labels in column order."""
        return tuple(value_type for _, value_type in self._headers)

    def to_row(self, values: Mapping[str, Any]) -> Row:
        """Packs the values into the desirable Row form.

        Arguments:
            values: Should have all the labels as keys. Extra keys will be ignored.

        Raises:
            KeyError: Missing label.
            TypeError: Value of the wrong type.
        """
        row = Row()
        for col_no, (label, value_type) in enumerate(self._headers):
            try:
                if not isinstance(values[label], value_type):
                    raise TypeError(f'label "{label}" should have type "{value_type.__name__}" but got "{type(values[label]).__name__}"')
            except KeyError:
                raise KeyError(f'label "{label}" is missing') from None
            row.append(Col(col_no, label, values[label]))
        return row


class Monitor(QMainWindow):
    s_button_clicked = pyqtSignal(int)

    def __init__(self, header = ColumnHeader([])) -> None:
        super().__init__()
        self.setWindowTitle("Teacher Monitor")
        self.resize(640, 480)

        self._table = QTableWidget(0, header.col_count)
        # read-only
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setCentralWidget(self._table)

        # this is the setter
        self.col_header = header

    @property
    def col_header(self) -> ColumnHeader:
        return self._header

    @col_header.setter
    def col_header(self, new_header: ColumnHeader) -> None:
        self._header = new_header
        self._table.setColumnCount(new_header.col_count + 1)
        self._table.setHorizontalHeaderLabels(new_header.labels())
        # add button header
        self._table.setHorizontalHeaderItem(new_header.col_count, QTableWidgetItem("history"))

    def insert_row(self, row: Row) -> None:
        """Inserts a new row to the bottom of the table."""
        self._table.insertRow(self._table.rowCount())

        row_no = self._table.rowCount() - 1
        self.update_row(row_no, row)

        button = QPushButton("look back")
        key_index = self._header.labels().index("id")
        # send id to controller
        button.clicked.connect(
            lambda: self.s_button_clicked.emit(row[key_index].value)
        )
        # append button in row
        self._table.setCellWidget(row_no, len(row), button)

    def update_row(self, row_no: int, row: Row) -> None:
        for col in row:
            self._table.setItem(row_no, col.no, QTableWidgetItem(str(col.value)))
        
    def sort_rows_by_label(self, label: str, order: Qt.SortOrder) -> None:
        self._table.sortItems(self._header.labels().index(label), order)

    def search_row_no(self, key: Tuple[str, Any]) -> int:
        """Searches with the key row by row.

        Returns:
            The row no. where the key is located, -1 if the key doesn't exist.
        """
        label, value = key
        col_no = self._header.labels().index(label)
        for row_no in range(self._table.rowCount()):
            if self._table.item(row_no, col_no).text() == str(value):
                return row_no
        return -1

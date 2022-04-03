from typing import Any, Dict, Iterable, List, Tuple, TypeVar

from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QMainWindow


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
    """


class ColumnHeader:
    """The header labels for columns of a Monitor."""

    def __init__(self, labels: Iterable[Tuple[str, type]]) -> None:
        """labels should be in the exact mapping order with respect to column.

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
        self._labels = tuple(labels)

    @property
    def col_count(self) -> int:
        return len(self._labels)

    def __iter__(self) -> Iterable[str]:
        for label, _ in self._labels:
            yield label

    def to_row(self, values: Dict[str, Any]) -> Row:
        """Packs the values into the desirable Row form.

        Arguments:
            values: Should have all the labels as keys. Extra keys will be ignored.

        Raises:
            KeyError: Missing label.
            TypeError: Value of the wrong type.
        """
        row = Row()
        for col_no, (label, value_type) in enumerate(self._labels):
            try:
                if not isinstance(values[label], value_type):
                    raise TypeError(f'label "{label}" should have type "{value_type.__name__}" but got "{type(values[label]).__name__}"')
            except KeyError:
                raise KeyError(f'label "{label}" is missing') from None
            row.append(Col(col_no, label, values[label]))
        return row


class Monitor(QMainWindow):
    def __init__(self, header: ColumnHeader) -> None:
        super().__init__()
        self._header = header
        self.setWindowTitle("Teacher Monitor")

        self._table = QTableWidget(0, header.col_count)
        self.setCentralWidget(self._table)

        self._table.setHorizontalHeaderLabels(header)

    def insert_row(self, row: Row) -> None:
        self._table.insertRow(self._table.rowCount())

        row_no = self._table.rowCount() - 1
        for col in row:
            self._table.setItem(row_no, col.no, QTableWidgetItem(str(col.value)))

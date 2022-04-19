from typing import Any, Iterable, List, Mapping, Tuple, TypeVar

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QMainWindow, QTreeWidget, QTreeWidgetItem

from util.color import RED


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
    s_button_clicked = pyqtSignal(str)

    def __init__(self, header: ColumnHeader, key_label: str = None) -> None:
        super().__init__()
        self.setWindowTitle("Teacher Monitor")
        self.resize(640, 480)

        self._table = QTreeWidget()
        self.setCentralWidget(self._table)

        self._set_col_header(header)
        self._key_label = key_label

    @property
    def col_header(self) -> ColumnHeader:
        return self._header

    def _set_col_header(self, header: ColumnHeader) -> None:
        self._header = header
        self._table.setColumnCount(header.col_count)
        self._table.setHeaderLabels(list(header.labels()))

    def insert_row(self, row: Row) -> None:
        """Inserts a new row to the bottom of the table."""
        content = [str(col.value) for col in row]
        new_item = QTreeWidgetItem(self._table, content)
        self._table.addTopLevelItem(new_item)

        key_index = self._header.labels().index(self._key_label)
        # NOTE: this signal is emitted more than once on a single expansion click
        self._table.itemExpanded.connect(
            lambda item: self.s_button_clicked.emit(item.text(key_index))
        )

    def update_row(self, row_no: int, row: Row) -> None:
        # A copy of the top level item is made before updating,
        # then the copy is inserted as the record (child).
        # NOTE: QTreeWidgetItem.clone() can't be used because it aslo clones the children.
        item = self._table.topLevelItem(row_no)
        content_copy = [item.text(i) for i in range(item.columnCount())]
        item_copy = QTreeWidgetItem(item, content_copy)
        # update top level
        for col in row:
            item.setText(col.no, str(col.value))
        # insert item record
        item.insertChild(0, item_copy)

    def set_background(self, row_no: int, label: str, color: Qt.GlobalColor) -> None:
        """Sets the background of the specific label at row_no to color."""
        item = self._table.topLevelItem(row_no)
        col_no = self._header.labels().index(label)
        # a bit dense on the background style so text are clear
        item.setBackground(col_no, QBrush(color, Qt.Dense4Pattern))

    def sort_rows_by_label(self, label: str, order: Qt.SortOrder) -> None:
        self._table.sortItems(self._header.labels().index(label), order)

    def search_row_no(self, key: Tuple[str, Any]) -> int:
        """Searches with the key row by row.

        Returns:
            The row no. where the key is located, -1 if the key doesn't exist.
        """
        label, value = key
        col_no = self._header.labels().index(label)
        for row_no in range(self._table.topLevelItemCount()):
            if self._table.topLevelItem(row_no).text(col_no) == str(value):
                return row_no
        return -1

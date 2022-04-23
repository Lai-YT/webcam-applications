from typing import Any, Iterable, List, Mapping, Tuple, TypeVar

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QTreeWidget, QTreeWidgetItem


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

    def __repr__(self) -> str:
        return f"Col(no={self._no}, label={self._label}, value={self._value})"


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
    """
    Signals:
        s_item_clicked:
            Emits when any of the items (row) are clicked. Sends the key value
            of that item and the label of the column that is clicked.
        s_item_collapsed:
            Emits when any of the items (row) are collapsed. Sends the key value
            of that item.
        s_item_expanded:
            Emits when any of the items (row) are expanded. Sends the key value
            of that item.
    """
    s_item_clicked = pyqtSignal(str, str)
    s_item_collapsed = pyqtSignal(str)
    s_item_expanded = pyqtSignal(str)

    MAX_HISTORY_NUM: int = 5

    def __init__(self, header: ColumnHeader, key_label: str = None) -> None:
        super().__init__()
        self.setWindowTitle("Teacher Monitor")
        self.resize(640, 480)

        self._table = QTreeWidget()
        self.setCentralWidget(self._table)

        self._set_col_header(header)
        self._key_label = key_label

        self._table.itemClicked.connect(
            lambda item, col_no: self.s_item_clicked.emit(
                *self._map_item_and_column_to_key_and_label(item, col_no)
            )
        )
        self._table.itemExpanded.connect(
            lambda item: self.s_item_expanded.emit(
                item.text(self._header.labels().index(self._key_label))
            )
        )
        self._table.itemCollapsed.connect(
            lambda item: self.s_item_collapsed.emit(
                item.text(self._header.labels().index(self._key_label))
            )
        )

    @property
    def col_header(self) -> ColumnHeader:
        return self._header

    def _set_col_header(self, header: ColumnHeader) -> None:
        self._header = header
        self._table.setColumnCount(header.col_count)
        self._table.setHeaderLabels(list(header.labels()))

    def insert_row(self, row: Row) -> QTreeWidgetItem:
        """Inserts a new row to the bottom of the table.

        Returns:
            The inserted widget item (row).
        """
        content = [str(col.value) for col in row]
        new_item = QTreeWidgetItem(self._table, content)
        # Since we lazily add children after the item is expanded, we have to
        # show the expansion indicator even there are no child.
        new_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
        self._table.addTopLevelItem(new_item)
        return new_item

    def update_row(self, row_no: int, row: Row) -> QTreeWidgetItem:
        """
        Returns:
            The updated widget item (row).
        """
        item = self._table.topLevelItem(row_no)
        for col in row:
            item.setText(col.no, str(col.value))
        return item

    def get_row_content(self, row_no: int) -> Row:
        """Returns text of columns of the row specified by row number."""
        item = self._table.topLevelItem(row_no)
        row = []
        for i in range(item.columnCount()):
            row.append(Col(i, self._header.labels()[i], item.text(i)))
        return row

    def add_history_of_row(self, row_no: int, hist_row: Row) -> QTreeWidgetItem:
        """Adds history from the top to the row specified by row number.

        At most MAX_HISTORY_NUM histories can be shown.

        Returns:
            The added history item (row).
        """
        item = self._table.topLevelItem(row_no)
        hist_item = QTreeWidgetItem(item, [str(col.value) for col in hist_row])
        # 0 is from top
        item.insertChild(0, hist_item)

        while item.childCount() > Monitor.MAX_HISTORY_NUM:
            item.removeChild(item.child(Monitor.MAX_HISTORY_NUM))
        return hist_item

    def remove_histories_of_row(self, row_no: int) -> None:
        """Removes histories from the top to the row specified by row number."""
        item = self._table.topLevelItem(row_no)
        item.takeChildren()

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

    def _map_item_and_column_to_key_and_label(
            self, item: QTreeWidgetItem, col_no: int) -> Tuple[str, str]:
        key_index = self._header.labels().index(self._key_label)
        return item.text(key_index), self._header.labels()[col_no]

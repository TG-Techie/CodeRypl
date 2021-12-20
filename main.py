from __future__ import annotations

import sys

from PySide6.QtCore import QAbstractTableModel, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QTableView


import sys
from typing import *
from dataclasses import dataclass, field
import functools


# import the necessary modules
import PySide6 as pyside
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import (
    Qt,
    QModelIndex,
    QAbstractTableModel,
    QMimeData,
    QEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QScrollArea,
    QAbstractItemView,
    QHeaderView,
)


ENABLE_STAY_ON_INSERT_ABOVE = not (
    {"--disable-stay-on-above-insert", "-dis-soai"} & set(sys.argv)
)


@dataclass(repr=True, frozen=False)
class Rplm:  # replacement model
    # class Field(Enum):
    #     first = auto()
    #     last = auto()
    #     num = auto()
    #     posn = auto()

    first: str
    last: str
    num: str
    posn: str

    # uuid: UUID = field(default_factory=uuid4, repr=False)

    def isempty(self) -> bool:
        return {self.first, self.last, self.num, self.posn} == {""}

    @classmethod
    def empty(cls):
        return cls("", "", "", "")

    def _get_field_by_col(self, col: int) -> str:
        match col:
            # fmt: off
            case 0: return self.first
            case 1: return self.last
            case 2: return self.num
            case 3: return self.posn
            # fmt: on
            case _:
                raise ValueError(f"{self}._get_field_by_col({col})")

    def _set_field_by_col(self, col: int, value: str) -> None:
        match col:
            # fmt: off
            case 0: self.first = value
            case 1: self.last = value
            case 2: self.num = value
            case 3: self.posn = value
            # fmt: on
            case _:
                raise ValueError(f"{self}._set_field_by_col({col})")


# def emptyguard(fn):
#     @functools.wraps(fn)
#     def wrapper(self: RplmFileModel, *args, **kwargs):
#         ret = fn(self, *args, **kwargs)

#         self._data = [datum for datum in self._data if not datum.isempty()]

#         if not self.get_rplm(-1).isempty():
#             self.append(Rplm.empty())
#         else:
#             self.layoutChange.emit()

#         return ret

#     return wrapper


# if TYPE_CHECKING:
emptyguard = lambda fn: fn


class RplmFileModel(QAbstractTableModel):

    _get_fieldname_by_col = {
        0: "first",
        1: "last",
        2: "num",
        3: "posn",
    }

    _blank_field_text_from_col = _get_fieldname_by_col
    # {
    #     0: "first ...",
    #     1: "last ...",
    #     2: "num ...",
    #     3: "posn ...",
    # }

    def __init__(self, name: str, data: Iterable[Rplm]) -> None:
        super().__init__()
        self._data = data
        self._filename = name
        self._last_used_index = QtCore.QModelIndex()
        self.set_selected_cell: Callable[[QtCore.QModelIndex], None] = lambda _: None

    def __len__(self):
        return len(self._data)

    @property
    def filename(self) -> str:
        return self._filename

    @classmethod
    def open(cls, filename: str) -> RplmFileModel:
        raise NotImplementedError(
            f"fromfile not implemented for {cls.__name__}.open({filename})"
        )
        return cls(data)

    @classmethod
    def untitled(cls) -> RplmFileModel:
        return cls("Untitled.rplm", [Rplm.empty()])

    def current_rplem(self) -> Rplm:
        return self._data[self._last_used_index.row()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        return 4

    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole):

        if not index.isValid():
            return None

        self._last_used_index = index

        rplm = self._data[index.row()]
        value = rplm._get_field_by_col(index.column())

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return (
                value if len(value) else self._blank_field_text_from_col[index.column()]
            )

        elif role == Qt.ForegroundRole:
            return None if len(value) else QtGui.QColor("gray")

        return None

    @emptyguard
    def setData(self, index, value, role):

        self._last_used_index = index
        match role:
            case Qt.EditRole:
                self.set_rplm_field(index.row(), index.column(), value)
                return True
            case _:
                raise ValueError(f"{self}.setData({index=}, {value=}, {role=})")

    def get_rplm_field(self, row: int, col: int) -> str:
        return self._data[row]._get_field_by_col(col)

    def get_rplm(self, row: int) -> Rplm:
        return self._data[row]

    @emptyguard
    def set_rplm_field(self, row: int, col: int, value) -> None:

        value = value.strip()

        if value == self._blank_field_text_from_col[col]:
            value = ""

        rplm = self._data[row]

        rplm._set_field_by_col(col, value)

    def append(self, rplm: Rplm):
        self._data.append(rplm)
        self.layoutChanged.emit()
        # self.set_selected_row(self._last_used_index.siblingAtRow(len(self._data) - 1))

    def insert(self, row: int, rplm: Rplm) -> None:
        self._data.insert(row, rplm)
        self.layoutChanged.emit()

    def flags(self, index):
        # rplm = self._data[index.row()]
        # prev = super().flags(index)
        return (
            Qt.ItemIsSelectable
            | Qt.ItemIsEnabled
            | Qt.ItemIsEditable
            | Qt.ItemIsDragEnabled
            | Qt.ItemIsDropEnabled
        )

    def mimeData(self, indicies: list[QModelIndex]) -> Rplm:
        self._drop_sources = indicies

        if len(indicies) != 1:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setText(
                f"Can only drag one item at a time, not {len(indicies)}.\n"
                "(If you're Ryan reading this message, what would that even do?)"
            )
            msgbox.exec()

        data = super().mimeData(indicies)
        data.setData("application/rplm-row", QtCore.QByteArray(str(indicies[0].row())))
        data.setData(
            "application/rplm-col", QtCore.QByteArray(str(indicies[0].column()))
        )
        return data

    @emptyguard
    def dropMimeData(self, data: QMimeData, action, _r, _c, parent):

        if action == Qt.CopyAction:
            dest_pos = (parent.row(), parent.column())
            src_pos = (
                int(data.data("application/rplm-row")),
                int(data.data("application/rplm-col")),
            )

            # swap the fields
            src_value = self.get_rplm_field(*src_pos)
            dest_value = self.get_rplm_field(*dest_pos)

            self.set_rplm_field(*dest_pos, src_value)
            self.set_rplm_field(*src_pos, dest_value)

            # update the table
            self.layoutChanged.emit()

            # keep focus on the dragged item (feels a bit more natural)
            self.set_selected_cell(parent)
        else:
            raise RuntimeError(
                f"unknown drop action {action} in {type(self).__name__}.dropMimeData"
            )

        return True


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setFixedSize(720, 450)
        self.setWindowTitle("RyPlacement")

        self.model = RplmFileModel.untitled()

        self._skip_next_row_forward = False

        self.init_layout()

    def init_layout(self) -> None:
        # setup the base widget and layout
        self.base_widget = base_widget = QWidget()
        self.base_layout = base_layout = QVBoxLayout()

        base_widget.setLayout(base_layout)
        self.setCentralWidget(base_widget)

        self.header = header = self._make_header()
        self.table = table = self._make_table()

        # add the header and table to the layout
        base_layout.addLayout(header)
        base_layout.addWidget(table)

        # self.setCentralWidget(table)

    def _make_table(self) -> QTableView:
        table = QTableView()
        table.setModel(self.model)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.model.set_selected_cell = table.setCurrentIndex

        table.setDragDropMode(QAbstractItemView.DragDrop)

        # hide the verical and horizontal headers
        table.verticalHeader().hide()
        table.horizontalHeader().hide()

        # set the column widths to be the same as the header
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        table.installEventFilter(self)

        return table

    def eventFilter(self, _, event) -> bool:

        index = self.table.currentIndex()

        # input sanitation
        if not index.isValid() or event.type() != QEvent.KeyPress:
            return True

        is_enter = event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return
        is_tab = event.key() == Qt.Key_Tab
        is_backtab = event.key() == Qt.Key_Backtab

        with_shift = event.modifiers() & Qt.ShiftModifier
        with_control = event.modifiers() & Qt.MetaModifier
        with_option = event.modifiers() & Qt.AltModifier

        at_bottom = index.row() == len(self.model) - 1
        row_empty = self.model.get_rplm(index.row()).isempty()

        # print(
        #     f"{is_enter=}, {is_tab=}, {is_backtab=}, {with_shift=}, {with_control=}, "
        #     f"{with_option=}, {at_bottom=}, {row_empty=}, {self._skip_next_row_forward=}"
        # )

        if is_tab:
            self._move_col_forward_no_wrap(index)
            return True
        elif is_backtab:
            self._move_col_backward_no_wrap(index)
            return True
        elif is_enter:
            if with_shift and with_option:
                self.model.insert(index.row(), Rplm.empty())
                self._skip_next_row_forward = True and ENABLE_STAY_ON_INSERT_ABOVE
                return False
            if with_option:
                self.model.insert(index.row() + 1, Rplm.empty())
                self._move_row_forward_one(index)
                return True
            if row_empty and at_bottom:
                return True
            if with_shift:
                self._move_row_backward_one(index)
                return True
            else:
                # this gate prenet an enter down after an insert into a row above
                if self._skip_next_row_forward and ENABLE_STAY_ON_INSERT_ABOVE:
                    self._skip_next_row_forward = False
                else:
                    self._move_row_forward_one(index)
                return True

        else:
            # print("fall thorught")
            return False

        # This should be unreachable (also grayed out with pylance)
        assert False, "unreachable"

    def _make_header(self) -> QHBoxLayout:
        self.header_layout = header_layout = QHBoxLayout()
        # create the open and export buttons and labels
        self.open_button = open_button = QPushButton("Open")
        self.filename_input = filename_input = QTextEdit(self.model.filename)
        self.export_button = export_button = QPushButton("Export")

        # make the label fill the space between the buttons
        # and center the text in the label
        filename_input.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Preferred
        )
        filename_input.setAlignment(QtCore.Qt.AlignCenter)
        filename_input.setFixedHeight(
            QtGui.QFontMetrics(filename_input.font()).height() + 10
        )
        # make the filename_input double clickable to edit
        filename_input.setReadOnly(False)
        filename_input.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # add the buttons  and current lable to the horizontal layout
        header_layout.addWidget(open_button)
        header_layout.addWidget(filename_input)
        header_layout.addWidget(export_button)

        return header_layout

    # table navigation methods
    def _move_col_forward_no_wrap(self, index: QModelIndex):
        self.table.setCurrentIndex(index.siblingAtColumn((index.column() + 1) % 4))

    def _move_col_backward_no_wrap(self, index: QModelIndex):
        self.table.setCurrentIndex(index.siblingAtColumn((index.column() - 1) % 4))

    # def _move_to_first_row(self, index: QModelIndex):
    #     self.table.setCurrentIndex(index.siblingAtRow(0))

    # def _move_to_last_row(self, index: QModelIndex):
    #     self.table.rrentIndex(index.siblingAtRow(len(self.model) - 1))

    def _move_row_forward_one(self, index: QModelIndex):
        self.table.setCurrentIndex(
            index.siblingAtRow((index.row() + 1) % len(self.model))
        )

    def _move_row_backward_one(self, index: QModelIndex):
        self.table.setCurrentIndex(
            index.siblingAtRow((index.row() - 1) % len(self.model))
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

from __future__ import annotations

import sys
from typing import *
from dataclasses import dataclass, field

from PySide6 import QtGui

from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
    QModelIndex,
    QByteArray,
    QMimeData,
)


def error_dialog():
    msgbox = QtWidgets.QMessageBox()
    msgbox.setText(
        f"Can only drag one item at a time, not {len(indicies)}.\n"
        "(If you're Ryan reading this message, what would that even do?)"
    )
    msgbox.exec()


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
        self._last_used_index = QModelIndex()
        self.set_selected_cell: Callable[[QModelIndex], None] = lambda _: None

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
            error_dialog()

        data = super().mimeData(indicies)
        data.setData("application/rplm-row", QByteArray(str(indicies[0].row())))
        data.setData("application/rplm-col", QByteArray(str(indicies[0].column())))
        return data

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

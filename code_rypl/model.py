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

from PySide6.QtWidgets import (
    QMessageBox,
)

from render_template import RplmFileRenderer


def blocking_error_popup(message):
    msgbox = QMessageBox()
    msgbox.setText(message)
    msgbox.exec()


class Rplm:

    field_spec: ClassVar[dict[str, int]]
    _cols: dict[int, str]

    def __new__(cls, **kwargs):
        if cls is Rplm:
            raise TypeError("cannot instantiate abstract class Rplm")
        return object.__new__(cls)

    def __init__(self, **kwargs) -> None:

        spec = self.field_spec

        assert (
            len(extras := set(kwargs) - set(spec)) == 0
        ), f"unexpedted kwargs: {extras}"

        assert (
            len(missing := set(spec) - set(kwargs)) == 0
        ), f"missing kwargs: {missing}"

        assert set(spec) == set(kwargs), (
            f"argument errors, got {set(kwargs)}, "
            "however this assert should not have been reached, please report this bug"
        )

        self._cols = {spec[f]: kwargs[f] for f in kwargs}

    def get_col(self, col: int) -> str:
        return self._cols[col]

    def set_col(self, col: int, value: str) -> None:
        self._cols[col] = value

    def isempty(self) -> bool:
        return set(self._cols.values()) == {""}

    @classmethod
    def empty(cls) -> Rplm:
        return cls(**{f: "" for f in cls.field_spec})

    @classmethod
    def num_cols(cls) -> int:
        return len(cls.field_spec)  # type: ignore

    @classmethod
    def prompt_for_col(cls, col: int) -> str:
        for prompt, colno in cls.field_spec.items():
            if colno == col:
                return prompt
        raise RuntimeError(f"unknown column {col} for {cls.__name__}")


class Player(Rplm):

    # TODO: make this a tuple
    field_spec = dict(
        first=0,
        last=1,
        num=2,
        posn=3,
    )


class Coach(Rplm):

    field_spec = dict(
        first=0,
        last=1,
        kind=2,
    )


class RplmFileModel:
    def __init__(
        self,
        *,
        filename: None | str = None,
        school: str = "",
        sport: str = "",
        category: str = "",
        season: str = "",
        players: Iterable[Player] | None = None,
        coaches: Iterable[Coach] | None = None,
        set_selected_cell: Callable[[QModelIndex], None] = None,
    ) -> None:
        super().__init__()

        self.players = players = (
            RplmList([Player.empty()]) if players is None else RplmList(players)
        )
        self.coaches = coaches = (
            RplmList([Coach.empty()]) if coaches is None else RplmList(coaches)
        )

        self.school = school
        self.sport = sport
        self.category = category
        self.season = season

        self.filename = filename

        self._last_used_index = QModelIndex()

        # intentionally not using the set_selected_cell not the internal one
        self.set_selected_cell = (
            set_selected_cell if set_selected_cell is not None else (lambda _: None)
        )

    @property
    def set_selected_cell(self) -> Callable[[QModelIndex], None]:
        return self._set_selected_cell

    @set_selected_cell.setter
    def set_selected_cell(self, set_selected_cell: Callable[[QModelIndex], None]):
        self._set_selected_cell = set_selected_cell
        self.players.set_selected_cell = set_selected_cell
        self.coaches.set_selected_cell = set_selected_cell

    @classmethod
    def open(cls, filename: str) -> RplmFileModel:
        raise NotImplementedError(
            f"fromfile not implemented for {cls.__name__}.open({filename})"
        )
        # return cls(data)

    @classmethod
    def untitled(cls) -> RplmFileModel:
        return cls(filename=None)

    def export_file(self, render_session_generator: Type[RplmFileRenderer]) -> None:
        print(render_session_generator)
        renderer = render_session_generator(
            school=self.school,
            sport=self.sport,
            category=self.category,
            season=self.season,
        )

        print(
            "==========================starting export==========================\n\n\n"
        )

        filename = renderer.suggested_filename()

        if self.filename is None:
            filename = "Untitled"

        filename = filename + ".txt"

        print(f"{filename=}")

        # TODO: skip empty lines
        for player in self.players:
            # todo: make this not shit
            renderer.render_player(
                first=player.get_col(0),
                last=player.get_col(1),
                num=player.get_col(2),
                posn=player.get_col(3),
            )

        for coach in self.coaches:
            renderer.render_coach(
                first=coach.get_col(0),
                last=coach.get_col(1),
                kind=coach.get_col(2),
            )

    def set_meta(
        self,
        school: None | str = None,
        sport: None | str = None,
        category: None | str = None,
        season: None | str = None,
    ):
        if school is not None:
            self.school = school
        if sport is not None:
            self.sport = sport
        if category is not None:
            self.category = category
        if season is not None:
            self.season = season


R = TypeVar("R", bound=Rplm)


class RplmList(Generic[R], QAbstractTableModel):
    def __init__(
        self,
        data: Iterable[R],
        set_selected_cell: Callable[[QModelIndex], None] = None,
    ):
        super().__init__()

        self._data = list(data)
        assert len(self._data) > 0, f"cannot create an empty RplmList"

        self._data_type = type(self._data[0])

        # live settable attr
        self.set_selected_cell: Callable[[QModelIndex], None] = (
            (lambda _: None) if set_selected_cell is None else set_selected_cell
        )

    def __len__(self) -> int:
        return len(self._data)

    def __str__(self) -> str:
        return f"{type(self).__name__}[{self._data_type.__name__}](...)"

    def __iter__(self) -> Iterator[R]:
        return iter(self._data)

    def current_rplm(self) -> R:
        return self._data[self._last_used_index.row()]

    # QT interface methods
    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        return self._data_type.num_cols()

    def data(self, index: QModelIndex, role: Qt.ItemDataRole):  # type: ignore

        # print(f"{self}.data({index}, {role})")

        if not index.isValid():
            return None

        self._last_used_index = index

        rplm = self._data[index.row()]
        value = rplm.get_col(index.column())

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return (
                value if len(value) else self._data_type.prompt_for_col(index.column())
            )

        elif role == Qt.ForegroundRole:
            return None if len(value) else QtGui.QColor("gray")

        return None

    def setData(self, index, value, role):

        self._last_used_index = index
        if role == Qt.EditRole:
            self.set_rplm_field(index.row(), index.column(), value)
            return True
        else:
            raise ValueError(f"{self}.setData({index=}, {value=}, {role=})")

    def get_rplm_field(self, row: int, col: int) -> str:
        return self._data[row].get_col(col)

    def get_rplm(self, row: int) -> R:
        return self._data[row]

    def set_rplm_field(self, row: int, col: int, value) -> None:

        value = value.strip()

        if value == self._data_type.prompt_for_col(col):
            value = ""

        rplm = self._data[row]

        rplm.set_col(col, value)

    def append(self, rplm: R):
        self._data.append(rplm)
        self.refresh()
        # self.set_selected_row(self._last_used_index.siblingAtRow(len(self._data) - 1))

    def insert(self, row: int, rplm: R) -> None:
        self._data.insert(row, rplm)
        self.refresh()

    def refresh(self) -> None:
        self.layoutChanged.emit()

    def pop(self, row: int) -> R:
        item = self._data.pop(row)
        if len(self._data) == 0:
            self.append(self._data_type.empty())  # type: ignore
        self.refresh()
        return item

    def flags(self, index):
        return (
            Qt.ItemIsSelectable
            | Qt.ItemIsEnabled
            | Qt.ItemIsEditable
            | Qt.ItemIsDragEnabled
            | Qt.ItemIsDropEnabled
        )

    def mimeData(self, indicies: list[QModelIndex]) -> QMimeData:  # type: ignore
        self._drop_sources = indicies

        if len(indicies) != 1:
            blocking_error_popup(
                f"Can only drag one item at a time, not {len(indicies)}.\n"
                "(If you're Ryan reading this message, what would that even do?)"
            )

        data = super().mimeData(indicies)  # type: ignore

        data.setData(
            "application/rplm-row",
            QByteArray((str(indicies[0].row())).encode()),
        )
        data.setData(
            "application/rplm-col",
            QByteArray((str(indicies[0].column())).encode()),
        )
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
            self.refresh()

            # keep focus on the dragged item (feels a bit more natural)
            self.set_selected_cell(parent)
        else:
            raise RuntimeError(
                f"unknown drop action {action} in {type(self).__name__}.dropMimeData"
            )

        return True

from __future__ import annotations

import sys
from typing import *

from model import RplmFileModel, Rplm

from PySide6.QtCore import (
    Qt,
    QEvent,
)

from PySide6.QtWidgets import (
    QTableView,
    QSizePolicy,
    QAbstractItemView,
    QHeaderView,
)

# cli args imports
ENABLE_STAY_ON_INSERT_ABOVE = not (
    {"--disable-stay-on-above-insert", "-dis-soai"} & set(sys.argv)
)
ENABLE_MOVE_TO_FIRST_ON_INSERT = not (
    {"--disable-move-to-first-on-insert", "-dis-mtfoi"} & set(sys.argv)
)
DISABLE_TAB_WRAP = bool({"--disable-tab-wrap", "-dis-tw"} & set(sys.argv))


class RplmTableView(QTableView):
    def __init__(self) -> None:
        super().__init__(parent=None)
        # self._model: None | RplmFileModel = None

        self._init_format()

        # navigation state
        self._skip_next_row_forward = False

    def load_rplm_model(self, model: RplmFileModel) -> None:
        self._model = model
        model.set_selected_cell = self.setCurrentIndex
        self.setModel(model)

    def _init_format(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setDragDropMode(QAbstractItemView.DragDrop)

        # hide the verical and horizontal headers
        self.verticalHeader().hide()
        self.horizontalHeader().hide()

        # set the column widths to be the same as the header
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.installEventFilter(self)

    def insert_above(self) -> None:

        index = self.currentIndex()

        self._model.insert(index.row(), Rplm.empty())
        self._skip_next_row_forward = True and ENABLE_STAY_ON_INSERT_ABOVE

        if ENABLE_MOVE_TO_FIRST_ON_INSERT:
            self.setCurrentIndex(index.siblingAtColumn(0))

    def insert_below(self) -> None:

        index = self.currentIndex()

        self._model.insert(index.row() + 1, Rplm.empty())
        self.setCurrentIndex(
            index.sibling(
                (index.row() + 1) % len(self._model),
                0 if ENABLE_MOVE_TO_FIRST_ON_INSERT else index.column(),
            )
        )

    # table navigation methods
    def move_right(self):
        index = self.currentIndex()
        self.setCurrentIndex(
            index.siblingAtColumn((index.column() + 1) % Rplm.NUM_COLS)
        )

    def move_left(self):
        index = self.currentIndex()
        self.setCurrentIndex(
            index.siblingAtColumn((index.column() - 1) % Rplm.NUM_COLS)
        )

    # def _move_to_first_row(self, index: QModelIndex):
    #     self.setCurrentIndex(index.siblingAtRow(0))

    # def _move_to_last_row(self, index: QModelIndex):
    #     self.rrentIndex(index.siblingAtRow(len(self._model) - 1))

    def move_down(self):
        index = self.currentIndex()
        self.setCurrentIndex(index.siblingAtRow((index.row() + 1) % len(self._model)))

    def move_up(self):
        index = self.currentIndex()
        self.setCurrentIndex(index.siblingAtRow((index.row() - 1) % len(self._model)))

    def go_col(self, col: int):
        index = self.currentIndex()
        self.setCurrentIndex(index.siblingAtColumn(col))

    def go(self, row: int, col: int):
        index = self.currentIndex()
        self.setCurrentIndex(index.sibling(row % len(self._model), col % Rplm.NUM_COLS))

    def remove_row(self, row: int):
        self._model.pop(row)
        self.go_col(0)

    def eventFilter(self, _, event) -> bool:

        index = self.currentIndex()

        # input sanitation
        if not index.isValid() or event.type() != QEvent.KeyPress:
            return False

        is_enter = event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return
        is_tab = event.key() == Qt.Key_Tab
        is_backtab = event.key() == Qt.Key_Backtab
        is_delete = event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace
        is_escape = event.key() == Qt.Key_Escape

        with_shift = event.modifiers() & Qt.ShiftModifier
        with_control = event.modifiers() & Qt.MetaModifier
        with_option = event.modifiers() & Qt.AltModifier

        at_bottom = index.row() == len(self._model) - 1
        at_h_hend = index.column() in {3, 4}
        row_empty = self._model.get_rplm(index.row()).isempty()
        cell_empty = self._model.get_rplm_field(index.row(), index.column()) == ""

        # print(
        #     f"{is_enter=}, {is_tab=}, {is_backtab=}, {with_shift=}, {with_control=}, "
        #     f"{with_option=}, {at_bottom=}, {row_empty=}, {self._skip_next_row_forward=}, {cell_empty=}"
        # )

        # TODO: cmd-z and m=cmd-sft-z
        if is_delete and with_shift:
            self.remove_row(index.row())
            return True
        elif is_delete:
            self._model.set_rplm_field(index.row(), index.column(), "")
            self._model.refresh()
            return True
        elif is_tab and at_bottom and at_h_hend:
            if row_empty:
                self.go_col(0)
            else:
                self.insert_below()
            return True
        if is_tab and at_h_hend:
            if row_empty:
                self.go_col(0)
            else:
                self.go(index.row() + 1, 0)
            return True
        elif is_tab and DISABLE_TAB_WRAP:
            print("asdf")
            self.move_right()
            return True
        elif is_backtab and DISABLE_TAB_WRAP:
            self.move_left()
            return True
        elif is_enter:
            if with_shift and with_option:
                self.insert_above()
                return False
            elif with_shift:
                self.move_up()
                return True
            elif with_option:
                self.insert_below()
                return True
            elif at_bottom and at_h_hend:
                if row_empty:
                    self.go_col(0)
                else:
                    self.insert_below()
                return True
            elif at_h_hend:
                self.move_down()
                self.go_col(0)
                return True
            if row_empty and at_bottom:
                return True
            else:
                # this gate prenet an enter down after an insert into a row above
                if self._skip_next_row_forward and ENABLE_STAY_ON_INSERT_ABOVE:
                    self._skip_next_row_forward = False
                else:
                    self.move_down()
                return True

        else:
            if is_tab or is_enter or is_backtab:
                import time

                print()
                print(time.monotonic(), "unhandled keypress", event.key())
                print("fall thorught")
                print(
                    f"{is_enter=}, {is_tab=}, {is_backtab=}, {with_shift=}, {with_control=}, "
                    f"{with_option=}, {at_bottom=}, {row_empty=}, {self._skip_next_row_forward=}, {cell_empty=}"
                )
            return False

        # This should be unreachable (also grayed out with pylance)
        assert False, "unreachable"

from __future__ import annotations

import sys

from typing import *
from dataclasses import dataclass, field


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
    QTableView,
    QMainWindow,
    QSizePolicy,
    QScrollArea,
    QAbstractItemView,
    QHeaderView,
)


ENABLE_STAY_ON_INSERT_ABOVE = not (
    {"--disable-stay-on-above-insert", "-dis-soai"} & set(sys.argv)
)
ENABLE_MOVE_TO_FIRST_ON_INSERT = not (
    {"--disable-move-to-first-on-insert", "-dis-mtfoi"} & set(sys.argv)
)
DISABLE_TAB_WRAP = bool({"--disable-tab-wrap", "-dis-tw"} & set(sys.argv))

print(f"{DISABLE_TAB_WRAP=}")

from model import *


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
            return False

        is_enter = event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return
        is_tab = event.key() == Qt.Key_Tab
        is_backtab = event.key() == Qt.Key_Backtab
        is_delete = event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace

        with_shift = event.modifiers() & Qt.ShiftModifier
        with_control = event.modifiers() & Qt.MetaModifier
        with_option = event.modifiers() & Qt.AltModifier

        at_bottom = index.row() == len(self.model) - 1
        at_right = index.column() == 3
        row_empty = self.model.get_rplm(index.row()).isempty()
        cell_empty = self.model.get_rplm_field(index.row(), index.column()) == ""

        # print(
        #     f"{is_enter=}, {is_tab=}, {is_backtab=}, {with_shift=}, {with_control=}, "
        #     f"{with_option=}, {at_bottom=}, {row_empty=}, {self._skip_next_row_forward=}, {cell_empty=}"
        # )
        if is_delete and with_shift:
            raise NotImplementedError("shift delete not implemented")
            self.remove_row(index.row())
            return True
        elif is_tab and at_bottom and at_right:
            if row_empty:
                self.go_col(0)
            else:
                self.insert_below()
            return True
        if is_tab and at_right:
            self.insert_below()
            return True
        elif is_tab and DISABLE_TAB_WRAP:
            self.move_right()
            return True
        elif is_backtab and DISABLE_TAB_WRAP:
            self.move_left()
            return True
        elif is_enter:
            if with_shift and with_option:
                self.insert_above()
                return False
            if with_shift:
                self.move_up()
                return True
            if with_option:
                self.insert_below()
                return True
            if at_bottom and at_right:
                if row_empty:
                    self.go_col(0)
                else:
                    self.insert_below()
                return True
            if at_right:
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
                print("fall thorught")
            return False

        # This should be unreachable (also grayed out with pylance)
        assert False, "unreachable"

    def _make_header(self) -> QHBoxLayout:
        self.header_layout = header_layout = QHBoxLayout()
        # create the open and export buttons and labels
        self.open_button = open_button = QPushButton("Open")
        self.filename_input = filename_input = QLineEdit(self.model.filename)
        self.export_button = export_button = QPushButton("Export")

        # make the label fill the space between the buttons
        # and center the text in the label
        filename_input.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Preferred
        )
        filename_input.setAlignment(QtCore.Qt.AlignCenter)
        # filename_input.setFixedHeight(
        #     QtGui.QFontMetrics(filename_input.font()).height() + 10
        # )
        # make the filename_input double clickable to edit
        filename_input.setReadOnly(False)
        # filename_input.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # add the buttons  and current lable to the horizontal layout
        header_layout.addWidget(open_button)
        header_layout.addWidget(filename_input)
        header_layout.addWidget(export_button)

        return header_layout

    def insert_above(self) -> None:

        index = self.table.currentIndex()

        self.model.insert(index.row(), Rplm.empty())
        self._skip_next_row_forward = True and ENABLE_STAY_ON_INSERT_ABOVE

        if ENABLE_MOVE_TO_FIRST_ON_INSERT:
            self.table.setCurrentIndex(index.siblingAtColumn(0))

    def insert_below(self) -> None:

        index = self.table.currentIndex()

        self.model.insert(index.row() + 1, Rplm.empty())
        self.table.setCurrentIndex(
            index.sibling(
                (index.row() + 1) % len(self.model),
                0 if ENABLE_MOVE_TO_FIRST_ON_INSERT else index.column(),
            )
        )

    # table navigation methods
    def move_right(self):
        index = self.table.currentIndex()
        self.table.setCurrentIndex(index.siblingAtColumn((index.column() + 1) % 4))

    def move_left(self):
        index = self.table.currentIndex()
        self.table.setCurrentIndex(index.siblingAtColumn((index.column() - 1) % 4))

    # def _move_to_first_row(self, index: QModelIndex):
    #     self.table.setCurrentIndex(index.siblingAtRow(0))

    # def _move_to_last_row(self, index: QModelIndex):
    #     self.table.rrentIndex(index.siblingAtRow(len(self.model) - 1))

    def move_down(self):
        index = self.table.currentIndex()
        self.table.setCurrentIndex(
            index.siblingAtRow((index.row() + 1) % len(self.model))
        )

    def move_up(self):
        index = self.table.currentIndex()
        self.table.setCurrentIndex(
            index.siblingAtRow((index.row() - 1) % len(self.model))
        )

    def go_col(self, col: int):
        index = self.table.currentIndex()
        self.table.setCurrentIndex(index.siblingAtColumn(col))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

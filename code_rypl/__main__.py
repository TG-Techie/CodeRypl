from __future__ import annotations

import sys
import os

from typing import *
from dataclasses import dataclass, field


# import the necessary modules
import PySide6 as pyside
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import (
    Qt,
    # QModelIndex,
    # QAbstractTableModel,
    # QMimeData,
    QEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    # QTextEdit,
    # QLabel,
    QTableView,
    QMainWindow,
    QSizePolicy,
    # QScrollArea,
    QAbstractItemView,
    QHeaderView,
)


from model import RplmFileModel, Rplm
from table import RplmTableView

# maybe name this code ryple document?
@final
class CodeRyplWindow(QMainWindow):
    @overload
    def __init__(self, model: RplmFileModel) -> None:
        ...

    @overload
    def __init__(self) -> None:
        ...

    def __init__(self, model: None | RplmFileModel = None) -> None:
        # TODO: make this take a filename as an argument and open it
        # or none for an untitled one
        super().__init__()

        self.setFixedSize(720, 450)

        self._skip_next_row_forward = False

        self.init_layout()

        self.model = model = RplmFileModel.untitled() if model is None else model

        self.table.load_rplm_model(model)

        self.setWindowTitle(f"CodeRyple - {model.filename}")

    def init_layout(self) -> None:
        # setup the base widget and layout
        self.base_widget = base_widget = QWidget()
        self.base_layout = base_layout = QVBoxLayout()

        base_widget.setLayout(base_layout)
        self.setCentralWidget(base_widget)

        self.header = header = self._make_header()
        self.table = table = RplmTableView()

        # add the header and table to the layout
        base_layout.addLayout(header)
        base_layout.addWidget(table)

        # self.setCentralWidget(table)

    def _make_header(self) -> QHBoxLayout:
        self.header_layout = header_layout = QHBoxLayout()
        # create the open and export buttons and labels
        self.open_button = open_button = QPushButton("Open")
        # self.filename_input = filename_input = QLineEdit(self.model.filename)
        self.export_button = export_button = QPushButton("Export")

        # make the label fill the space between the buttons
        # and center the text in the label
        # filename_input.setSizePolicy(
        #     QSizePolicy.MinimumExpanding, QSizePolicy.Preferred
        # )
        # filename_input.setAlignment(Qt.AlignCenter)  # type: ignore
        # # filename_input.setFixedHeight(
        #     QtGui.QFontMetrics(filename_input.font()).height() + 10
        # )
        # make the filename_input double clickable to edit
        # filename_input.setReadOnly(False)
        # filename_input.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # add the buttons  and current lable to the horizontal layout
        header_layout.addWidget(open_button)
        # header_layout.addWidget(filename_input)
        header_layout.addWidget(export_button)

        return header_layout


class CodeRyplApplication(QApplication):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._windows: list[CodeRyplWindow] = []
        # # the below commented code was auto-suggested by copilot
        # self.setStyle("Fusion")
        # self.setStyleSheet(
        #     open(
        #         os.path.join(os.path.dirname(__file__), "..", "styles", "fusion.qss"),
        #         "r",
        #     ).read()
        # )

    def new_window(self):
        window = CodeRyplWindow()
        self._windows.append(window)
        window.show()
        return window


if __name__ == "__main__":
    app = CodeRyplApplication(sys.argv)
    window = app.new_window()

    # window = CodeRyplWindow()
    # window.show()

    # window2 = CodeRyplWindow()
    # window2.show()

    sys.exit(app.exec())

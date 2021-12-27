from __future__ import annotations

from typing import *

import sys

from .document import CodeRyplDocumentWindow
from .preferences import PrefWindow

from PySide6.QtWidgets import QApplication


class CodeRyplApplication(QApplication):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._documents: list[CodeRyplDocumentWindow] = []
        self._pref_window = PrefWindow(self)

    def new_document(self, filename: None | str = None) -> CodeRyplDocumentWindow:
        document = CodeRyplDocumentWindow(self, filename)
        self._documents.append(document)
        document.show()
        return document

    def open_preferences(self) -> None:
        # if the pref window is open, focus it

        self._pref_window.show()
        self._pref_window.switch_focus()

    def closeEvent(self, event) -> None:
        print("Closing all documents")
        for document in self._documents:
            document.close()
        super().closeEvent(event)

    def run(self) -> NoReturn:
        sys.exit(self.exec())


def run(filename: str | None = None) -> NoReturn:

    app = CodeRyplApplication(sys.argv)

    # parse filename

    app.new_document(filename)

    app.run()

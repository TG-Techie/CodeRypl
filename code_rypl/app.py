from __future__ import annotations

from typing import *

import sys
import click

from .document import CodeRyplDocumentWindow

from PySide6.QtWidgets import QApplication


class CodeRyplApplication(QApplication):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._documents: list[CodeRyplDocumentWindow] = []

    def new_document(self, filename: None | str = None) -> CodeRyplDocumentWindow:
        document = CodeRyplDocumentWindow(self, filename)
        self._documents.append(document)
        document.show()
        return document

    def run(self) -> NoReturn:
        sys.exit(self.exec())


def run(filename: str | None = None) -> NoReturn:

    app = CodeRyplApplication(sys.argv)

    # parse filename
    # [arg for arg in sys.argv if not arg.startswith("-")]

    app.new_document(filename)

    app.run()

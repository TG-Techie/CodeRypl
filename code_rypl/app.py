from __future__ import annotations

from typing import *

import sys

from . import auto_log
from . import versioning


from .document import CodeRyplDocumentWindow

import PySide6
from PySide6.QtWidgets import QApplication

print(f"using PySide version {PySide6.__version__}")
print("--- CodeRypl version info ---")
print(versioning.full_version())

# get the current app version


class CodeRyplApplication(QApplication):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._documents: list[CodeRyplDocumentWindow] = []

    def new_document(self, filename: None | str = None) -> CodeRyplDocumentWindow:
        document = CodeRyplDocumentWindow(self, filename)
        self._documents.append(document)
        document.show()
        return document

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

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


@click.command()
@click.argument("filename", required=False)
def run(filename: str | None):

    app = CodeRyplApplication(sys.argv)

    app.new_document(filename)

    app.run()

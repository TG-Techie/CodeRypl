from .app import run, CodeRyplApplication
from .document import CodeRyplDocumentWindow
from .model import Player, Coach, Rplm, RplmFile, RplmList
from .renderers.template import RplmFileRenderer

if __name__ == "__main__":
    run()

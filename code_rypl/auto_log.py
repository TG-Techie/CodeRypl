"""
Intercepts write() calls to stdout and stderr and logs them to the temp dir
"""

import sys
import builtins
import datetime
import tempfile
from typing import *

from .versioning import BuildMode, __build_mode__ as build_mode

# if the sys._getframe api is available inject statements into print indicating the module
if hasattr(sys, "_getframe") and build_mode != BuildMode.release:
    _orig_print = builtins.print

    _last_moule_name: None | str = None

    def _moduled_print(*args, **kwargs) -> None:
        global _last_moule_name
        outer = sys._getframe(1)

        modname = outer.f_globals.get("__name__", None)
        # f"[{modinfo}]" if modinfo is not None else "[?unknown]"
        if (
            modname.startswith("code_rypl")
            and modname is not None
            and modname != _last_moule_name
        ):
            _last_moule_name = modname
            _orig_print(f"@[module: {modname}]")
        elif modname is None:
            _last_moule_name = None
            _orig_print("@[module: ?unknown]")

        _orig_print(*args, **kwargs)

    builtins.print = _moduled_print


def instrument_logging(fromstd: TextIO, *, into: tuple[TextIO, ...]) -> None:
    """
    wrap key methods used by print/etc to also write output to a file in addition to stdout|stderr
    """

    # normalize to and sanitize input
    if isinstance(into, TextIO):
        into = (into,)
    else:
        into = tuple(into)

    # keep a local closure of the original methods
    fromstd_flush = fromstd.flush
    fromstd_seek = fromstd.seek
    fromstd_truncate = fromstd.truncate
    fromstd_write = fromstd.write
    fromstd_writelines = fromstd.writelines

    # wrapper for the original methods
    def flush() -> None:
        fromstd_flush()
        for file in into:
            file.flush()

    def seek(offset: int, whence: int = 0) -> int:
        ret = fromstd_seek(offset, whence)
        for file in into:
            file.seek(offset, whence)
        return ret

    def truncate(size: int = None) -> int:
        ret = fromstd_truncate(size)
        for file in into:
            file.truncate(size)
        return ret

    def write(s) -> int:
        ret = fromstd_write(s)
        for file in into:
            file.write(s)
        return ret

    def writelines(lines) -> None:
        lines = list(lines)
        fromstd_writelines(lines)
        for file in into:
            file.writelines(lines)

    fromstd.flush = flush  # type: ignore[assignment]
    fromstd.seek = seek  # type: ignore[assignment]
    fromstd.truncate = truncate  # type: ignore[assignment]
    fromstd.write = write  # type: ignore[assignment]
    fromstd.writelines = writelines  # type: ignore[assignment]


# --- perform patching ---
now = datetime.datetime.now()

prefix = f"code_rypl_{now.strftime('%Y-%m-%d_%H-%M-%S')}_"

_tmperr_fd, _tmperr_name = tempfile.mkstemp(suffix=".err", prefix=prefix)
_tmpout_fd, _tmpout_name = tempfile.mkstemp(suffix=".out", prefix=prefix)
_tmplog_fd, _tmplog_name = tempfile.mkstemp(suffix=".log", prefix=prefix)

tmperr = open(_tmperr_name, "w")
tmpout = open(_tmpout_name, "w")
tmplog = open(_tmplog_name, "w")

# the individual styles
instrument_logging(sys.stderr, into=(tmperr, tmplog))
instrument_logging(sys.stdout, into=(tmpout, tmplog))


# # and output
print("CodeRypl logging starting up...")

print(
    "logging:\n"
    f"\tstderr to: {tmperr.name!r}\n"
    f"\tstdout to: {tmpout.name!r}\n"
    f"\tboth to: {tmplog.name!r}"
)

print("CodeRypl logging setup finished.")

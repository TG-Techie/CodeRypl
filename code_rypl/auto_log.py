"""
Intercepts write() calls to stdout and stderr and logs them to the temp dir
"""

from os import path
from re import escape
import sys
import datetime
import tempfile
from typing import *


def patch_in_second(*, fromstd: TextIO, tofiles: TextIO | Iterable[TextIO]) -> None:
    """
    wrap key methods used by print/etc to also write output to a file in addition to stdout|stderr
    """

    # normalize to and sanitize input
    if isinstance(tofiles, TextIO):
        tofiles = (tofiles,)
    else:
        tofiles = tuple(tofiles)

    # keep a local closure of the original methods
    fromstd_flush = fromstd.flush
    fromstd_seek = fromstd.seek
    fromstd_truncate = fromstd.truncate
    fromstd_write = fromstd.write
    fromstd_writelines = fromstd.writelines

    # wrapper for the original methods
    def flush() -> None:
        fromstd_flush()
        for file in tofiles:
            file.flush()

    def seek(offset: int, whence: int = 0) -> int:
        ret = fromstd_seek(offset, whence)
        for file in tofiles:
            file.seek(offset, whence)
        return ret

    def truncate(size: int = None) -> int:
        ret = fromstd_truncate(size)
        for file in tofiles:
            file.truncate(size)
        return ret

    def write(s: AnyStr) -> int:
        ret = fromstd_write(s)
        for file in tofiles:
            file.write(s)
        return ret

    def writelines(lines: Iterable[AnyStr]) -> None:
        lines = list(lines)
        fromstd_writelines(lines)
        for file in tofiles:
            file.writelines(lines)

    fromstd.flush = flush
    fromstd.seek = seek
    fromstd.truncate = truncate
    fromstd.write = write
    fromstd.writelines = writelines


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
patch_in_second(fromstd=sys.stderr, tofile=tmperr)
patch_in_second(fromstd=sys.stdout, tofile=tmpout)

# have the combined output go to the log file
patch_in_second(fromstd=sys.stdout, tofile=tmplog)
patch_in_second(fromstd=sys.stderr, tofile=tmplog)

# # and output
print("CodeRypl is starting up...")

print(f"{sys.version=!r}")
print(f"{sys.platform=!r}")
print(f"{sys.executable=!r}")
print(f"{sys.argv=!r}")

print(
    "logging:\n"
    f"\tstderr to: {tmperr.name!r}\n"
    f"\tstdout to: {tmpout.name!r}\n"
    f"\tboth to: {tmplog.name!r}"
)

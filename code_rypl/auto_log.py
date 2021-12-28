"""
Intercepts write() calls to stdout and stderr and logs them to the temp dir
"""

from os import path
import sys
import datetime
import tempfile
from typing import *


def patch_in_second(*, fromstd: TextIO, tofile: TextIO) -> None:

    fromstd_flush = fromstd.flush
    fromstd_seek = fromstd.seek
    fromstd_truncate = fromstd.truncate
    fromstd_write = fromstd.write
    fromstd_writelines = fromstd.writelines

    def flush() -> None:
        fromstd_flush()
        tofile.flush()

    def seek(offset: int, whence: int = 0) -> int:
        ret = fromstd_seek(offset, whence)
        tofile.seek(offset, whence)
        return ret

    def truncate(size: int = None) -> int:
        ret = fromstd_truncate(size)
        tofile.truncate(size)
        return ret

    def write(s: AnyStr) -> int:
        ret = fromstd_write(s)
        tofile.write(s)
        return ret

    def writelines(lines: List[AnyStr]) -> None:
        fromstd_writelines(lines)
        tofile.writelines(lines)

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

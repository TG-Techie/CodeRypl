"""
used to derive the version and the build number.
This file may be pre-processed by the build system.

test script:
```bash
    rm -rf build/code_rypl \
    && cp -r code_rypl build/code_rypl\
    && py build/code_rypl/versioning.py --pre-process-in-place
```
"""


import sys
import datetime
from typing import *
import git
from enum import Enum


class BuildMode(Enum):
    dev = "dev"
    release = "release"
    # TODO: review later, left this in for now. It'd be cool to have debug mode but
    # without a good reason it does not make sense
    debug = "debug"

    def __repr__(self) -> str:
        # DO NOT CHANGE THIS LINE, it is used by the build system
        # fmt: off
        return f"{type(self).__name__}.{self.name}"
        # fmt: on


# ===== possible pre-processed values =====
# === DO NOT CHANGE THESE LINES ====
# START
# fmt: off
# --- flag ---
__pre_processed__: bool = False
# --- python / build related ---
__build_date__: str = ""
__build_time__: str = ""
__build_platform__: str = ""
__python_build_version__: str = ""
# --- git / source related ---
__branch_name__: str = ""
__build_mode__: None | BuildMode = None
__build_number__: str = ""
# fmt: on
# END
# === RESUME NORMAL CODE ====


# DO NOT CHANGE THE NEXT LINE, it is used by the build system
if not __pre_processed__:
    # resuming normal code
    assert __build_date__ == ""
    assert __build_time__ == ""
    assert __build_platform__ == ""
    assert __python_build_version__ == ""

    now = datetime.datetime.now()

    __build_date__ = now.strftime("%d%b%Y")
    __build_time__ = now.strftime("%Hh%Mm%Ss")
    __build_platform__: str = sys.platform  # type: ignore[no-redef]
    __python_build_version__: str = sys.version  # type: ignore[no-redef]

    assert __branch_name__ == ""
    assert __build_mode__ is None
    assert __build_number__ == ""

    repo = git.Repo(search_parent_directories=True)
    __branch_name__ = repo.active_branch.name
    __build_mode__ = BuildMode.dev
    __build_number__ = repo.git.rev_parse(repo.active_branch.commit.hexsha, short=7)


def full_version() -> str:
    return (
        "version:(\n\t"
        + ",\n\t".join(
            (
                f"{__build_date__ = !r}",
                f"{__build_time__ = !r}",
                f"{__build_platform__ = !r}",
                f"{__python_build_version__ = !r}",
                f"{__pre_processed__ = !r}",
                f"{__branch_name__ = !r}",
                f"{__build_mode__ = !r}",
                f"{__build_number__ = !r}",
            )
        )
        + "\n)"
    )


if __name__ == "__main__":
    if "--pre-process-in-place" not in sys.argv:
        print(f"skipping pre-processing, use --pre-process-in-place to enable")
        print(full_version())
    else:

        print(f"adding version and build info with pre-processing to {__file__!r}")
        assert __file__.endswith("build/code_rypl/versioning.py"), (
            "code_rypl must be copied to to a 'build/' directory to "
            f"be pre-processed, in {__file__}"
        )

        # determine the bulid mode
        if "--build-mode=release" in sys.argv:
            build_mode = BuildMode.dev
        elif "--build-mode=debug" in sys.argv:
            build_mode = BuildMode.debug
        else:
            # if it is specified here then it must be
            if any((fullarg := arg).startswith("--build-mode=") for arg in sys.argv):
                assert fullarg == "--build-mode=dev"
            build_mode = BuildMode.dev

        with open(__file__, "r") as file:
            lines = file.readlines()

        # fmt: off
        replacements = {
            '__build_date__: str = ""\n':
            f'__build_date__: Literal["{__build_date__}"] = "{__build_date__}"\n',
            
            '__build_time__: str = ""\n':
            f'__build_time__: Literal["{__build_time__}"] = "{__build_time__}"\n',
            
            '__build_platform__: str = ""\n':
            f'__build_platform__: Literal["{__build_platform__}"] = "{__build_platform__}"\n',

            '__python_build_version__: str = ""\n':
            f'__python_build_version__: Final[str] = "{__python_build_version__}"\n',

            "__pre_processed__: bool = False\n":
            "__pre_processed__: Literal[True] = True\n",

            '__branch_name__: str = ""\n': 
            f'__branch_name__: Literal["{__branch_name__}"] = "{__branch_name__}"\n',

            "__build_mode__: None | BuildMode = None\n": 
            f"__build_mode__: Final[BuildMode] = {build_mode}\n",

            '__build_number__: str = ""\n':
            f'__build_number__: Literal["{__build_number__}"] = "{__build_number__}"\n',
        }
        # fmt: on

        with open(__file__, "w") as file:
            itrbl = iter(lines)
            for line in itrbl:

                if line == ("if not __pre_processed__:\n") or line.startswith(
                    'if __name__ == "__main__"'
                ):
                    # skip the next indentation level
                    file.write(f"# {line}")
                    next_line: None | str = next(itrbl)
                    while next_line is not None and (
                        next_line.startswith(" ")
                        or next_line.startswith("\n")
                        or next_line.startswith("#")
                    ):  # while starts with an indent
                        file.write(f"# {next_line}")
                        next_line = next(itrbl, None)
                    else:
                        if next_line is None:
                            continue
                        line = next_line

                if line in replacements:
                    file.write(replacements.pop(line))
                else:
                    file.write(line)

        assert (
            len(replacements) == 0
        ), f"unable to pre-process {__file__}, cound not find where to replace {set(replacements)}"

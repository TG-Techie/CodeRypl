try:
    from code_rypl import run
except ModuleNotFoundError as err:
    import sys

    # if len(set(sys.argv) & {"--debug", "-d"}):
    #     pass
    # else:
    #     # skip outputting to stdout and stderr when in distribtion mode
    #     import sys
    #     import tempfile

    #     sys.stdout = tempfile.TemporaryFile() # t
    #     sys.stderr = tempfile.TemporaryFile()

    if str(err) == "No module named 'code_rypl'" and "-m" not in sys.argv:
        raise Warning(
            "looks like you're trying to run this as a module, "
            "use `python -m code_rypl` instead"
        ) from err
    else:
        raise err


if __name__ == "__main__":
    run()

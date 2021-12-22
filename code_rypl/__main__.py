try:
    from code_rypl.document import run_main
except ImportError as err:
    import sys

    if "-m" not in sys.argv:
        raise Warning(
            "looks like you're trying to run this as a module, use `python -m code_rypl` instead"
        ) from err


if __name__ == "__main__":
    run_main()

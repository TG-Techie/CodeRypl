try:
    from code_rypl import run
except ModuleNotFoundError as err:
    import sys

    if str(err) == "No module named 'code_rypl'" and "-m" not in sys.argv:
        raise Warning(
            "looks like you're trying to run this as a module, "
            "use `python -m code_rypl` instead"
        ) from err
    else:
        raise err


if __name__ == "__main__":
    run()

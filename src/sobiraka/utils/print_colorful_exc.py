import sys


def print_colorful_exc():
    print(file=sys.stderr)
    exc_type, exc_value, exc_traceback = sys.exc_info()
    sys.excepthook(exc_type, exc_value, exc_traceback)

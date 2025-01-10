import re


def parse_vars(raw: list[str]) -> dict[str, str | bool]:
    """
    Given a list of strings (most likely collected via argparse),
    return a dictionary with variable names and values that the user wants to set.

    - 'KEY=VALUE' → result[KEY] = VALUE
    - 'KEY='      → result[KEY] = ''
    - 'KEY'       → result[KEY] = True
    """
    result: dict[str, str | bool] = {}
    for item in raw:
        key, val = re.fullmatch(r'([^=]+) (?: = (.*) )?', item, re.VERBOSE).groups()
        if val is None:
            val = True
        result[key] = val
    return result

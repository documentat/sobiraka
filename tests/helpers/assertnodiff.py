from difflib import unified_diff
from typing import Sequence


def assertNoDiff(expected: Sequence[str], actual: Sequence[str]):
    diff = list(unified_diff(expected, actual, n=1000))
    if diff:
        raise AssertionError('\n\n' + '\n'.join(diff[3:]))

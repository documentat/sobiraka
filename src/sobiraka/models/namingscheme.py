import re
from math import inf
from pathlib import Path
from typing import Sequence


class NamingScheme:
    def __init__(self, patterns: Sequence[str] = (
            r'(?P<index>\d+) - (?P<stem>.+)',
            r'(?P<index>\d+)',
            r'(?P<stem>.+)',
    )):
        self.patterns: list[re.Pattern] = []
        for pattern in patterns:
            self.patterns.append(re.compile(pattern, re.VERBOSE))

    def get_index(self, path: Path | str) -> int | float:
        return self.get_index_and_stem(path)[0]

    def get_stem(self, path: Path | str) -> str:
        return self.get_index_and_stem(path)[1]

    def get_index_and_stem(self, path: Path | str) -> tuple[int | float, str]:
        name = Path(path).stem
        if name == '':
            return inf, ''
        for pattern in self.patterns:
            if m := pattern.fullmatch(name):
                try:
                    index = int(m.group('index'))
                except (IndexError, TypeError):
                    index = inf
                try:
                    stem = m.group('stem')
                except IndexError:
                    stem = name
                return index, stem
        raise ValueError(name)

    def get_sorting_key(self, path: Path) -> list[tuple[int | float, str]]:
        key = []
        for part in path.parts:
            key.append(self.get_index_and_stem(part))
        return key

from __future__ import annotations

import re
from dataclasses import dataclass
from math import inf

from sobiraka.utils import Location, RelativePath

DEFAULT_PATTERNS = (
    re.compile(r'(?P<is_main> ^$                                 )  # (empty name)   ', re.VERBOSE),
    re.compile(r'(?P<is_main> index                              )  # index.md       ', re.VERBOSE),
    re.compile(r'(?P<is_main> (?P<pos> \d+ ) - (?P<stem> index ) )  # 123-index.md   ', re.VERBOSE),
    re.compile(r'(?P<is_main> (?P<pos> 0 )                       )  # 0.md           ', re.VERBOSE),
    re.compile(r'(?P<is_main> (?P<pos> 0 ) - .*                  )  # 0-anything.md  ', re.VERBOSE),
    re.compile(r'(?P<pos> \d+ ) - (?P<stem> .+ )                    # 123-anything.md', re.VERBOSE),
    re.compile(r'(?P<pos> \d+ )                                     # 123.md         ', re.VERBOSE),
    re.compile(r'(?P<stem> .+ )                                     # anything.md    ', re.VERBOSE),
)


@dataclass
class NamingScheme:
    patterns: tuple[re.Pattern, ...] = DEFAULT_PATTERNS

    def __post_init__(self):
        self.patterns = tuple(
            pattern if isinstance(pattern, re.Pattern) else re.compile(pattern, re.VERBOSE)
            for pattern in self.patterns)

    def parse(self, path: RelativePath | str) -> FileNameData:
        name = RelativePath(path).stem

        for pattern in self.patterns:
            if m := pattern.fullmatch(name):
                groupdict = m.groupdict()
                data = FileNameData(
                    pos=int(groupdict['pos']) if 'pos' in groupdict else inf,
                    stem=groupdict.get('stem') or name,
                    is_main=groupdict.get('is_main') is not None,
                )
                return data

        raise ValueError(name)

    def path_sorting_key(self, path: RelativePath) -> tuple[FileNameData, ...]:
        return tuple(map(self.parse, path.parts))

    def make_location(self, path: RelativePath, *, as_dir: bool = False) -> Location:
        """
        Parse every component of the path and use the stems to construct a Location.
        """
        location = '/'.join(self.parse(p).stem for p in path.parts)
        location = '/' + location
        if as_dir and location != '/':
            location += '/'
        return Location(location)


@dataclass(frozen=True, slots=True)
class FileNameData:
    pos: int | float
    stem: str
    is_main: bool = False

    def __lt__(self, other):
        assert isinstance(other, FileNameData)
        return (not self.is_main, self.pos, self.stem) < (not other.is_main, other.pos, other.stem)

from __future__ import annotations

import re
from os.path import dirname, relpath

from sobiraka.utils import RelativePath


class Location:
    """
    A URL-like object that describes a Page's position in the output file structure.

    It always starts with a `/` and uses forward slashes, regardless of the OS.
    When converting to a path, it always creates a RelativePath and ignores the leading slash.

    The most important distinction from a classic Path is that the trailing slash is significant:
    if a location ends with a slash, it's a directory, otherwise it's a file.
    For HTML output, this means that Sobiraka will create append `index.html` to the generated path.
    """

    def __init__(self, t: str):
        assert t.startswith('/'), t
        assert '//' not in t, t
        assert '.' not in t.split('/'), t
        assert '..' not in t.split('/'), t
        self.t = re.sub(r'^\./?', '', t)

    def __str__(self):
        return self.t

    def __repr__(self):
        return f'{self.__class__.__name__}({self.t!r})'

    def __eq__(self, other: Location | str):
        return isinstance(other, (Location, str)) and str(self) == str(other)

    @property
    def level(self) -> int:
        if self.t == '/':
            return 1
        return self.t.rstrip('/').count('/') + 1

    @property
    def is_root(self) -> bool:
        return self.t == '/'

    @property
    def is_dir(self) -> bool:
        return self.t.endswith('/')

    @property
    def parent(self) -> Location | None:
        """
        Return a location representing a directory that contains the current location.
        The result always contains a trailing slash (because the result is a directory).
        """
        if self.is_root:
            return None
        result = dirname(self.t.rstrip('/'))
        if not result.endswith('/'):
            result += '/'
        return Location(result)

    @property
    def name(self) -> str | None:
        """
        The name of the location's last component. None if root.
        """
        if self.is_root:
            return None
        return self.t.rstrip('/').rsplit('/', maxsplit=1)[1]

    def as_path(self) -> RelativePath:
        """
        A relative path from the root to this location.
        """
        return RelativePath(self.t[1:])

    def as_relative_path_str(self, *, start: Location | None, suffix: str, index_file_name: str) -> str:
        """
        A string that can be used to reference this location from the given `start` location.
        For a file location, it adds the `suffix` to the end (e.g., '.html').
        For a directory location, it adds the `index_file_name` to the end (e.g., 'index.html').

        The result never starts with a slash because it's a relative path.
        """
        if self == start:
            return ''

        if start is None or start.is_root:
            result = self.t[1:]

        elif self.is_dir and not start.is_dir and self == start.parent:
            return index_file_name or './'

        else:
            if not start.is_dir:
                start = start.parent
            result = relpath(self.t, start=start.t)
            if self.is_dir:
                result += '/'
            if result == './':
                result = ''

        result += index_file_name if self.is_dir else suffix
        return result

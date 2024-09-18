from __future__ import annotations

import os.path
import sys
from os import PathLike
from pathlib import Path, PurePosixPath


class AbsolutePath(Path):
    if sys.version_info >= (3, 12):
        def __init__(self, *pathsegments):
            tmp_path = Path(*pathsegments)
            tmp_path = tmp_path.resolve()
            tmp_path = tmp_path.absolute()
            super().__init__(tmp_path)
    else:
        _flavour = Path().__class__._flavour  # pylint: disable=no-member,protected-access

        def __new__(cls, *args, **kwargs):
            path = super().__new__(cls, *args, **kwargs)
            path = path.resolve()
            path = path.absolute()
            return path

    def relative_to(self, start: PathLike | str) -> RelativePath:
        # pylint: disable=arguments-differ
        start = AbsolutePath(start)
        return RelativePath(os.path.relpath(self, start=start))


class RelativePath(PurePosixPath):
    if sys.version_info >= (3, 12):
        def __init__(self, *pathsegments):
            super().__init__(*pathsegments)
            if self.is_absolute():
                raise WrongPathType(f'{str(self)!r} is not a relative path.')
    else:
        def __new__(cls, *args):
            path = super().__new__(cls, *args)
            if path.is_absolute():
                raise WrongPathType(f'{str(path)!r} is not a relative path.')
            return path

    def __truediv__(self, other: PathLike | str) -> AbsolutePath | RelativePath:
        other = absolute_or_relative(other)
        if isinstance(other, AbsolutePath):
            return other

        result: list[str] = list(self.parts)

        for part in Path(other).parts:
            if part == '..':
                try:
                    result.pop()
                except IndexError as e:
                    raise PathGoesOutsideStartDirectory(f'{str(other)!r} goes outside {str(self)!r}') from e
            else:
                result.append(part)

        return RelativePath(*result)

    def relative_to(self, start: PathLike | str) -> RelativePath:
        # pylint: disable=arguments-differ
        start = RelativePath(start)
        return RelativePath(os.path.relpath(self, start=start))


def absolute_or_relative(path: Path | str) -> AbsolutePath | RelativePath:
    if Path(path).is_absolute():
        return AbsolutePath(path)
    return RelativePath(path)


class WrongPathType(Exception):
    pass


class IncompatiblePathTypes(Exception):
    pass


class PathGoesOutsideStartDirectory(Exception):
    pass

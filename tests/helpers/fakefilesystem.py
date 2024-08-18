from contextlib import AbstractContextManager, contextmanager
from io import BytesIO, StringIO
from typing import BinaryIO, Iterable, TextIO

from wcmatch.glob import globmatch

from sobiraka.models.filesystem.filesystem import FileSystem, GLOB_KWARGS
from sobiraka.utils import AbsolutePath, RelativePath


class FakeFileSystem(FileSystem):
    def __init__(self):
        self._files: dict[RelativePath, bytes | str] = {}

    def __setitem__(self, key: RelativePath | str, value: bytes | str):
        self._files = dict(sorted((*self._files.items(), (RelativePath(key), value))))

    def exists(self, path: RelativePath) -> bool:
        return path in self._files

    def is_dir(self, path: RelativePath) -> bool:
        if path in self._files:
            return False
        for result in self._files.keys():
            if result.parts[:len(path.parts)] == path.parts:
                return True
        return False

    @contextmanager
    def open_bytes(self, path: RelativePath) -> AbstractContextManager[BinaryIO]:
        yield BytesIO(self._files[path])

    @contextmanager
    def open_text(self, path: RelativePath) -> AbstractContextManager[TextIO]:
        yield StringIO(self._files[path])

    def copy(self, source: RelativePath, target: AbsolutePath):
        match self._files[source]:
            case bytes() as data:
                target.write_bytes(data)
            case str() as data:
                target.write_text(data)

    def glob(self, path: RelativePath, pattern: str) -> Iterable[RelativePath]:
        for result in self._files.keys():
            part1 = RelativePath(*result.parts[:len(path.parts)])
            part2 = RelativePath(*result.parts[len(path.parts):])
            if part1 == path and globmatch(part2, pattern, **GLOB_KWARGS):
                yield part2

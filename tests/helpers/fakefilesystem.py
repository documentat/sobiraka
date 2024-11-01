from contextlib import AbstractContextManager, contextmanager
from io import BytesIO, StringIO
from typing import BinaryIO, Iterable, TextIO

from wcmatch.glob import globmatch

from sobiraka.models.filesystem.filesystem import FileSystem, GLOB_KWARGS
from sobiraka.utils import AbsolutePath, RelativePath


class FakeFileSystem(FileSystem):
    def __init__(self, pseudofiles: dict[RelativePath, bytes | str] = None):
        self.pseudofiles: dict[RelativePath, bytes | str] = pseudofiles or {}

    def __setitem__(self, key: RelativePath | str, value: bytes | str):
        self.pseudofiles = dict(sorted((*self.pseudofiles.items(), (RelativePath(key), value))))

    def exists(self, path: RelativePath) -> bool:
        return path in self.pseudofiles

    def is_dir(self, path: RelativePath) -> bool:
        if path in self.pseudofiles:
            return False
        for result in self.pseudofiles.keys():
            if result.parts[:len(path.parts)] == path.parts:
                return True
        return False

    @contextmanager
    def open_bytes(self, path: RelativePath) -> AbstractContextManager[BinaryIO]:
        yield BytesIO(self.pseudofiles[path])

    @contextmanager
    def open_text(self, path: RelativePath) -> AbstractContextManager[TextIO]:
        yield StringIO(self.pseudofiles[path])

    def copy(self, source: RelativePath, target: AbsolutePath):
        target.parent.mkdir(parents=True, exist_ok=True)
        match self.pseudofiles[source]:
            case bytes() as data:
                target.write_bytes(data)
            case str() as data:
                target.write_text(data)

    def glob(self, path: RelativePath, pattern: str) -> Iterable[RelativePath]:
        for result in self.pseudofiles.keys():
            part1 = RelativePath(*result.parts[:len(path.parts)])
            part2 = RelativePath(*result.parts[len(path.parts):])
            if part1 == path and globmatch(part2, pattern, **GLOB_KWARGS):
                yield part2

from contextlib import AbstractContextManager, contextmanager
from io import BytesIO, StringIO
from pathlib import Path
from typing import BinaryIO, Iterable, TextIO

from wcmatch.glob import globmatch

from sobiraka.models.filesystem.filesystem import FileSystem, GLOB_KWARGS


class FakeFileSystem(FileSystem):
    def __init__(self):
        self._files: dict[Path, bytes | str] = {}

    def __setitem__(self, key: Path | str, value: bytes | str):
        self._files = dict(sorted((*self._files.items(), (Path(key), value))))

    def exists(self, path: Path) -> bool:
        return path in self._files

    def is_dir(self, path: Path) -> bool:
        if path in self._files:
            return False
        for result in self._files.keys():
            if result.parts[:len(path.parts)] == path.parts:
                return True
        return False

    @contextmanager
    def open_bytes(self, path: Path) -> AbstractContextManager[BinaryIO]:
        yield BytesIO(self._files[path])

    @contextmanager
    def open_text(self, path: Path) -> AbstractContextManager[TextIO]:
        yield StringIO(self._files[path])

    def copy(self, source: Path, target: Path):
        match self._files[source]:
            case bytes() as data:
                target.write_bytes(data)
            case str() as data:
                target.write_text(data)

    def glob(self, path: Path, pattern: str) -> Iterable[Path]:
        for result in self._files.keys():
            part1 = Path(*result.parts[:len(path.parts)])
            part2 = Path(*result.parts[len(path.parts):])
            if part1 == path and globmatch(part2, pattern, **GLOB_KWARGS):
                yield part2

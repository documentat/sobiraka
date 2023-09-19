from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import BinaryIO, Iterable, TextIO

from wcmatch.glob import GLOBSTAR, NODIR

GLOB_KWARGS = dict(flags=GLOBSTAR | NODIR, limit=0)


class FileSystem(metaclass=ABCMeta):
    @abstractmethod
    def resolve(self, path: Path | None) -> Path: ...

    @abstractmethod
    def exists(self, path: Path) -> bool: ...

    @abstractmethod
    def is_dir(self, path: Path) -> bool: ...

    @abstractmethod
    def open_bytes(self, path: Path) -> BinaryIO: ...

    @abstractmethod
    def open_text(self, path: Path) -> TextIO: ...

    def read_bytes(self, path: Path) -> bytes:
        return self.open_bytes(path).read()

    def read_text(self, path: Path) -> str:
        return self.open_text(path).read()

    @abstractmethod
    def copy(self, source: Path, target: Path): ...

    @abstractmethod
    def glob(self, path: Path, pattern: str) -> Iterable[Path]: ...

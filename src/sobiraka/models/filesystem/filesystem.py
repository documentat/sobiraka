from abc import ABCMeta, abstractmethod
from contextlib import AbstractContextManager
from pathlib import Path
from typing import BinaryIO, Iterable, TextIO

from wcmatch.glob import GLOBSTAR, NODIR

GLOB_KWARGS = dict(flags=GLOBSTAR | NODIR, limit=0)


class FileSystem(metaclass=ABCMeta):
    def resolve(self, path: Path | None) -> Path:
        raise NotImplementedError

    @abstractmethod
    def exists(self, path: Path) -> bool: ...

    @abstractmethod
    def is_dir(self, path: Path) -> bool: ...

    @abstractmethod
    def open_bytes(self, path: Path) -> AbstractContextManager[BinaryIO]: ...

    @abstractmethod
    def open_text(self, path: Path) -> AbstractContextManager[TextIO]: ...

    def read_bytes(self, path: Path) -> bytes:
        with self.open_bytes(path) as file:
            return file.read()

    def read_text(self, path: Path) -> str:
        with self.open_text(path) as file:
            return file.read()

    @abstractmethod
    def copy(self, source: Path, target: Path): ...

    @abstractmethod
    def glob(self, path: Path, pattern: str) -> Iterable[Path]: ...

from abc import ABCMeta, abstractmethod
from contextlib import AbstractContextManager
from typing import BinaryIO, Iterable, TextIO

from wcmatch.glob import GLOBSTAR, NODIR

from sobiraka.utils import AbsolutePath, RelativePath

GLOB_KWARGS = dict(flags=GLOBSTAR | NODIR, limit=0)


class FileSystem(metaclass=ABCMeta):
    def resolve(self, path: RelativePath | None) -> AbsolutePath:
        raise NotImplementedError

    @abstractmethod
    def exists(self, path: RelativePath) -> bool: ...

    @abstractmethod
    def is_dir(self, path: RelativePath) -> bool: ...

    @abstractmethod
    def open_bytes(self, path: RelativePath) -> AbstractContextManager[BinaryIO]: ...

    @abstractmethod
    def open_text(self, path: RelativePath) -> AbstractContextManager[TextIO]: ...

    def read_bytes(self, path: RelativePath) -> bytes:
        with self.open_bytes(path) as file:
            return file.read()

    def read_text(self, path: RelativePath) -> str:
        with self.open_text(path) as file:
            return file.read()

    @abstractmethod
    def copy(self, source: RelativePath, target: AbsolutePath): ...

    @abstractmethod
    def iterdir(self, path: RelativePath) -> Iterable[RelativePath]: ...

    @abstractmethod
    def glob(self, path: RelativePath, pattern: str) -> Iterable[RelativePath]: ...

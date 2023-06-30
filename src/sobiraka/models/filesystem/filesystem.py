from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Iterable

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
    def read_bytes(self, path: Path) -> bytes: ...

    @abstractmethod
    def read_text(self, path: Path) -> str: ...

    @abstractmethod
    def copy(self, source: Path, target: Path): ...

    @abstractmethod
    def glob(self, path: Path, pattern: str) -> Iterable[Path]: ...

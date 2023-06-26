import shutil
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Iterable


class FileSystem(metaclass=ABCMeta):
    @abstractmethod
    def resolve(self, path: Path | None) -> Path: ...

    @abstractmethod
    def read_bytes(self, path: Path) -> bytes: ...

    @abstractmethod
    def read_text(self, path: Path) -> str: ...

    @abstractmethod
    def copy(self, source: Path, target: Path): ...

    @abstractmethod
    def glob(self, path: Path, pattern: str) -> Iterable[Path]: ...


class RealFileSystem(FileSystem):
    def __init__(self, base: Path):
        self.base: Path = base

    def __str__(self):
        return self.base

    def resolve(self, path: Path | None) -> Path:
        if path:
            return self.base / path
        return self.base

    def read_bytes(self, path: Path) -> bytes:
        return self.resolve(path).read_bytes()

    def read_text(self, path: Path) -> str:
        return self.resolve(path).read_text('utf-8')

    def copy(self, source: Path, target: Path):
        source = self.resolve(source)
        shutil.copyfile(source, target)

    def glob(self, path: Path, pattern: str) -> Iterable[Path]:
        path = self.resolve(path)
        for result in path.glob(pattern):
            yield result.relative_to(path)

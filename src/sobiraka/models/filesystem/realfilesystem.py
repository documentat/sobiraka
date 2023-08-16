from pathlib import Path
from shutil import copyfile
from typing import Iterable

from wcmatch.glob import glob

from .filesystem import FileSystem, GLOB_KWARGS


class RealFileSystem(FileSystem):
    def __init__(self, base: Path):
        self.base: Path = base

    def __str__(self):
        return self.base

    def resolve(self, path: Path | None) -> Path:
        if path:
            assert not path.is_absolute()
            return self.base / path
        return self.base

    def exists(self, path: Path) -> bool:
        return self.resolve(path).exists()

    def is_dir(self, path: Path) -> bool:
        return self.resolve(path).is_dir()

    def read_bytes(self, path: Path) -> bytes:
        return self.resolve(path).read_bytes()

    def read_text(self, path: Path) -> str:
        return self.resolve(path).read_text('utf-8')

    def copy(self, source: Path, target: Path):
        source = self.resolve(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        copyfile(source, target)

    def glob(self, path: Path, pattern: str) -> Iterable[Path]:
        path = self.resolve(path)
        return map(Path, glob(pattern, root_dir=path, **GLOB_KWARGS))

import shutil
from pathlib import Path
from typing import Iterable

from wcmatch.glob import GLOBSTAR, NODIR, glob

from .filesystem import FileSystem


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
        for result in glob(pattern, flags=GLOBSTAR | NODIR, root_dir=path, limit=0):
            yield Path(result)

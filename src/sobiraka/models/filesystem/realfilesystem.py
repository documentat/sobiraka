from contextlib import AbstractContextManager
from shutil import copyfile
from typing import BinaryIO, Iterable, TextIO

from typing_extensions import override
from wcmatch.glob import glob

from sobiraka.utils import AbsolutePath, RelativePath
from .filesystem import FileSystem, GLOB_KWARGS


class RealFileSystem(FileSystem):
    def __init__(self, base: AbsolutePath):
        self.base: AbsolutePath = base

    def __str__(self):
        return self.base

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self.base)!r}>'

    @override
    def resolve(self, path: RelativePath | None) -> AbsolutePath:
        if path:
            assert not path.is_absolute()
            return self.base / path
        return self.base

    @override
    def exists(self, path: RelativePath) -> bool:
        return self.resolve(path).exists()

    @override
    def is_dir(self, path: RelativePath) -> bool:
        return self.resolve(path).is_dir()

    @override
    def open_bytes(self, path: RelativePath) -> AbstractContextManager[BinaryIO]:
        return open(self.resolve(path), 'rb')

    @override
    def open_text(self, path: RelativePath) -> AbstractContextManager[TextIO]:
        return open(self.resolve(path), 'rt', encoding='utf-8')

    @override
    def read_bytes(self, path: RelativePath) -> bytes:
        return self.resolve(path).read_bytes()

    @override
    def read_text(self, path: RelativePath) -> str:
        return self.resolve(path).read_text('utf-8')

    @override
    def copy(self, source: RelativePath, target: AbsolutePath):
        source = self.resolve(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        copyfile(source, target)

    @override
    def glob(self, path: RelativePath, pattern: str) -> Iterable[RelativePath]:
        path = self.resolve(path)
        return map(RelativePath, glob(pattern, root_dir=path, **GLOB_KWARGS))

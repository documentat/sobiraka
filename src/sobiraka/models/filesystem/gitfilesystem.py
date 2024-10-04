import os
from contextlib import AbstractContextManager, contextmanager
from io import BytesIO, StringIO
from os.path import relpath
from typing import BinaryIO, Iterable, TextIO

from wcmatch.glob import globmatch

from sobiraka.utils import AbsolutePath, RelativePath
from .filesystem import FileSystem, GLOB_KWARGS

os.environ['GIT_PYTHON_REFRESH'] = 'quiet'
from git import Commit, Tree  # pylint: disable=wrong-import-order,wrong-import-position


class GitFileSystem(FileSystem):

    def __init__(self, commit: Commit):
        self.commit: Commit = commit

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.commit.hexsha[:7]}>'

    def exists(self, path: RelativePath) -> bool:
        return str(path) in self.commit.tree

    def is_dir(self, path: RelativePath) -> bool:
        return isinstance(self.commit.tree[str(path)], Tree)

    @contextmanager
    def open_bytes(self, path: RelativePath) -> AbstractContextManager[BinaryIO]:
        data = self.read_bytes(path)
        yield BytesIO(data)

    @contextmanager
    def open_text(self, path: RelativePath) -> AbstractContextManager[TextIO]:
        data = self.read_text(path)
        yield StringIO(data)

    def read_bytes(self, path: RelativePath) -> bytes:
        blob = self.commit.tree / str(path)
        return blob.data_stream.read()

    def read_text(self, path: RelativePath) -> str:
        return self.read_bytes(path).decode('utf-8')

    def copy(self, source: RelativePath, target: AbsolutePath):
        raise NotImplementedError

    def glob(self, path: RelativePath, pattern: str) -> Iterable[RelativePath]:
        tree = self.commit.tree[str(path)]
        for subpath in self._iter_recurse(tree):
            if globmatch(subpath, pattern, **GLOB_KWARGS):
                yield RelativePath(subpath)

    def _iter_recurse(self, tree: Tree) -> Iterable[str]:
        for blob in tree:
            if isinstance(blob, Tree):
                yield from self._iter_recurse(blob)
            else:
                yield relpath(blob.path, start=tree.path)

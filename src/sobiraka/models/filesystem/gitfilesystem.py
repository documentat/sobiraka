from os.path import relpath
from pathlib import Path
from typing import Iterable

from git import Commit, Tree
from wcmatch.glob import globmatch

from .filesystem import FileSystem, GLOB_KWARGS


class GitFileSystem(FileSystem):

    def __init__(self, commit: Commit):
        self.commit: Commit = commit

    def resolve(self, path: Path | None) -> Path:
        raise NotImplementedError

    def exists(self, path: Path) -> bool:
        raise NotImplementedError

    def is_dir(self, path: Path) -> bool:
        raise NotImplementedError

    def read_bytes(self, path: Path) -> bytes:
        blob = self.commit.tree / str(path)
        return blob.data_stream.read()

    def read_text(self, path: Path) -> str:
        blob = self.commit.tree / str(path)
        return blob.data_stream.read().decode('utf-8')

    def copy(self, source: Path, target: Path):
        raise NotImplementedError

    def glob(self, path: Path, pattern: str) -> Iterable[Path]:
        tree = self.commit.tree[str(path)]
        for subpath in self._iter_recurse(tree):
            if globmatch(subpath, pattern, **GLOB_KWARGS):
                yield Path(subpath)

    def _iter_recurse(self, tree: Tree) -> Iterable[str]:
        for blob in tree:
            if isinstance(blob, Tree):
                yield from self._iter_recurse(blob)
            else:
                yield relpath(blob.path, start=tree.path)

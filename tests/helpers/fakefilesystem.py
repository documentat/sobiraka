from contextlib import AbstractContextManager, contextmanager
from io import BytesIO, StringIO
from textwrap import dedent
from typing import BinaryIO, Dict, Iterable, TextIO, Union

from wcmatch.glob import globmatch

from sobiraka.models.filesystem.filesystem import FileSystem, GLOB_KWARGS
from sobiraka.utils import AbsolutePath, RelativePath

PseudoFiles = Dict[str, Union[str, bytes, 'PseudoFiles']]


class FakeFileSystem(FileSystem):
    def __init__(self, pseudofiles: PseudoFiles = None):
        self.pseudofiles: dict[RelativePath, str | bytes] = {}
        if pseudofiles:
            self.add_files(pseudofiles)

    def add_files(self, pseudofiles: PseudoFiles, *, parent: RelativePath = RelativePath()):
        for name, content in pseudofiles.items():
            match content:
                case dict():
                    self.add_files(content, parent=parent / name)
                case str():
                    self.pseudofiles[parent / name] = dedent(content).strip()
                case bytes():
                    self.pseudofiles[parent / name] = content
                case _:
                    raise TypeError(content)

    def __setitem__(self, key: RelativePath | str, value: bytes | str):
        self.pseudofiles = dict(sorted((*self.pseudofiles.items(), (RelativePath(key), value))))

    def exists(self, path: RelativePath) -> bool:
        return path in self.pseudofiles or self.is_dir(path)

    def is_dir(self, path: RelativePath) -> bool:
        if path in self.pseudofiles:
            return False
        for result in self.pseudofiles:
            if result.parts[:len(path.parts)] == path.parts:
                return True
        return False

    def resolve(self, path: RelativePath | None) -> AbsolutePath:
        return AbsolutePath('/FAKE') / path

    @contextmanager
    def open_bytes(self, path: RelativePath) -> AbstractContextManager[BinaryIO]:
        yield BytesIO(self.pseudofiles[path])

    @contextmanager
    def open_text(self, path: RelativePath) -> AbstractContextManager[TextIO]:
        yield StringIO(self.pseudofiles[path])

    def copy(self, source: RelativePath, target: AbsolutePath):
        target.parent.mkdir(parents=True, exist_ok=True)
        match self.pseudofiles[source]:
            case bytes() as data:
                target.write_bytes(data)
            case str() as data:
                target.write_text(data)

    def glob(self, path: RelativePath, pattern: str) -> Iterable[RelativePath]:
        for result in self.pseudofiles:
            part1 = RelativePath(*result.parts[:len(path.parts)])
            part2 = RelativePath(*result.parts[len(path.parts):])
            if part1 == path and globmatch(part2, pattern, **GLOB_KWARGS):
                yield part2

    def iterdir(self, directory: RelativePath) -> Iterable[RelativePath]:
        # pylint: disable=arguments-renamed

        assert self.is_dir(directory), directory
        n = len(directory.parts)

        results: set[RelativePath] = set()
        for path in self.pseudofiles:
            if path.parts[:n] == directory.parts:
                results.add(RelativePath(*path.parts[:n + 1]))

        return tuple(sorted(results))

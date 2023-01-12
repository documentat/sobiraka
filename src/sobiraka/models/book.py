from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import Self, TYPE_CHECKING

import yaml

if TYPE_CHECKING: from .page import Page


class Book:
    def __init__(self, id: str, root: Path, title: str):
        self.id: str = id
        self.root: Path = root.resolve()
        self.title: str = title

        self.pages_by_path: dict[Path, Page] = {}

    @classmethod
    async def from_manifest(cls, manifest_path: Path) -> Self:
        from .page import Page

        with manifest_path.open() as manifest_file:
            manifest: dict = yaml.load(manifest_file, yaml.SafeLoader) or {}

        book_id = manifest.get('id', manifest_path.parent.stem)
        book_root = manifest_path.parent
        book_title = manifest.get('title', book_id)
        book = cls(id=book_id, root=book_root, title=book_title)

        paths: set[Path] = set()
        for pattern in manifest.get('include', ('**/*',)):
            paths |= set(book.root.glob(pattern))
        for pattern in manifest.get('exclude', ()):
            paths -= set(book.root.glob(pattern))

        for path in list(sorted(paths)):
            book.pages_by_path[path] = Page(book, path)

        return book

    @property
    def pages(self) -> list[Page]:
        return list(self.pages_by_path.values())

    @cached_property
    def max_level(self) -> int:
        levels = tuple(page.level for page in self.pages)
        return max(levels) if levels else 0
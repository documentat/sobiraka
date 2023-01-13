from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import Self, TYPE_CHECKING

import yaml
from schema import Optional, Schema, Use

if TYPE_CHECKING: from .page import Page


class Book:
    def __init__(self, id: str, root: Path, title: str):
        self.id: str = id
        self.root: Path = root.resolve()
        self.title: str = title
        self.header: Path | None = None

        self.pages_by_path: dict[Path, Page] = {}

    @classmethod
    async def from_manifest(cls, manifest_path: Path) -> Self:
        from .page import Page

        schema = Schema({
            Optional('id', default=manifest_path.parent.stem): str,
            Optional('title', default=manifest_path.parent.stem): str,
            Optional('include', default=['**/*']): [str],
            Optional('exclude', default=[]): [str],
            Optional('header', default=None): Use(lambda x: manifest_path.parent / x),
        })

        with manifest_path.open() as manifest_file:
            manifest: dict = yaml.load(manifest_file, yaml.SafeLoader) or {}
        manifest = schema.validate(manifest)

        book = cls(id=manifest['id'], root=manifest_path.parent, title=manifest['title'])
        book.header = manifest['header']

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

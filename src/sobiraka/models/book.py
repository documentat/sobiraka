from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import Self, TYPE_CHECKING

import yaml
from schema import Optional, Schema, Use

if TYPE_CHECKING: from .page import Page


class Book:
    """
    A single documentation project that needs to be processed and rendered.

    .. important::
        Note that because each :class:`.Page`'s data is modified during processing, a book must not be used for more than one rendering.
        Doing so will lead to unexpected behavior, as data loaded with different parameters do not necessarily co-exist nnicely.
    """
    def __init__(self, id: str, root: Path, title: str):
        self.id: str = id
        """Alphanumerical identifier of the book."""

        self.root: Path = root.resolve()
        """Absolute path to the root directory of the book."""

        self.title: str = title
        """Boook title. May be used when rendering output files."""

        self.header: Path | None = None
        """Path to the file containing LaTeX header directives for the book, if provided."""

        self.pages_by_path: dict[Path, Page] = {}
        """All pages in the book, sorted and indexed by :data:`.Page.relative_path`."""

    @classmethod
    async def from_manifest(cls, manifest_path: Path) -> Self:
        """
        Create a :class:`Book` object using parameters from given `manifest_path`.
        """
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
        """All pages in the book."""
        return list(self.pages_by_path.values())

    @cached_property
    def max_level(self) -> int:
        """Maximum value of :obj:`.Page.level` in the book. Used for calculating :obj:`.Page.antilevel`."""
        levels = tuple(page.level for page in self.pages)
        return max(levels) if levels else 0

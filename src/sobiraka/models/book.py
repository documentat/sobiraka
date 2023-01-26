from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any, TYPE_CHECKING

import yaml
from frozendict import frozendict
from schema import And, Optional, Schema, Use

if TYPE_CHECKING: from .page import Page


@dataclass(kw_only=True, frozen=True)
class BookConfig_Paths:
    manifest_path: Path
    root: Path
    include: tuple[str] = field(default_factory=tuple)
    exclude: tuple[str] = field(default_factory=tuple)


@dataclass(kw_only=True, frozen=True)
class BookConfig_Latex:
    header: Path | None = None
    """Path to the file containing LaTeX header directives for the book, if provided."""


@dataclass(kw_only=True, frozen=True)
class BookConfig_SpellCheck:
    dictionaries: tuple[str] = field(default_factory=tuple)
    """List of Hunspell dictionaries to use for spellchecking."""

    exceptions: tuple[Path] = field(default_factory=tuple)


@dataclass(kw_only=True, frozen=True)
class Book:
    """
    A single documentation project that needs to be processed and rendered.

    .. important::
        Note that because each :class:`.Page`'s data is modified during processing, a book must not be used for more than one rendering.
        Doing so will lead to unexpected behavior, as data loaded with different parameters do not necessarily co-exist nnicely.
    """

    id: str = field(default='')
    """Alphanumerical identifier of the book."""

    title: str = field(default='')
    """Book title. May be used when rendering output files."""

    paths: BookConfig_Paths = field(default_factory=BookConfig_Paths, kw_only=True)
    latex: BookConfig_Latex = field(default_factory=BookConfig_Latex, kw_only=True)
    spellcheck: BookConfig_SpellCheck = field(default_factory=BookConfig_SpellCheck, kw_only=True)
    variables: dict[str, Any] = field(default_factory=frozendict)

    pages: tuple[Page, ...] = field(default_factory=tuple, init=False, hash=False)
    pages_by_path: dict[Path, Page] = field(default_factory=frozendict, init=False, hash=False)

    def __repr__(self):
        return f'<{self.__class__.__name__}: {repr(str(self.paths.root))}>'

    @classmethod
    def from_manifest(cls, manifest_path: Path) -> Book:

        schema = Schema({
            Optional('id', default=manifest_path.parent.stem): str,
            Optional('title', default=manifest_path.parent.stem): str,
            Optional('paths', default={}): {
                Optional('root', default=manifest_path.parent): And(str, Use(lambda x: (manifest_path.parent / x).resolve())),
                Optional('include', default=('**/*',)): And([str], Use(tuple)),
                Optional('exclude', default=()): And([str], Use(tuple)),
            },
            Optional('latex', default={}): {
                Optional('header', default=None): And(str, Use(lambda x: manifest_path.parent / x)),
            },
            Optional('spellcheck', default={}): {
                Optional('dictionaries', default=()): And([str], Use(tuple)),
                Optional('exceptions', default=()): And([
                    And(str, Use(lambda x: (manifest_path.parent / x).resolve())),
                ], Use(tuple)),
            },
            Optional('variables', default=frozendict): And(dict, Use(frozendict)),
        })

        manifest_path = manifest_path.resolve()
        with manifest_path.open() as manifest_file:
            manifest: dict = yaml.load(manifest_file, yaml.SafeLoader) or {}
        manifest = schema.validate(manifest)

        book = Book(
            id=manifest['id'],
            title=manifest['title'],
            paths=BookConfig_Paths(**manifest['paths'], manifest_path=manifest_path),
            latex=BookConfig_Latex(**manifest['latex']),
            spellcheck=BookConfig_SpellCheck(**manifest['spellcheck']),
            variables=manifest['variables'],
        )
        return book

    def __post_init__(self):
        from .page import Page

        paths: set[Path] = set()
        for pattern in self.paths.include:
            paths |= set(self.root.glob(pattern))
        for pattern in self.paths.exclude:
            paths -= set(self.root.glob(pattern))

        pages: list[Page] = []
        pages_by_path: dict[Path, Page] = {}
        for path in list(sorted(paths)):
            relative_path = path.relative_to(self.root)
            absolute_path = path.resolve()

            page = Page(self, absolute_path)
            pages.append(page)
            pages_by_path[relative_path] = page
            if page.is_index:
                pages_by_path[relative_path.parent] = page

        object.__setattr__(self, 'pages', tuple(pages))
        object.__setattr__(self, 'pages_by_path', frozendict(pages_by_path))

    @property
    def root(self) -> Path:
        """Absolute path to the root directory of the book."""
        return self.paths.root

    @cached_property
    def max_level(self) -> int:
        """Maximum value of :obj:`.Page.level` in the book. Used for calculating :obj:`.Page.antilevel`."""
        levels = tuple(page.level for page in self.pages)
        return max(levels) if levels else 0

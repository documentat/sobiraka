from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any, Self, TYPE_CHECKING

import yaml
from frozendict import frozendict
from jsonschema import validate
from more_itertools import unique_justseen

from sobiraka.runtime import RT

if TYPE_CHECKING: from .page import Page

MANIFEST_SCHEMA = yaml.load((RT.FILES / 'sobiraka-book.yaml').read_text(), yaml.SafeLoader)

MANIFEST_BASE = {
    'id': None,
    'title': None,
    'paths': {
        'root': None,
        'resources': None,
        'include': ['**/*'],
        'exclude': '',
    },
    'html': {
        'resources_prefix': '_resources',
    },
    'pdf': {
        'header': None,
    },
    'lint': {
        'dictionaries': [],
        'exceptions': [],
        'checks': {},
    },
    'variables': {},
}


@dataclass(kw_only=True, frozen=True)
class BookConfig_Paths:
    manifest_path: Path
    root: Path
    resources: Path
    include: tuple[str]
    exclude: tuple[str]


@dataclass(kw_only=True, frozen=True)
class BookConfig_HTML:
    resources_prefix: Path | None = None


@dataclass(kw_only=True, frozen=True)
class BookConfig_PDF:
    header: Path | None = None
    """Path to the file containing LaTeX header directives for the book, if provided."""


@dataclass(kw_only=True, frozen=True)
class BookConfig_Lint_Checks:
    phrases_must_begin_with_capitals: bool = True


@dataclass(kw_only=True, frozen=True)
class BookConfig_Lint:
    dictionaries: tuple[str, ...]
    """List of Hunspell dictionaries to use for spellchecking."""

    exceptions: tuple[Path]

    checks: BookConfig_Lint_Checks


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
    html: BookConfig_HTML = field(default_factory=BookConfig_HTML, kw_only=True)
    pdf: BookConfig_PDF = field(default_factory=BookConfig_PDF, kw_only=True)
    lint: BookConfig_Lint = field(default_factory=BookConfig_Lint, kw_only=True)
    variables: dict[str, Any] = field(default_factory=frozendict)

    def __repr__(self):
        return f'<{self.__class__.__name__}: {repr(str(self.paths.root))}>'

    @classmethod
    def from_manifest(cls, manifest_path: Path) -> Self:
        from sobiraka.utils import convert_or_none, merge_dicts

        def path(x: str) -> Path:
            return (manifest_path.parent / (x or '')).resolve()

        manifest_path = manifest_path.resolve()
        with manifest_path.open() as manifest_file:
            manifest: dict = yaml.load(manifest_file, yaml.SafeLoader) or {}
        validate(manifest, MANIFEST_SCHEMA)
        manifest = merge_dicts(MANIFEST_BASE, manifest)

        book = Book(
            id=manifest['id'] or manifest_path.parent.stem,
            title=manifest['id'] or manifest_path.parent.stem,
            paths=BookConfig_Paths(
                manifest_path=manifest_path,
                root=path(manifest['paths']['root']),
                resources=path(manifest['paths']['resources']),
                include=tuple(manifest['paths']['include']),
                exclude=tuple(manifest['paths']['exclude']),
            ),
            html=BookConfig_HTML(
                resources_prefix=convert_or_none(Path, manifest['html']['resources_prefix']),
            ),
            pdf=BookConfig_PDF(
                header=convert_or_none(path, manifest['pdf']['header']),
            ),
            lint=BookConfig_Lint(
                dictionaries=tuple(manifest['lint']['dictionaries']),
                exceptions=tuple(path(x) for x in manifest['lint']['exceptions']),
                checks=BookConfig_Lint_Checks(**manifest['lint']['checks']),
            ),
            variables=frozendict(manifest['variables']),
        )
        return book

    @cached_property
    def pages_by_path(self) -> dict[Path, Page]:
        from .page import Page
        from .emptypage import EmptyPage

        paths: set[Path] = set()
        for pattern in self.paths.include:
            paths |= set(self.root.glob(pattern))
        for pattern in self.paths.exclude:
            paths -= set(self.root.glob(pattern))

        pages: list[Page] = []
        pages_by_path: dict[Path, Page] = {}
        expected_paths: set[Path] = set()

        for path in paths:
            relative_path = path.relative_to(self.root)
            absolute_path = path.resolve()

            page = Page(self, absolute_path)
            pages.append(page)
            pages_by_path[relative_path] = page
            if page.is_index:
                pages_by_path[relative_path.parent] = page
                expected_paths |= set(relative_path.parent.parents)
            else:
                expected_paths |= set(relative_path.parents)

        for expected_path in expected_paths:
            if expected_path not in pages_by_path:
                page = EmptyPage(self, self.root / expected_path)
                pages.append(page)
                pages_by_path[expected_path] = page

        return frozendict(sorted(pages_by_path.items()))

    @property
    def pages(self) -> list[Page]:
        pages = sorted(self.pages_by_path.values(), key=lambda p: p.path)
        pages = list(unique_justseen(pages))
        return pages

    @property
    def root(self) -> Path:
        """Absolute path to the root directory of the book."""
        return self.paths.root

    @cached_property
    def max_level(self) -> int:
        """Maximum value of :obj:`.Page.level` in the book. Used for calculating :obj:`.Page.antilevel`."""
        levels = tuple(page.level for page in self.pages)
        return max(levels) if levels else 0
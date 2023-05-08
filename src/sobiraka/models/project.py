from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any, TYPE_CHECKING

from more_itertools import unique_justseen
from utilspie.collectionsutils import frozendict

if TYPE_CHECKING: from .page import Page


@dataclass(kw_only=True, frozen=True)
class Volume_Paths:
    root: Path
    resources: Path
    include: tuple[str]
    exclude: tuple[str]


@dataclass(kw_only=True, frozen=True)
class Volume_HTML:
    resources_prefix: Path | None = None


@dataclass(kw_only=True, frozen=True)
class Volume_PDF:
    header: Path | None = None
    """Path to the file containing LaTeX header directives for the volume, if provided."""


@dataclass(kw_only=True, frozen=True)
class Volume_Lint_Checks:
    phrases_must_begin_with_capitals: bool = True


@dataclass(kw_only=True, frozen=True)
class Volume_Lint:
    dictionaries: tuple[str, ...]
    """List of Hunspell dictionaries to use for spellchecking."""

    exceptions: tuple[Path]

    checks: Volume_Lint_Checks


@dataclass(kw_only=True, frozen=True)
class Volume:
    project: Project = field(init=False, hash=False)
    lang: str | None = None
    codename: str | None = None

    title: str = ''
    """Volume title."""

    paths: Volume_Paths = field(default_factory=Volume_Paths, kw_only=True)
    html: Volume_HTML = field(default_factory=Volume_HTML, kw_only=True)
    pdf: Volume_PDF = field(default_factory=Volume_PDF, kw_only=True)
    lint: Volume_Lint = field(default_factory=Volume_Lint, kw_only=True)
    variables: dict[str, Any] = field(default_factory=frozendict, kw_only=True)

    def __hash__(self):
        return hash((id(self.project), self.codename, self.lang))

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.identifier!r}>'

    def __lt__(self, other):
        assert isinstance(other, Volume)
        assert self.project is other.project
        volumes = self.project.volumes
        return volumes.index(self) < volumes.index(other)

    @property
    def identifier(self) -> str | None:
        return '/'.join(filter(None, (self.lang, self.codename))) or None

    @cached_property
    def pages_by_path(self) -> dict[Path, Page]:
        from .page import Page
        from .emptypage import EmptyPage

        pages: list[Page] = []
        pages_by_path: dict[Path, Page] = {}
        expected_paths: set[Path] = set()

        paths: set[Path] = set()
        for pattern in self.paths.include:
            paths |= set(self.root.glob(pattern))
        for pattern in self.paths.exclude:
            paths -= set(self.root.glob(pattern))

        for path in paths:
            path_in_project = path.relative_to(self.project.base)
            absolute_path = path.resolve()

            page = Page(self, absolute_path)
            pages.append(page)
            pages_by_path[path_in_project] = page
            if page.is_index():
                pages_by_path[path_in_project.parent] = page

            for parent in path_in_project.parents:
                if parent not in pages_by_path:
                    expected_paths.add(parent)
                if parent == self.relative_root:
                    break

        for expected_path in expected_paths:
            if expected_path not in pages_by_path:
                page = EmptyPage(self, self.project.base / expected_path)
                pages.append(page)
                pages_by_path[expected_path] = page

        return frozendict(sorted(pages_by_path.items()))

    @property
    def pages(self) -> tuple[Page, ...]:
        pages = sorted(self.pages_by_path.values(), key=lambda p: p.path)
        pages = list(unique_justseen(pages))
        return tuple(pages)

    @property
    def root(self) -> Path:
        """Absolute path to the root directory of the volume."""
        return self.paths.root

    @property
    def relative_root(self) -> Path:
        return self.paths.root.relative_to(self.project.base)

    @cached_property
    def max_level(self) -> int:
        """Maximum value of :obj:`.Page.level` in the volume. Used for calculating :obj:`.Page.antilevel`."""
        levels = tuple(page.level for page in self.pages)
        return max(levels) if levels else 0


@dataclass(kw_only=True, frozen=True)
class Project:
    """
    A single documentation project that needs to be processed and rendered.
    """
    base: Path

    volumes: tuple[Volume, ...] = field(hash=False)

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self.base)!r}>'

    def get_volume(self, identifier: str | None = None) -> Volume:
        for volume in self.volumes:
            if volume.identifier == identifier:
                return volume
        raise KeyError

    @cached_property
    def pages_by_path(self) -> dict[Path, Page]:
        pages_by_path = {}
        for volume in self.volumes:
            pages_by_path |= volume.pages_by_path
        return frozendict(pages_by_path)

    @cached_property
    def pages(self) -> tuple[Page, ...]:
        pages = sorted(self.pages_by_path.values(), key=lambda p: p.path)
        pages = list(unique_justseen(pages))
        return tuple(pages)
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Callable

from more_itertools import unique_justseen
from utilspie.collectionsutils import frozendict

from .config import Config
from .page import DirPage, IndexPage, Page
from .project import Project


# pylint: disable=too-many-instance-attributes
@dataclass(kw_only=True, frozen=True)
class Volume(Config):
    """
    A part of a :obj:`.Project`, identified uniquely by :data:`lang` and :data:`codename`.
    """

    project: Project = field(init=False, hash=False)
    """
    The project to which this volume belongs.
    """

    lang: str | None = None
    """
    The language code of this volume. See :obj:`
    """

    codename: str | None = None
    """
    Short identifier of the 
    """

    title: str | None = None
    """Human-readable title of the volume."""

    def __hash__(self):
        return hash((id(self.project), self.codename, self.lang))

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.autoprefix!r}>'

    def __lt__(self, other):
        assert isinstance(other, Volume)
        assert self.project is other.project
        volumes = self.project.volumes
        return volumes.index(self) < volumes.index(other)

    @property
    def autoprefix(self) -> str | None:
        return '/'.join(filter(None, (self.lang, self.codename))) or None

    def _find_files(self) -> set[Path]:
        paths: set[Path] = set()
        for pattern in self.paths.include:
            paths |= set(self.root.glob(pattern))
        for pattern in self.paths.exclude:
            paths -= set(self.root.glob(pattern))
        return paths

    def _init_page(self, path_in_project: Path, *,
                   page_class: Callable[[Volume, Path], Page] = Page,
                   dirpage_class: Callable[[Volume, Path], Page] = DirPage,
                   indexpage_class: Callable[[Volume, Path], Page] = IndexPage,
                   ) -> Page:
        path = self.project.base / path_in_project
        if path.is_dir():
            return dirpage_class(self, path)
        if re.fullmatch(r'0(-.*)? | (\d+-)?index', path.stem, flags=re.X):
            return indexpage_class(self, path)
        return page_class(self, path)

    @cached_property
    def pages_by_path(self) -> dict[Path, Page]:
        pages: list[Page] = []
        pages_by_path: dict[Path, Page] = {}
        expected_paths: set[Path] = set()

        for path in self._find_files():
            path_in_project = path.relative_to(self.project.base)

            page = self._init_page(path_in_project)
            pages.append(page)
            for key in page.keys():
                pages_by_path[key] = page

            for parent in path_in_project.parents:
                if parent not in pages_by_path:
                    expected_paths.add(parent)
                if parent == self.relative_root:
                    break

        for expected_path in expected_paths:
            if expected_path not in pages_by_path:
                page = self._init_page(expected_path)
                for key in page.keys():
                    pages_by_path[key] = page

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

    @property
    def root_page(self) -> Page:
        return self.pages_by_path[self.relative_root]

    @cached_property
    def max_level(self) -> int:
        """Maximum value of :obj:`.Page.level` in the volume. Used for calculating :obj:`.Page.antilevel`."""
        levels = tuple(page.level for page in self.pages)
        return max(levels) if levels else 0

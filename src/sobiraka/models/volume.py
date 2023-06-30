from __future__ import annotations

import re
from functools import cached_property
from pathlib import Path
from typing import Iterable, overload

from more_itertools import unique_justseen

from .config import Config
from .page import DirPage, IndexPage, Page
from .project import Project


class Volume:
    """
    A part of a :obj:`.Project`, identified uniquely by :data:`lang` and :data:`codename`.
    """

    @overload
    def __init__(self, paths: tuple[Path, ...]):
        ...

    @overload
    def __init__(self, pages_by_path: dict[Path, Page]):
        ...

    @overload
    def __init__(self, lang: str, codename: str, paths: tuple[Path, ...]):
        ...

    @overload
    def __init__(self, lang: str, codename: str, pages_by_path: dict[Path, Page]):
        ...

    @overload
    def __init__(self, lang: str, codename: str, config: Config):
        ...

    @overload
    def __init__(self, project: Project, lang: str, codename: str, config: Config):
        ...

    @overload
    def __init__(self, root: Path):
        ...

    def __init__(self, *args):
        self.project: Project | None = None
        self.lang: str | None = None
        self.codename: str | None = None
        self.config: Config = Config()
        self.relative_root: Path | None = None

        self.__initial_pages: Iterable[Page]

        match args:
            case tuple() as paths,:
                self.__initial_pages = self._generate_pages(paths)

            case dict() as pages_by_path,:
                for path, page in pages_by_path.items():
                    page.volume = self
                    page.path_in_volume = path
                self.__initial_pages = pages_by_path.values()

            case str() | None as lang, str() | None as codename, tuple() as paths:
                self.lang = lang
                self.codename = codename
                self.__initial_pages = self._generate_pages(paths)

            case str() | None as lang, str() | None as codename, dict() as pages_by_path:
                self.lang = lang
                self.codename = codename
                for path, page in pages_by_path.items():
                    page.volume = self
                    page.path_in_volume = path
                self.__initial_pages = pages_by_path.values()

            case str() | None as lang, str() | None as codename, Config() as config:
                self.lang = lang
                self.codename = codename
                self.config = config
                self.relative_root = config.paths.root
                self.__initial_pages = self._generate_pages(self._find_files())

            case Project() as project, str() | None as lang, str() | None as codename, Config() as config:
                self.project = project
                self.lang = lang
                self.codename = codename
                self.config = config
                self.relative_root = config.paths.root
                self.__initial_pages = self._generate_pages(self._find_files())

            case _:
                raise TypeError(*args)

    def __hash__(self):
        return hash(id(self))

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.autoprefix!r}>'

    def __lt__(self, other):
        assert isinstance(other, Volume)
        assert self.project is other.project
        volumes = self.project.volumes
        return volumes.index(self) < volumes.index(other)

    # ------------------------------------------------------------------------------------------------------------------
    # Project and configuration

    @property
    def autoprefix(self) -> str | None:
        return '/'.join(filter(None, (self.lang, self.codename))) or None

    # ------------------------------------------------------------------------------------------------------------------
    # Pages and paths

    def _find_files(self) -> Iterable[Path]:
        paths: set[Path] = set()
        for pattern in self.config.paths.include:
            paths |= set(self.project.fs.glob(self.relative_root, pattern))
        for pattern in self.config.paths.exclude:
            paths -= set(self.project.fs.glob(self.relative_root, pattern))
        yield from paths

    def _generate_pages(self, paths: Iterable[Path]) -> Iterable[Page]:
        for path_in_volume in paths:
            if re.fullmatch(r'0(-.*)? | (\d+-)?index', path_in_volume.stem, flags=re.X):
                yield IndexPage(self, path_in_volume)
            else:
                yield Page(self, path_in_volume)

    @cached_property
    def pages_by_path(self) -> dict[Path, Page]:
        assert self.project is not None, 'You must bind the volume to a project before working with pages.'

        pages_by_path: dict[Path, Page] = {}
        expected_paths: set[Path] = set()
        for page in self.__initial_pages:
            pages_by_path[page.path_in_volume] = page
            if isinstance(page, IndexPage):
                pages_by_path[page.path_in_volume.parent] = page

            for parent in page.path_in_volume.parents:
                expected_paths.add(parent)

        for expected_path in expected_paths:
            if expected_path not in pages_by_path:
                page = DirPage(self, expected_path)
                pages_by_path[expected_path] = page

        pages_by_path = dict(sorted(pages_by_path.items()))
        return pages_by_path

    @property
    def pages(self) -> tuple[Page, ...]:
        pages = sorted(self.pages_by_path.values(), key=lambda p: p.path_in_volume)
        pages = list(unique_justseen(pages))
        return tuple(pages)

    @property
    def root_page(self) -> Page:
        return self.pages_by_path[Path('.')]

    @cached_property
    def max_level(self) -> int:
        """Maximum value of :obj:`.Page.level` in the volume. Used for calculating :obj:`.Page.antilevel`."""
        levels = tuple(page.level for page in self.pages)
        return max(levels) if levels else 0
